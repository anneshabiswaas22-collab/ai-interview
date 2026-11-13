/**
 * Interview session state machine, independent of any LLM, database or web framework.
 *
 * A prototype domain module for a future audited app foundation.
 * It does NOT authenticate HTTP requests, store sessions, call AI models or issue validated hiring grades.
 *
 * Every mutation requires a server-validated actorId. The caller must persist the
 * returned snapshot atomically with optimistic locking before acknowledging success.
 */

import { createHash } from "node:crypto";

export class InterviewError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "InterviewError";
    this.code = code;
  }
}

function invalid(code, message) {
  throw new InterviewError(code, message);
}

function requiredString(value, name, max = 1000) {
  if (typeof value !== "string" || value.trim().length === 0 || value.length > max) {
    invalid("INVALID_INPUT", name + " must be a nonempty string of at most " + max + " characters");
  }
  return value.trim();
}

function timestamp(now) {
  if (!Number.isSafeInteger(now) || now <= 0) invalid("INVALID_TIME", "now must be a positive Unix millisecond timestamp");
  return now;
}

function authorized(session, actorId) {
  if (!session || !actorId || session.ownerId !== actorId) {
    invalid("NOT_FOUND", "Interview not found");
  }
}

// Store a content fingerprint rather than a second copy of each answer. This is
// not encryption; snapshots and their transcript still need normal data protection.
function fingerprint(kind, text = null) {
  return createHash("sha256").update(JSON.stringify([kind, text])).digest("hex");
}

function isReplay(session, requestId, digest) {
  const previous = (session.processedRequests ?? []).find((item) => item.id === requestId);
  if (previous) {
    if (previous.digest !== digest) invalid("IDEMPOTENCY_CONFLICT", "Request id was already used for a different operation or answer");
    return true;
  }
  // Old prototype snapshots had IDs but no payload fingerprint. A replay cannot
  // be compared safely; do not silently treat an unrelated action as a retry.
  if (session.processedRequestIds.includes(requestId)) invalid("IDEMPOTENCY_UNVERIFIABLE", "Cannot verify a request recorded by an older snapshot");
  return false;
}

function markProcessed(session, requestId, digest) {
  return {
    ...session,
    processedRequestIds: [...session.processedRequestIds, requestId],
    processedRequests: [...(session.processedRequests ?? []), { id: requestId, digest }],
  };
}

function append(session, event) {
  const sequence = session.events.length + 1;
  const next = { ...session, version: session.version + 1 };
  next.events = [
    ...session.events,
    {
      eventId: session.id + ":" + sequence,
      sequence,
      ...event,
    },
  ];
  return next;
}

function questionEvent(question, now) {
  return { kind: "interviewer.question", questionId: question.id, competency: question.competency, text: question.text, at: now };
}

function finishActive(session, now, reason) {
  if (session.status !== "ACTIVE") return session;
  const s = append(session, { kind: "interview.completed", at: now, reason });
  return { ...s, status: "COMPLETED", completedAt: now };
}

/**
 * Normalize a bounded, caller-provided plan. Upstream interviewer planning and
 * generation must be server-side and are deliberately outside this core.
 */
export function validatePlan(input) {
  if (!Array.isArray(input) || input.length < 1 || input.length > 20) {
    invalid("INVALID_PLAN", "A plan must contain 1 to 20 questions");
  }
  const ids = new Set();
  return input.map((q) => {
    if (!q || typeof q !== "object") invalid("INVALID_PLAN", "Question must be an object");
    const id = requiredString(q.id, "question id", 128);
    if (ids.has(id)) invalid("INVALID_PLAN", "Duplicate question id");
    ids.add(id);
    const competency = requiredString(q.competency, "competency", 128);
    const text = requiredString(q.text, "question text", 2000);
    const maxFollowUps = q.maxFollowUps ?? 1;
    if (!Number.isInteger(maxFollowUps) || maxFollowUps < 0 || maxFollowUps > 2) {
      invalid("INVALID_PLAN", "maxFollowUps must be between 0 and 2");
    }
    return { id, competency, text, maxFollowUps };
  });
}

/**
 * Create a session after the HTTP layer has authenticated the owner and checked
 * quota. No user-provided model instructions or evaluation scores are accepted.
 */
export function createSession({ id, ownerId, role, seniority, questions, now, durationMinutes = 20 }) {
  const plan = validatePlan(questions);
  if (!Number.isInteger(durationMinutes) || durationMinutes < 5 || durationMinutes > 120) {
    invalid("INVALID_DURATION", "Duration must be 5 to 120 minutes");
  }
  const startedAt = timestamp(now);
  const sessionId = requiredString(id, "session id", 128);
  const owner = requiredString(ownerId, "owner id", 128);
  const session = {
    id: sessionId,
    ownerId: owner,
    role: requiredString(role, "role", 128),
    seniority: requiredString(seniority, "seniority", 64),
    plan,
    status: "ACTIVE",
    currentIndex: 0,
    followUpsUsed: 0,
    startedAt,
    deadlineAt: startedAt + durationMinutes * 60_000,
    completedAt: null,
    version: 1,
    processedRequestIds: [],
    processedRequests: [],
    events: [],
  };
  const first = append(session, questionEvent(plan[0], startedAt));
  return { ...first, version: 1 };
}

