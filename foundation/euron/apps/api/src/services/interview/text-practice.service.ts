/** Text practice: server-selected questions, owner checks and retry-safe answers. */
import { createHash } from "node:crypto";
import type { Transaction } from "kysely";
import type { TextPracticeAnswer, TextPracticeState } from "@open-conversation/types";
import { requireActive, requireActor, type Actor } from "../../core/context";
import { withTransaction } from "../../core/effects";
import { conflict, notFound } from "../../core/errors";
import { newId } from "../../core/ids";
import { db } from "../../db/kysely";
import type { DB } from "../../db/types";
import { planOf } from "../../presenters/interview.presenter";
import { dispatchScore, recordScoreDispatch } from "../../jobs/score-outbox";
import { ownedInterview } from "./interview.service";
import { nextPosition, questionAt } from "./plan";

type Executor = typeof db | Transaction<DB>;

async function state(exec: Executor, interviewId: string): Promise<TextPracticeState> {
  const session = await exec.selectFrom("text_practice_sessions").selectAll().where("interview_id", "=", interviewId).executeTakeFirst();
  if (!session) throw notFound("Text practice has not been started", "TEXT_PRACTICE_NOT_FOUND");
  const interview = await exec.selectFrom("interviews").select("status").where("id", "=", interviewId).executeTakeFirstOrThrow();
  const events = await exec.selectFrom("text_practice_events").selectAll().where("interview_id", "=", interviewId).orderBy("sequence").execute();
  return {
    interviewId,
    status: interview.status,
    version: session.version,
    consentedAt: session.consented_at.toISOString(),
    events: events.map((e) => ({ id: e.id, sequence: e.sequence, kind: e.kind, round: e.round_index, question: e.question_index, text: e.text, createdAt: e.created_at.toISOString() })),
  };
}

export async function getTextPractice(actor: Actor, interviewId: string): Promise<TextPracticeState> {
  return db.transaction().execute(async (trx) => {
    await ownedInterview(requireActor(actor).id, interviewId, trx, true);
    return state(trx, interviewId);
  });
}

export async function startTextPractice(actor: Actor, interviewId: string): Promise<TextPracticeState> {
  const a = requireActive(actor);
  return withTransaction(async (trx) => {
    const interview = await ownedInterview(a.id, interviewId, trx, true);
    const existing = await trx.selectFrom("text_practice_sessions").select("interview_id").where("interview_id", "=", interviewId).executeTakeFirst();
    if (existing) return state(trx, interviewId);
    if (interview.status !== "READY" || interview.started_at) throw conflict("This interview has already started or is not ready for text practice", "INTERVIEW_MODE_CONFLICT");
    const plan = planOf(interview);
    const first = plan && questionAt(plan, 0, 0);
    if (!first) throw conflict("The interview plan is not ready", "PLAN_NOT_READY");
    await trx.insertInto("text_practice_sessions").values({ interview_id: interviewId }).execute();
    await trx.insertInto("text_practice_events").values({ id: newId(), interview_id: interviewId, sequence: 1, kind: "QUESTION", round_index: 0, question_index: 0, text: first.text }).execute();
    await trx.updateTable("interviews").set({ status: "IN_PROGRESS", started_at: new Date(), updated_at: new Date(), current_round: 0, current_question: 0 }).where("id", "=", interviewId).execute();
    return state(trx, interviewId);
  });
}

export async function answerTextPractice(actor: Actor, interviewId: string, input: TextPracticeAnswer): Promise<TextPracticeState> {
  const a = requireActive(actor);
  const answerText = input.text.trim();
  const fingerprint = createHash("sha256").update(JSON.stringify([input.expectedVersion, answerText])).digest("hex");
  return withTransaction(async (trx, fx) => {
    const interview = await ownedInterview(a.id, interviewId, trx, true);
    const session = await trx.selectFrom("text_practice_sessions").selectAll().where("interview_id", "=", interviewId).executeTakeFirst();
    if (!session) throw notFound("Text practice has not been started", "TEXT_PRACTICE_NOT_FOUND");
    const previous = await trx.selectFrom("text_practice_requests").select("fingerprint").where("interview_id", "=", interviewId).where("request_id", "=", input.requestId).executeTakeFirst();
    if (previous) {
      if (previous.fingerprint !== fingerprint) throw conflict("This request ID was already used for another answer", "IDEMPOTENCY_CONFLICT");
      return state(trx, interviewId);
    }
    if (interview.status !== "IN_PROGRESS") throw conflict("This interview is finished", "INTERVIEW_COMPLETED");
    if (session.version !== input.expectedVersion) throw conflict("The interview changed; refresh before answering", "TEXT_VERSION_CONFLICT");
    const plan = planOf(interview);
    const asked = plan && questionAt(plan, interview.current_round, interview.current_question);
    if (!plan || !asked) throw conflict("The current question is unavailable", "QUESTION_NOT_FOUND");
    // Question text and position are selected from the frozen server-side plan, never the client.
    const answer = await trx.insertInto("answers").values({
      id: newId(), interview_id: interviewId, round_index: interview.current_round, question_index: interview.current_question,
      kind: "TEXT", transcript: JSON.stringify([{ role: "interviewer", text: asked.text }, { role: "candidate", text: answerText }]),
      code: null, language: null, status: "SCORING",
    }).returningAll().executeTakeFirstOrThrow();
    const sequence = session.version * 2;
    await trx.insertInto("text_practice_events").values({ id: newId(), interview_id: interviewId, sequence, kind: "ANSWER", round_index: interview.current_round, question_index: interview.current_question, text: answerText }).execute();
    const next = nextPosition(plan, interview.current_round, interview.current_question);
    const nextQuestion = next ? questionAt(plan, next.round, next.question) : null;
    await trx.insertInto("text_practice_events").values({
      id: newId(), interview_id: interviewId, sequence: sequence + 1, kind: next ? "QUESTION" : "COMPLETED",
      round_index: next?.round ?? interview.current_round, question_index: next?.question ?? interview.current_question,
      text: nextQuestion?.text ?? "Interview completed.",
    }).execute();
    const now = new Date();
    await trx.updateTable("interviews").set(next ? { current_round: next.round, current_question: next.question, updated_at: now } : { status: "COMPLETED", completed_at: now, updated_at: now }).where("id", "=", interviewId).execute();
    await trx.updateTable("text_practice_sessions").set({ version: session.version + 1 }).where("interview_id", "=", interviewId).execute();
    await trx.insertInto("text_practice_requests").values({ interview_id: interviewId, request_id: input.requestId, fingerprint }).execute();
    await recordScoreDispatch(trx, answer.id, answer.updated_at);
    fx.after(() => dispatchScore(answer.id));
    return state(trx, interviewId);
  });
}
