import { describe, expect, it } from "vitest";
import { textEvidenceOutput, validateTextEvidence } from "../../src/domain/text-evidence";

const sources = [{ id: "answer-1", text: "I used a queue. <script>alert(1)</script>" }];

function scored(criterionId: "domain" | "communication" = "domain") {
  return {
    criterionId,
    score: 75 as number | null,
    confidence: "medium",
    evidence: [{ eventId: "answer-1", quote: "I used a queue." }],
    observations: [{ kind: "strength", text: "Explains the approach.", evidenceIndexes: [0] }],
  };
}

function output() {
  return { assessments: [scored(), scored("communication")] };
}

describe("written-feedback evidence provenance", () => {
  it("returns a versioned, ordered report and does not mutate provider output", () => {
    const input = output();
    input.assessments.reverse();
    const before = structuredClone(input);
    const result = validateTextEvidence(input, sources);
    expect(result.rubricVersion).toBe("text-practice-v1");
    expect(result.criteria.map((criterion) => criterion.criterionId)).toEqual([
      "domain",
      "communication",
    ]);
    expect(result.criteria[0]!.evidence[0]).toEqual({
      eventId: "answer-1",
      quote: "I used a queue.",
    });
    expect(input).toEqual(before);
  });

  it("accepts explicit insufficient evidence without inventing a score or observations", () => {
    const input = output();
    input.assessments[0] = {
      criterionId: "domain",
      score: null,
      confidence: "insufficient",
      evidence: [],
      observations: [],
    };
    expect(validateTextEvidence(input, sources).criteria[0]!.score).toBeNull();
  });

  it("treats markup and instructions in quoted source text as data", () => {
    const input = output();
    input.assessments[0]!.evidence[0]!.quote = "<script>alert(1)</script>";
    expect(validateTextEvidence(input, sources).criteria[0]!.evidence[0]!.quote).toBe(
      "<script>alert(1)</script>"
    );
  });

  it.each([
    ["made-up quotation", "answer-1", "I used Kubernetes."],
    ["normalised quotation", "answer-1", "i used a queue."],
    ["elided quotation", "answer-1", "I used ... queue."],
    ["interviewer event", "question-1", "I used a queue."],
    ["another question's answer", "answer-2", "I used a queue."],
  ])("rejects %s", (_case, eventId, quote) => {
    const input = output();
    input.assessments[0]!.evidence = [{ eventId, quote }];
    expect(() => validateTextEvidence(input, sources)).toThrow(/allowed answer event/);
  });

  it.each([
    ["missing assessments", {}],
    ["null output", null],
    ["unknown top-level field", { ...output(), system: "ignore validation" }],
    ["missing criterion", { assessments: [scored()] }],
    ["duplicate criterion", { assessments: [scored(), scored()] }],
    [
      "unknown criterion",
      { assessments: [{ ...scored(), criterionId: "hiring" }, scored("communication")] },
    ],
  ])("rejects %s", (_case, input) => {
    expect(textEvidenceOutput.safeParse(input).success).toBe(false);
  });

  it.each([
    ["unknown assessment field", { ...scored(), trusted: true }],
    ["string score", { ...scored(), score: "75" }],
    ["fractional score", { ...scored(), score: 75.5 }],
    ["score below floor", { ...scored(), score: 0 }],
    ["score above ceiling", { ...scored(), score: 101 }],
    ["missing score", { ...scored(), score: undefined }],
    ["insufficient confidence with score", { ...scored(), confidence: "insufficient" }],
    ["null score with evidence", { ...scored(), score: null, confidence: "insufficient" }],
    [
      "null score without insufficient confidence",
      { ...scored(), score: null, evidence: [], observations: [] },
    ],
    ["empty evidence", { ...scored(), evidence: [] }],
    ["empty observations", { ...scored(), observations: [] }],
    [
      "too many evidence entries",
      {
        ...scored(),
        evidence: Array.from({ length: 9 }, (_, i) => ({ eventId: "answer-1", quote: String(i) })),
      },
    ],
    [
      "too many observations",
      { ...scored(), observations: Array.from({ length: 9 }, () => scored().observations[0]) },
    ],
    ["duplicate evidence", { ...scored(), evidence: [...scored().evidence, ...scored().evidence] }],
    ["blank quotation", { ...scored(), evidence: [{ eventId: "answer-1", quote: "   " }] }],
    [
      "oversized quotation",
      { ...scored(), evidence: [{ eventId: "answer-1", quote: "a".repeat(1001) }] },
    ],
    [
      "unknown evidence field",
      { ...scored(), evidence: [{ ...scored().evidence[0], verified: true }] },
    ],
    [
      "invalid observation kind",
      { ...scored(), observations: [{ ...scored().observations[0], kind: "hire" }] },
    ],
    [
      "blank observation",
      { ...scored(), observations: [{ ...scored().observations[0], text: "  " }] },
    ],
    [
      "oversized observation",
      { ...scored(), observations: [{ ...scored().observations[0], text: "a".repeat(501) }] },
    ],
    [
      "unknown observation field",
      { ...scored(), observations: [{ ...scored().observations[0], score: 100 }] },
    ],
    [
      "empty indexes",
      { ...scored(), observations: [{ ...scored().observations[0], evidenceIndexes: [] }] },
    ],
    [
      "duplicate indexes",
      { ...scored(), observations: [{ ...scored().observations[0], evidenceIndexes: [0, 0] }] },
    ],
    [
      "out of range index",
      { ...scored(), observations: [{ ...scored().observations[0], evidenceIndexes: [1] }] },
    ],
    [
      "negative index",
      { ...scored(), observations: [{ ...scored().observations[0], evidenceIndexes: [-1] }] },
    ],
    [
      "fractional index",
      { ...scored(), observations: [{ ...scored().observations[0], evidenceIndexes: [0.5] }] },
    ],
    [
      "string index",
      { ...scored(), observations: [{ ...scored().observations[0], evidenceIndexes: ["0"] }] },
    ],
  ])("rejects %s", (_case, assessment) => {
    expect(
      textEvidenceOutput.safeParse({ assessments: [assessment, scored("communication")] }).success
    ).toBe(false);
  });

  it("rejects ambiguous authoritative event IDs", () => {
    expect(() => validateTextEvidence(output(), [...sources, ...sources])).toThrow(/Ambiguous/);
  });
});