function nextQuestion(session, now) {
  const nextIndex = session.currentIndex + 1;
  if (nextIndex >= session.plan.length) return finishActive(session, now, "plan_finished");
  const next = append(session, questionEvent(session.plan[nextIndex], now));
  return { ...next, currentIndex: nextIndex, followUpsUsed: 0 };
}

function checkDeadline(session, now) {
  if (now < session.startedAt) invalid("INVALID_TIME", "Time precedes session start");
  if (now < session.events[session.events.length - 1].at) invalid("INVALID_TIME", "Time precedes last event");
  return now >= session.deadlineAt;
}

/**
 * Record an answer and choose either a follow-up or the next question.
 * choice comes from a trusted server-side interviewer policy, NEVER the browser.
 * The candidate answer is transcript data, not executable control instructions.
 */
export function submitAnswer(session, { actorId, requestId, text, now, choice }) {
  authorized(session, actorId);
  const request = requiredString(requestId, "request id", 128);
  const answer = requiredString(text, "candidate answer", 10_000);
  const digest = fingerprint("answer", answer);
  if (isReplay(session, request, digest)) return session;
  if (session.status !== "ACTIVE") invalid("SESSION_CLOSED", "Interview is not active");
  timestamp(now);
  if (checkDeadline(session, now)) return markProcessed(finishActive(session, now, "time_expired"), request, digest);
  if (!choice || !["probe", "next"].includes(choice.kind)) {
    invalid("INVALID_CHOICE", "Trusted policy must choose probe or next");
  }
  const question = session.plan[session.currentIndex];
  if (choice.kind === "probe" && session.followUpsUsed >= question.maxFollowUps) {
    invalid("PROBE_LIMIT", "Follow-up cap reached");
  }
  let state = append(session, { kind: "candidate.answer", questionId: question.id, text: answer, at: now });
  if (choice.kind === "probe") {
    const probe = requiredString(choice.text, "follow-up text", 2000);
    state = append(state, { kind: "interviewer.follow_up", questionId: question.id, competency: question.competency, text: probe, at: now });
    state = { ...state, followUpsUsed: state.followUpsUsed + 1 };
  } else {
    state = nextQuestion(state, now);
  }
  return markProcessed(state, request, digest);
}

/** Candidate skip is not a scored answer. */
export function skipQuestion(session, { actorId, requestId, now }) {
  authorized(session, actorId);
  const request = requiredString(requestId, "request id", 128);
  const digest = fingerprint("skip");
  if (isReplay(session, request, digest)) return session;
  if (session.status !== "ACTIVE") invalid("SESSION_CLOSED", "Interview is not active");
  timestamp(now);
  if (checkDeadline(session, now)) return markProcessed(finishActive(session, now, "time_expired"), request, digest);
  const question = session.plan[session.currentIndex];
  let state = append(session, { kind: "candidate.skipped", questionId: question.id, at: now });
  state = nextQuestion(state, now);
  return markProcessed(state, request, digest);
}

export function finishSession(session, { actorId, now }) {
  authorized(session, actorId);
  timestamp(now);
  if (session.status === "COMPLETED") return session;
  if (now < session.events[session.events.length - 1].at) invalid("INVALID_TIME", "Cannot finish in the past");
  return finishActive(session, now, now >= session.deadlineAt ? "time_expired" : "candidate_finished");
}

/**
 * Construct a report from a TRUSTED server-side evaluator's grades.
 * Reject ungrounded evidence IDs and unsupported scores.
 * This function does not invent scores, infer candidates' traits, or certify hiring fit.
 */
export function compilePracticeReport(session, { actorId, grades }) {
  authorized(session, actorId);
  if (session.status !== "COMPLETED") invalid("SESSION_ACTIVE", "Finish interview before generating report");
  if (!Array.isArray(grades)) invalid("INVALID_GRADES", "Grades must be an array");
  const answerIds = new Set(session.events.filter((e) => e.kind === "candidate.answer").map((e) => e.eventId));
  const criteria = grades.map((g) => {
    if (!g || typeof g !== "object") invalid("INVALID_GRADES", "Grade must be an object");
    const criterion = requiredString(g.criterion, "criterion", 128);
    if (!Number.isInteger(g.score) || g.score < 0 || g.score > 5) invalid("INVALID_GRADES", "Grade score must be between 0 and 5");
    if (!Array.isArray(g.evidenceEventIds) || g.evidenceEventIds.length === 0 ||
        !g.evidenceEventIds.every((id) => answerIds.has(id))) {
      invalid("UNGROUNDED_GRADE", "Each grade must cite at least one candidate answer event");
    }
    return {
      criterion,
      score: g.score,
      evidenceEventIds: [...new Set(g.evidenceEventIds)],
      coaching: requiredString(g.coaching, "coaching", 2000),
    };
  });
  return {
    sessionId: session.id,
    type: "practice_feedback",
    criteria,
    disclaimer: "AI-supported practice coaching, not a validated hiring decision.",
  };
}
