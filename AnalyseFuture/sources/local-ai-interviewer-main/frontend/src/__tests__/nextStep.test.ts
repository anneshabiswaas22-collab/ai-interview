import { describe, expect, it } from "vitest";
import { pickNextStep, topicNames, weakTopics } from "../nextStep";
import type { HistoryRow } from "../types";

const row = (over: Partial<HistoryRow>): HistoryRow => ({ id: 1, title: "Mock 1", interview_type: "technical", status: "completed", phase: "", created_at: "", updated_at: "", completed_at: null, total: 8, answered: 0, skipped: 0, has_report: 1, average_score: 6, ...over });
const topics = (...t: [string, number, boolean?][]) => ({ topics: t.map(([topic, average_score, untagged]) => ({ topic, average_score, questions: 3, untagged: !!untagged })) });

describe("pickNextStep", () => {
  it("is unknown until the history is loaded", () => { expect(pickNextStep(null, topics(["SQL", 3]))).toBeNull(); });
  it("1. an interview in progress comes first, with the question it is on", () => {
    const s = pickNextStep([row({ id: 4, status: "in_progress", answered: 2, skipped: 1, total: 8 }), row({ id: 2 })], topics(["SQL", 3]));
    expect(s).toMatchObject({ kind: "continue", question: 4, total: 8 }); expect((s as { row: HistoryRow }).row.id).toBe(4);
  });
  it("treats a paused interview as unfinished and never goes past the last question", () => {
    expect(pickNextStep([row({ status: "paused", answered: 8, total: 8 })], null)).toMatchObject({ kind: "continue", question: 8, total: 8 });
  });
  it("2. otherwise the weakest topics (at most 3, weakest first, only below 7)", () => {
    const s = pickNextStep([row({})], topics(["SQL", 3], ["Spark", 4.5], ["Python", 6], ["Kafka", 6.9], ["Git", 7], ["Docker", 9]));
    expect(s).toMatchObject({ kind: "practice" });
    if (s?.kind === "practice") { expect(s.targets.map((t) => t.topic)).toEqual(["SQL", "Spark", "Python"]); expect(s.weak).toHaveLength(4); }
  });
  it("3. no history at all: start the first interview", () => { expect(pickNextStep([], topics())).toEqual({ kind: "first" }); expect(pickNextStep([], null)).toEqual({ kind: "first" }); });
  it("with history but nothing weak, suggests another interview", () => { expect(pickNextStep([row({})], topics(["SQL", 8]))).toEqual({ kind: "another" }); });
  it("an in-progress interview wins even when there are no stats yet", () => { expect(pickNextStep([row({ status: "in_progress" })], undefined)?.kind).toBe("continue"); });
});

describe("weak topics", () => {
  it("keeps the untagged flag and names untagged questions plainly", () => {
    const w = weakTopics(topics(["Uncategorized", 2, true], ["SQL", 5]));
    expect(w).toEqual([{ topic: "Uncategorized", untagged: true }, { topic: "SQL", untagged: false }]);
    expect(topicNames(w)).toBe("No topic set, SQL");
  });
});
