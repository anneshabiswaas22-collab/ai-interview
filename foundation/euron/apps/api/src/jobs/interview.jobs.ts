/**
 * Job handlers of the interview module:
 *
 *   interview.plan     write the round plan from a resume or a job description
 *   interview.score    score one answer (ratings and feedback) with the text model
 *   interview.hangup   end an OpenAI call whose session was closed
 *   interview.sweep    expire live sessions the browser never ended (every minute)
 *
 * Planning and scoring catch their own failures and record them on the row (the queue
 * does not retry a model that answered badly). Each is safe to run twice: planning only
 * acts on a PLANNING interview, scoring only writes when the answer is the version it
 * was queued for.
 */
import { z } from "zod";
import { captureError, logger } from "../core/logger";
import { db } from "../db/kysely";
import { generateJson, ModelOutputError } from "../services/interview/ai";
import { EvaluationContractError, buildTextEvidencePrompt, hasCandidateResponse, provenanceOf, TEXT_EVALUATION_OUTPUT, unansweredFeedback, validateTextEvaluation } from "../services/interview/evaluation";
import { hangup, sweepLiveSessions } from "../services/interview/live.service";
import { normalisePlan, plannerOutput, questionAt } from "../services/interview/plan";
import { codeScorer, plannerFromJobDescription, plannerFromResume, voiceScorer } from "../services/interview/prompts";
import { resolveTextModel } from "../services/models.service";
import { recordUsage } from "../services/quota.service";
import { getSettings } from "../services/settings.service";
import { planOf } from "../presenters/interview.presenter";
import { registerJob } from "./registry";
import { dispatchPendingScores } from "./score-outbox";

export async function planInterview(interviewId: string, resumeText?: string): Promise<void> {
  const row = await db.selectFrom("interviews").selectAll().where("id", "=", interviewId).executeTakeFirst();
  if (!row || row.status !== "PLANNING") return;
  const fail = async (reason: string) => {
    await db.updateTable("interviews").set({ status: "PLAN_FAILED", plan_error: reason, updated_at: new Date() }).where("id", "=", row.id).where("status", "=", "PLANNING").execute();
    // The interview was booked when it was created; a failed plan gives it back.
    if (row.text_model_id) await recordUsage({ userId: row.user_id, modelId: row.text_model_id, interviews: -1 });
  };
  if (row.source === "RESUME" && !resumeText) return fail("The resume is no longer available. Upload it again.");
  const model = await resolveTextModel(row.text_model_id);
  if (!model) return fail("No model is set up to plan interviews.");
  const settings = await getSettings();
  const prompt =
    row.source === "RESUME"
      ? plannerFromResume(resumeText!, settings.interviewerName)
      : plannerFromJobDescription({ company: row.company ?? "", role: row.role ?? "", jobDescription: row.job_description ?? "" }, settings.interviewerName);
  try {
    const out = await generateJson({ model, userId: row.user_id, system: prompt.system, user: prompt.user, schema: plannerOutput, maxOutputTokens: 12_000, temperature: 0.8 });
    const plan = normalisePlan(out.rounds);
    const role = row.source === "JOB_DESCRIPTION" ? row.role : out.role || null;
    await db
      .updateTable("interviews")
      .set({
        status: "READY",
        plan: JSON.stringify(plan),
        plan_error: null,
        summary: out.summary || null,
        domain: out.domain || null,
        role,
        title: row.source === "RESUME" && role ? `${role} interview`.slice(0, 160) : row.title,
        current_round: 0,
        current_question: 0,
        updated_at: new Date(),
      })
      .where("id", "=", row.id)
      .where("status", "=", "PLANNING")
      .execute();
  } catch (err) {
    if (!(err instanceof ModelOutputError) && !(err instanceof Error && err.message.includes("no usable rounds"))) captureError(err, { where: "interview.plan", interviewId });
    await fail("The interviewer could not prepare questions this time. Try again.");
  }
}

const scoreOutput = z.object({
  domainRating: z.coerce.number().min(0).max(100),
  communicationRating: z.coerce.number().min(0).max(100),
  strengths: z.array(z.string().max(500)).max(8).default([]),
  weaknesses: z.array(z.string().max(500)).max(8).default([]),
  suggestions: z.array(z.string().max(500)).max(8).default([]),
  analysis: z.string().max(5000).default(""),
  correctedSnippet: z.string().max(4000).nullish(),
});

const clampRating = (n: number) => Math.min(100, Math.max(1, Math.round(n)));

