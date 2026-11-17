/**
 * Checks quotation provenance for written practice feedback, not the truth of a
 * model's judgment. Callers supply only server-owned answer events for the answer
 * being scored; browser transcripts and other questions are not evidence sources.
 *
 * This is an independent implementation of the repository's evidence-contract
 * design. It does not create a second interview engine or adjust model judgments.
 */
import type { TextFeedbackEvidence } from "@open-conversation/types";
import { z } from "zod";

const nonblank = (max: number) =>
  z
    .string()
    .min(1)
    .max(max)
    .refine((text) => text.trim().length > 0, "Must not be blank");

const assessment = z
  .object({
    criterionId: z.enum(["domain", "communication"]),
    score: z.number().int().min(1).max(100).nullable(),
    confidence: z.enum(["low", "medium", "high", "insufficient"]),
    evidence: z.array(z.object({ eventId: nonblank(128), quote: nonblank(1000) }).strict()).max(8),
    observations: z
      .array(
        z
          .object({
            kind: z.enum(["strength", "gap", "next_step"]),
            text: nonblank(500),
            evidenceIndexes: z.array(z.number().int().min(0).max(7)).min(1).max(8),
          })
          .strict()
      )
      .max(8),
  })
  .strict()
  .superRefine((value, ctx) => {
    const insufficient = value.score === null;
    if (
      insufficient
        ? value.confidence !== "insufficient" ||
          value.evidence.length !== 0 ||
          value.observations.length !== 0
        : value.confidence === "insufficient" ||
          value.evidence.length === 0 ||
          value.observations.length === 0
    ) {
      ctx.addIssue({
        code: "custom",
        message: "A scored criterion needs evidence; an insufficient criterion must be unscored",
      });
    }
    const seen = new Set<string>();
    value.evidence.forEach((entry, index) => {
      const key = JSON.stringify([entry.eventId, entry.quote]);
      if (seen.has(key)) {
        ctx.addIssue({ code: "custom", path: ["evidence", index], message: "Duplicate evidence" });
      }
      seen.add(key);
    });
    value.observations.forEach((observation, index) => {
      const refs = observation.evidenceIndexes;
      if (new Set(refs).size !== refs.length || refs.some((ref) => ref >= value.evidence.length)) {
        ctx.addIssue({
          code: "custom",
          path: ["observations", index, "evidenceIndexes"],
          message: "Observations must cite distinct evidence entries in their own criterion",
        });
      }
    });
  });

/** Strict provider contract. Invalid fields are rejected, never silently stripped. */
export const textEvidenceOutput = z
  .object({ assessments: z.array(assessment).length(2) })
  .strict()
  .superRefine((value, ctx) => {
    if (new Set(value.assessments.map((item) => item.criterionId)).size !== 2) {
      ctx.addIssue({ code: "custom", message: "Provide one assessment for each criterion" });
    }
  });

/** Reject unknown IDs and altered quotations before any feedback can be persisted. */
export function validateTextEvidence(
  output: unknown,
  answers: { id: string; text: string }[]
): TextFeedbackEvidence {
  const parsed = textEvidenceOutput.parse(output);
  const sources = new Map(answers.map((answer) => [answer.id, answer.text]));
  if (sources.size !== answers.length) throw new Error("Ambiguous answer evidence sources");
  for (const criterion of parsed.assessments) {
    for (const entry of criterion.evidence) {
      const text = sources.get(entry.eventId);
      // Do not normalise quotes: their exact bytes must occur in the stored answer.
      if (text === undefined || !text.includes(entry.quote)) {
        throw new Error("Feedback evidence does not quote an allowed answer event");
      }
    }
  }
  return {
    rubricVersion: "text-practice-v1",
    criteria: ["domain", "communication"].map((criterionId) =>
      parsed.assessments.find((item) => item.criterionId === criterionId)!
    ),
  };
}
