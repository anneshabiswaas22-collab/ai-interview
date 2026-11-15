/**
 * Interview session state machine, independent of any LLM, database or web framework.
 *
 * A prototype domain module for a future audited app foundation.
 * It does NOT authenticate HTTP requests, store sessions, call AI models or issue validated hiring grades.
 *
 * Every mutation requires a server-validated actorId. The caller must persist the
 * returned snapshot atomically with optimistic locking before acknowledging success.
 */

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
  if (session.processedRequestIds.includes(request)) return session; // idempotent retry
  if (session.status !== "ACTIVE") invalid("SESSION_CLOSED", "Interview is not active");
  timestamp(now);
  if (checkDeadline(session, now)) return finishActive(session, now, "time_expired");
  const answer = requiredString(text, "candidate answer", 10_000);
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
  return { ...state, processedRequestIds: [...session.processedRequestIds, request] };
}

/** Candidate skip is not a scored answer. */
export function skipQuestion(session, { actorId, requestId, now }) {
  authorized(session, actorId);
  const request = requiredString(requestId, "request id", 128);
  if (session.processedRequestIds.includes(request)) return session;
  if (session.status !== "ACTIVE") invalid("SESSION_CLOSED", "Interview is not active");
  timestamp(now);
  if (checkDeadline(session, now)) return finishActive(session, now, "time_expired");
  const question = session.plan[session.currentIndex];
  let state = append(session, { kind: "candidate.skipped", questionId: question.id, at: now });
  state = nextQuestion(state, now);
  return { ...state, processedRequestIds: [...session.processedRequestIds, request] };
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

/**
 * Validate a server-owned rubric and a separate evaluator's structured output.
 *
 * Evidence must quote an actual candidate answer to an allowed question, and each
 * observation cites one or more of its criterion's evidence entries. Unknown or
 * unsupported criteria fail closed. This checks provenance, NOT the correctness,
 * fairness or usefulness of model judgments. Never expose this function as an
 * endpoint accepting scores from a candidate; the caller authenticates the actor,
 * loads the authoritative session/rubric, and invokes a trusted evaluator.
 */
export function compileEvidenceReport(session, { actorId, rubricVersion, rubric, assessments }) {
  authorized(session, actorId);
  if (session.status !== "COMPLETED") invalid("SESSION_ACTIVE", "Finish interview before generating report");
  const version = requiredString(rubricVersion, "rubric version", 128);
  if (!Array.isArray(rubric) || rubric.length < 1 || rubric.length > 20) {
    invalid("INVALID_RUBRIC", "Rubric must contain 1 to 20 criteria");
  }
  const questionIds = new Set(session.plan.map((q) => q.id));
  const criteria = new Map();
  for (const item of rubric) {
    if (!item || typeof item !== "object" || Array.isArray(item)) invalid("INVALID_RUBRIC", "Invalid rubric criterion");
    const id = requiredString(item.id, "criterion id", 128);
    const label = requiredString(item.label, "criterion label", 128);
    if (criteria.has(id) || !Array.isArray(item.questionIds) || item.questionIds.length < 1 || item.questionIds.length > 20 ||
        !item.questionIds.every((q) => typeof q === "string" && questionIds.has(q)) || new Set(item.questionIds).size !== item.questionIds.length) {
      invalid("INVALID_RUBRIC", "Criteria must be unique and name existing questions");
    }
    criteria.set(id, { id, label, questionIds: new Set(item.questionIds) });
  }
  if (!Array.isArray(assessments) || assessments.length !== criteria.size) {
    invalid("INVALID_ASSESSMENT", "Provide exactly one assessment for each rubric criterion");
  }
  const answers = new Map(session.events.filter((event) => event.kind === "candidate.answer").map((event) => [event.eventId, event]));
  const byCriterion = new Map();
  for (const assessment of assessments) {
    if (!assessment || typeof assessment !== "object" || Array.isArray(assessment) ||
        Object.keys(assessment).some((key) => !["criterionId", "score", "confidence", "evidence", "observations"].includes(key))) {
      invalid("INVALID_ASSESSMENT", "Invalid assessment fields");
    }
    const criterion = criteria.get(assessment.criterionId);
    if (!criterion || byCriterion.has(assessment.criterionId)) invalid("INVALID_ASSESSMENT", "Unknown or duplicate criterion");
    const unscored = assessment.score === null;
    if ((!unscored && (!Number.isInteger(assessment.score) || assessment.score < 0 || assessment.score > 5)) ||
        !(unscored ? assessment.confidence === "insufficient" : ["low", "medium", "high"].includes(assessment.confidence))) {
      invalid("INVALID_ASSESSMENT", "Invalid score or confidence");
    }
    if (!Array.isArray(assessment.evidence) || assessment.evidence.length > 8 || (!unscored && assessment.evidence.length === 0)) {
      invalid("UNGROUNDED_ASSESSMENT", "A scored criterion needs candidate evidence");
    }
    const seenEvidence = new Set();
    const evidence = assessment.evidence.map((entry) => {
      if (!entry || typeof entry !== "object" || Array.isArray(entry) ||
          Object.keys(entry).some((key) => !["eventId", "quote"].includes(key)) ||
          typeof entry.eventId !== "string" || typeof entry.quote !== "string" ||
          !entry.quote.trim() || entry.quote.length > 1000) {
        invalid("UNGROUNDED_ASSESSMENT", "Invalid evidence entry");
      }
      const answer = answers.get(entry.eventId);
      if (!answer || !criterion.questionIds.has(answer.questionId) || !answer.text.includes(entry.quote)) {
        invalid("UNGROUNDED_ASSESSMENT", "Evidence must exactly quote an allowed candidate answer");
      }
      const key = JSON.stringify([entry.eventId, entry.quote]);
      if (seenEvidence.has(key)) invalid("UNGROUNDED_ASSESSMENT", "Duplicate evidence entry");
      seenEvidence.add(key);
      return { eventId: entry.eventId, quote: entry.quote };
    });
    if (!Array.isArray(assessment.observations) || assessment.observations.length > 8 ||
        (!unscored && assessment.observations.length === 0)) {
      invalid("INVALID_ASSESSMENT", "A scored criterion needs an evidence-linked observation");
    }
    const observations = assessment.observations.map((observation) => {
      if (!observation || typeof observation !== "object" || Array.isArray(observation) ||
          Object.keys(observation).some((key) => !["kind", "text", "evidenceIndexes"].includes(key)) ||
          !["strength", "gap", "next_step"].includes(observation.kind)) {
        invalid("INVALID_ASSESSMENT", "Invalid observation");
      }
      const text = requiredString(observation.text, "observation", 2000);
      const refs = observation.evidenceIndexes;
      if (!Array.isArray(refs) || refs.length < 1 || refs.length > evidence.length ||
          !refs.every((index) => Number.isInteger(index) && index >= 0 && index < evidence.length) || new Set(refs).size !== refs.length) {
        invalid("UNGROUNDED_ASSESSMENT", "Every observation must cite its criterion evidence");
      }
      return { kind: observation.kind, text, evidenceIndexes: [...refs] };
    });
    byCriterion.set(criterion.id, { criterionId: criterion.id, label: criterion.label, score: assessment.score, confidence: assessment.confidence, evidence, observations });
  }
  return {
    sessionId: session.id,
    type: "practice_feedback",
    rubricVersion: version,
    criteria: [...criteria.keys()].map((id) => byCriterion.get(id)),
    disclaimer: "Practice feedback is not a validated hiring decision. Evidence quotations do not prove the accuracy of an assessment.",
  };
}
