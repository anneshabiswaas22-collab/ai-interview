import { describe, expect, it } from "vitest";
import { classLabel, currentFollowupKind, decisionLabel, deltaInfo, dimLabel, endReasonLabel, fmtClock, minutesLabel, remainingNow, resumeStrategyAvailable, shownDimensions, timelineRows, weightShares } from "../intel";
import type { Turn } from "../types";

describe("intel helpers", () => {
  it("formats clocks", () => {
    expect(fmtClock(0)).toBe("00:00"); expect(fmtClock(725)).toBe("12:05"); expect(fmtClock(3725)).toBe("1:02:05"); expect(fmtClock(-4)).toBe("00:00");
  });
  it("counts down from the server value and never below zero; null means no limit", () => {
    expect(remainingNow(null, 0, 5000)).toBeNull();
    expect(remainingNow(100, 1000, 4000)).toBe(97);
    expect(remainingNow(2, 0, 10_000)).toBe(0);
  });
  it("labels time limits", () => {
    expect(minutesLabel(null)).toBe("No limit"); expect(minutesLabel(30)).toBe("30 min"); expect(minutesLabel(120)).toBe("2 h"); expect(minutesLabel(90)).toBe("1 h 30 min");
  });
  it("describes progress deltas neutrally", () => {
    expect(deltaInfo(null)).toBeNull();
    expect(deltaInfo(1.25)).toMatchObject({ arrow: "↑", tone: "up" });
    expect(deltaInfo(-0.5)).toMatchObject({ arrow: "↓", text: "−0.5", tone: "down" });
    expect(deltaInfo(0.01)).toMatchObject({ arrow: "→", tone: "flat" });
  });
  it("labels classifications, dimensions and decisions with sane fallbacks", () => {
    expect(classLabel("correct_incomplete")).toBe("Correct but incomplete");
    expect(dimLabel("tradeoffs")).toBe("Trade-off analysis"); expect(dimLabel("new_thing")).toBe("New thing");
    expect(decisionLabel("probe_gap")).toBe("Probing a gap"); expect(decisionLabel("odd_one")).toBe("Odd one");
    expect(endReasonLabel("end_time")).toBe("The time limit was reached"); expect(endReasonLabel(null)).toBeNull();
  });
  it("skips null dimensions and hides production unless relevant", () => {
    const rows = shownDimensions({ dimension_scores: { clarity: 5, tradeoffs: null, correctness: 7, production_awareness: 4 }, production_relevant: false });
    expect(rows.map((r) => r[0])).toEqual(["correctness", "clarity"]);
    expect(shownDimensions({ dimension_scores: { production_awareness: 4 }, production_relevant: true })).toHaveLength(1);
  });
  it("turns weights into percentages, largest first", () => {
    expect(weightShares({ a: 0.1, b: 0.3, c: 0 })).toEqual([{ key: "b", pct: 30 }, { key: "a", pct: 10 }]);
    expect(weightShares(undefined)).toEqual([]);
  });
  it("finds the kind of the follow-up on screen", () => {
    const main = { seq: 0, kind: "main", status: "evaluated", evaluation: { followup_kind: "deepen" } } as unknown as Turn;
    const fu = { seq: 1, kind: "followup", status: "asked" } as unknown as Turn;
    expect(currentFollowupKind([main, fu], fu)).toBe("Going deeper");
    expect(currentFollowupKind([main, fu], main)).toBeNull();
    expect(currentFollowupKind([{ ...main, evaluation: {} } as unknown as Turn, fu], fu, "clarify")).toBe("Clarifying");
  });
  it("drops the closing event from the timeline", () => {
    expect(timelineRows([{ kind: "select" }, { kind: "end" }] as never)).toHaveLength(1);
  });
  it("allows the resume strategy only with resume questions", () => {
    expect(resumeStrategyAvailable(0, false, 5)).toBe(false); expect(resumeStrategyAvailable(2, false, 0)).toBe(true); expect(resumeStrategyAvailable(0, true, 5)).toBe(true);
  });
});

import { CONFIDENCE_TONE, monthsLabel, sourceLabel, sourceRef, yearsLabel } from "../intel";
describe("candidate profile helpers", () => {
  it("labels source checks in plain words", () => {
    expect(sourceLabel("verified")).toBe("found in the text"); expect(sourceLabel(undefined)).toBe("not checked"); expect(sourceLabel("zzz")).toBe("not checked");
    expect(CONFIDENCE_TONE.low).toBe("warn");
  });
  it("builds a source reference", () => {
    expect(sourceRef({ section: "Skills", label: "Tools", line: 5 })).toBe("Skills › Tools, line 5");
    expect(sourceRef({ section: "Skills" })).toBe("Skills"); expect(sourceRef({ line: 3 })).toBe("line 3");
  });
  it("formats durations", () => {
    expect(monthsLabel(9)).toBe("9 months"); expect(monthsLabel(1)).toBe("1 month"); expect(monthsLabel(30)).toBe("2 yr 6 mo"); expect(monthsLabel(36)).toBe("3 years");
    expect(yearsLabel(9.24)).toBe("9.2 years"); expect(yearsLabel(1)).toBe("1 year"); expect(yearsLabel(null)).toBe("—");
  });
});

describe("timeWarning / groupSkills", () => {
  it("warns at five minutes or less and never without a limit", async () => {
    const { timeWarning } = await import("../intel");
    expect(timeWarning(null)).toBe(false); expect(timeWarning(undefined)).toBe(false);
    expect(timeWarning(301)).toBe(false); expect(timeWarning(300)).toBe(true); expect(timeWarning(0)).toBe(true);
  });
  it("groups skills into high, medium and listed-only, leaving out empty groups", async () => {
    const { groupSkills } = await import("../intel");
    const s = [{ name: "a", confidence: "low" }, { name: "b", confidence: "high" }, { name: "c", confidence: "medium" }, { name: "d", confidence: "high" }];
    expect(groupSkills(s).map((g) => [g.label, g.skills.map((x) => x.name)])).toEqual([["High confidence", ["b", "d"]], ["Medium confidence", ["c"]], ["Listed only", ["a"]]]);
    expect(groupSkills([{ name: "x", confidence: "low" }]).map((g) => g.key)).toEqual(["listed"]);
    expect(groupSkills([])).toEqual([]);
  });
});
