import test from "node:test";
import assert from "node:assert/strict";
import { InterviewError, createSession, submitAnswer, skipQuestion, compileEvidenceReport } from "../index.mjs";

const startTime = 1_800_000_000_000;
const questions = [
  { id: "cache", competency: "resilience", text: "What happens when the cache fails?", maxFollowUps: 0 },
  { id: "api", competency: "api_design", text: "What is idempotency?", maxFollowUps: 0 },
];
const rubric = [
  { id: "resilience", label: "Failure handling", questionIds: ["cache"] },
  { id: "api_design", label: "API design", questionIds: ["api"] },
];

function start(id = "interview-1") {
  return createSession({ id, ownerId: "alice", role: "Backend engineer", seniority: "mid", questions, now: startTime });
}
function answer(session, text, requestId, now) {
  return submitAnswer(session, { actorId: "alice", text, requestId, now, choice: { kind: "next" } });
}
function finished() {
  const first = answer(start(), "I would fall back to the database and rate-limit requests.", "one", startTime + 1);
  return answer(first, "I would use an idempotency key for safe retries.", "two", startTime + 2);
}
function input(session = finished()) {
  const answers = session.events.filter((event) => event.kind === "candidate.answer");
  return {
    actorId: "alice", rubricVersion: "backend-v1", rubric: structuredClone(rubric),
    assessments: [
      {
        criterionId: "resilience", score: 3, confidence: "medium",
        evidence: [{ eventId: answers[0].eventId, quote: "rate-limit requests" }],
        observations: [{ kind: "strength", text: "Considered load on the database.", evidenceIndexes: [0] }],
      },
      {
        criterionId: "api_design", score: 4, confidence: "low",
        evidence: [{ eventId: answers[1].eventId, quote: "idempotency key" }],
        observations: [{ kind: "next_step", text: "Explain how you would store the key.", evidenceIndexes: [0] }],
      },
    ],
  };
}
function fails(fn, code) {
  assert.throws(fn, (error) => error instanceof InterviewError && error.code === code);
}

test("returns rubric-ordered feedback with exact answer evidence and independent output", () => {
  const session = finished();
  const args = input(session);
  args.assessments.reverse();
  const report = compileEvidenceReport(session, args);
  assert.deepEqual(report.criteria.map((criterion) => criterion.criterionId), ["resilience", "api_design"]);
  assert.equal(report.criteria[0].evidence[0].quote, "rate-limit requests");
  assert.deepEqual(report.criteria[0].observations[0].evidenceIndexes, [0]);
  assert.match(report.disclaimer, /do not prove the accuracy/);
  args.assessments[1].evidence[0].quote = "changed";
  assert.equal(report.criteria[0].evidence[0].quote, "rate-limit requests");
});

test("requires an authorized owner and a completed interview", () => {
  const session = finished();
  fails(() => compileEvidenceReport(session, { ...input(session), actorId: "mallory" }), "NOT_FOUND");
  fails(() => compileEvidenceReport(start(), { ...input(session) }), "SESSION_ACTIVE");
});

test("rejects made-up, altered or empty quotations", () => {
  const session = finished();
  for (const quote of ["I used a circuit breaker", "RATE-LIMIT REQUESTS", "", "   "]) {
    const args = input(session);
    args.assessments[0].evidence[0].quote = quote;
    fails(() => compileEvidenceReport(session, args), "UNGROUNDED_ASSESSMENT");
  }
});

test("rejects interviewer, another question, or another session as evidence", () => {
  const session = finished();
  const other = finished();
  other.events.find((event) => event.kind === "candidate.answer").eventId = "other:answer";
  const choices = [
    { eventId: session.events[0].eventId, quote: session.events[0].text },
    { eventId: session.events.find((event) => event.questionId === "api" && event.kind === "candidate.answer").eventId, quote: "idempotency key" },
    { eventId: "other:answer", quote: "rate-limit requests" },
  ];
  for (const evidence of choices) {
    const args = input(session);
    args.assessments[0].evidence = [evidence];
    fails(() => compileEvidenceReport(session, args), "UNGROUNDED_ASSESSMENT");
  }
});

test("represents a skipped or unsupported question as unscored, without fabricated evidence", () => {
  const skipped = skipQuestion(start(), { actorId: "alice", requestId: "skip", now: startTime + 1 });
  const session = answer(skipped, "Use an idempotency key.", "two", startTime + 2);
  const args = input(finished());
  args.assessments[0] = { criterionId: "resilience", score: null, confidence: "insufficient", evidence: [], observations: [] };
  args.assessments[1].evidence[0].eventId = session.events.find((event) => event.kind === "candidate.answer").eventId;
  const report = compileEvidenceReport(session, args);
  assert.equal(report.criteria[0].score, null);
  assert.equal(report.criteria[0].confidence, "insufficient");
  args.assessments[0].score = 0;
  args.assessments[0].confidence = "low";
  fails(() => compileEvidenceReport(session, args), "UNGROUNDED_ASSESSMENT");
});

test("rejects unlinked observations and invalid evidence references", () => {
  const session = finished();
  for (const indexes of [[], [1], [-1], [0, 0], [0.5], ["0"]]) {
    const args = input(session);
    args.assessments[0].observations[0].evidenceIndexes = indexes;
    fails(() => compileEvidenceReport(session, args), "UNGROUNDED_ASSESSMENT");
  }
});

test("rejects unknown or duplicate criteria and incomplete evaluator output", () => {
  const session = finished();
  for (const mutate of [
    (a) => { a.assessments[0].criterionId = "invented"; },
    (a) => { a.assessments[1].criterionId = "resilience"; },
    (a) => { a.assessments.pop(); },
    (a) => { a.assessments[0].isHiringRecommendation = true; },
  ]) {
    const args = input(session);
    mutate(args);
    fails(() => compileEvidenceReport(session, args), "INVALID_ASSESSMENT");
  }
});

test("rejects a rubric with repeated criteria, invalid question mappings or duplicate questions", () => {
  const session = finished();
  for (const mutate of [
    (a) => { a.rubric[1].id = "resilience"; },
    (a) => { a.rubric[0].questionIds = ["not-in-plan"]; },
    (a) => { a.rubric[0].questionIds = ["cache", "cache"]; },
    (a) => { a.rubric[0].questionIds = []; },
  ]) {
    const args = input(session);
    mutate(args);
    fails(() => compileEvidenceReport(session, args), "INVALID_RUBRIC");
  }
});

test("rejects invalid scores, confidence and duplicated evidence", () => {
  const session = finished();
  for (const mutate of [
    (a) => { a.assessments[0].score = 6; },
    (a) => { a.assessments[0].score = 1.5; },
    (a) => { a.assessments[0].confidence = "certain"; },
    (a) => { a.assessments[0].score = null; a.assessments[0].confidence = "high"; },
  ]) {
    const args = input(session);
    mutate(args);
    fails(() => compileEvidenceReport(session, args), "INVALID_ASSESSMENT");
  }
  const duplicate = input(session);
  duplicate.assessments[0].evidence.push({ ...duplicate.assessments[0].evidence[0] });
  fails(() => compileEvidenceReport(session, duplicate), "UNGROUNDED_ASSESSMENT");
});