export async function scoreAnswer(answerId: string, version: string): Promise<void> {
  const a = await db.selectFrom("answers").selectAll().where("id", "=", answerId).executeTakeFirst();
  if (!a || a.status !== "SCORING" || a.updated_at.toISOString() !== version) return;
  const row = await db.selectFrom("interviews").selectAll().where("id", "=", a.interview_id).executeTakeFirst();
  const q = row ? questionAt(planOf(row) ?? [], a.round_index, a.question_index) : null;
  const markFailed = () => db.updateTable("answers").set({ status: "FAILED" }).where("id", "=", a.id).where("updated_at", "=", a.updated_at).execute();
  const markUnanswered = () =>
    db
      .updateTable("answers")
      .set({
        status: "SCORED",
        evaluator_kind: null,
        domain_rating: null,
        communication_rating: null,
        feedback: JSON.stringify(unansweredFeedback()),
        scored_at: new Date(),
      })
      .where("id", "=", a.id)
      .where("updated_at", "=", a.updated_at)
      .execute();
  if (!row || !q) return void (await markFailed());

  const transcript = (a.transcript as { role: "interviewer" | "candidate"; text: string }[]) ?? [];
  const candidateTranscript = transcript.filter((line) => line.role === "candidate").map((line) => line.text).join("\n").trim();
  const submittedCode = (a.code ?? "").trim();

  // A missing response is absence of evidence, not proof of poor performance. Code
  // questions may be answered with code, a spoken explanation, or both.
  if (a.kind !== "TEXT" && !hasCandidateResponse(candidateTranscript) && !hasCandidateResponse(submittedCode)) {
    await markUnanswered();
    return;
  }

  let textAnswerEvent: { id: string; text: string } | null = null;
  if (a.kind === "TEXT") {
    // The text-practice event is the authoritative response record. Do not decide
    // whether a response exists from the duplicated transcript JSON.
    textAnswerEvent =
      (await db
        .selectFrom("text_practice_events")
        .select(["id", "text"])
        .where("interview_id", "=", a.interview_id)
        .where("kind", "=", "ANSWER")
        .where("round_index", "=", a.round_index)
        .where("question_index", "=", a.question_index)
        .executeTakeFirst()) ?? null;
    if (!textAnswerEvent) return void (await markFailed());
    if (!hasCandidateResponse(textAnswerEvent.text)) {
      await markUnanswered();
      return;
    }
  }

  const model = await resolveTextModel(row.text_model_id);
  if (!model) return void (await markFailed());

  try {
    if (a.kind === "TEXT") {
      const answerEvent = textAnswerEvent!;

      const prompt = buildTextEvidencePrompt({ question: q.text, answer: answerEvent.text, role: row.role });
      const output = await generateJson({
        model,
        userId: row.user_id,
        system: prompt.system,
        user: prompt.user,
        schema: TEXT_EVALUATION_OUTPUT,
        maxOutputTokens: 4000,
        temperature: 0.1,
      });
      const evaluated = validateTextEvaluation({
        answerEvent,
        output,
        provenance: provenanceOf(model),
      });
      await db
        .updateTable("answers")
        .set({
          status: "SCORED",
          evaluator_kind: model.kind,
          domain_rating: evaluated.domainRating,
          communication_rating: evaluated.communicationRating,
          feedback: JSON.stringify(evaluated.feedback),
          scored_at: new Date(),
        })
        .where("id", "=", a.id)
        .where("updated_at", "=", a.updated_at)
        .execute();
      return;
    }

    const prompt =
      a.kind === "CODE"
        ? codeScorer({ question: q.text, code: a.code ?? "", language: a.language, role: row.role })
        : voiceScorer({ question: q.text, transcript, role: row.role });
    const out = await generateJson({
      model,
      userId: row.user_id,
      system: prompt.system,
      user: prompt.user,
      schema: scoreOutput,
      maxOutputTokens: 3000,
      temperature: 0.2,
    });
    await db
      .updateTable("answers")
      .set({
        status: "SCORED",
        evaluator_kind: model.kind,
        domain_rating: clampRating(out.domainRating),
        communication_rating: clampRating(out.communicationRating),
        feedback: JSON.stringify({
          strengths: out.strengths,
          weaknesses: out.weaknesses,
          suggestions: out.suggestions,
          analysis: out.analysis,
          correctedSnippet: a.kind === "CODE" ? (out.correctedSnippet ?? null) : null,
        }),
        scored_at: new Date(),
      })
      .where("id", "=", a.id)
      .where("updated_at", "=", a.updated_at)
      .execute();
  } catch (err) {
    if (!(err instanceof ModelOutputError) && !(err instanceof EvaluationContractError)) captureError(err, { where: "interview.score", answerId });
    await markFailed();
  }
}

export function registerInterviewJobs(): void {
  registerJob("interview.plan", (d) => planInterview(d.interviewId, d.resumeText));
  registerJob("interview.score", (d) => scoreAnswer(d.answerId, d.version));
  registerJob("interview.hangup", (d) => hangup(d.sessionId));
  registerJob("interview.dispatch-scores", async () => {
    const n = await dispatchPendingScores();
    if (n) logger.info({ dispatched: n }, "recovered score dispatches");
  });
  registerJob("interview.sweep", async () => {
    const n = await sweepLiveSessions();
    if (n) logger.info({ expired: n }, "expired abandoned live sessions");
  });
}
