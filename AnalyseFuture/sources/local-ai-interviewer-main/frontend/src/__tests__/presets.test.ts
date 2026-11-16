import { describe, expect, it } from "vitest";
import { activePreset, presetDisabledReason, presetPlan, type PresetState } from "../presets";

const ctx = (n: number, resumeId: number | null = null) => ({ bankIds: Array.from({ length: n }, (_, i) => 100 + i), resumeId });
const base: PresetState = { cfg: { mode: "fixed", order: "supplied", max_followups: 2, time_limit_minutes: null, strategy: "progressive", max_questions: 10 }, source: "bank", selectMode: "all", selectedIds: [], autoOn: false };
/** What the page does when a preset is clicked. */
const apply = (st: PresetState, id: "quick" | "full" | "resume", c: ReturnType<typeof ctx>): PresetState => {
  const p = presetPlan(id, c)!;
  return { cfg: { ...st.cfg, ...p.cfg }, source: p.source ?? st.source, selectMode: p.selectMode ?? st.selectMode, selectedIds: p.selectedIds ?? st.selectedIds, autoOn: p.auto ? p.auto.on : st.autoOn };
};

describe("presetPlan", () => {
  it("quick practice: 5 questions, fixed order, one follow-up, no time limit", () => {
    const p = presetPlan("quick", ctx(12))!;
    expect(p.cfg).toMatchObject({ mode: "fixed", order: "supplied", max_followups: 1, time_limit_minutes: null });
    expect(p.selectedIds).toEqual([100, 101, 102, 103, 104]);
    expect(p.selectMode).toBe("selected"); expect(p.source).toBe("bank"); expect(p.note).toBeUndefined();
  });
  it("quick practice uses what exists and says so when the bank is smaller than 5", () => {
    const p = presetPlan("quick", ctx(3))!;
    expect(p.selectedIds).toEqual([100, 101, 102]);
    expect(p.note).toMatch(/only 3 questions/);
    expect(presetPlan("quick", ctx(1))!.note).toMatch(/only 1 question,.*uses it/);
  });
  it("full mock is adaptive and progressive with 45 minutes, 8 questions and 2 follow-ups; every setting is one the backend accepts", () => {
    const p = presetPlan("full", ctx(20))!;
    expect(p.cfg).toEqual({ mode: "adaptive", strategy: "progressive", time_limit_minutes: 45, max_questions: 8, max_followups: 2 });
    const c = p.cfg;
    expect(c.time_limit_minutes! >= 5 && c.time_limit_minutes! <= 240).toBe(true);     // InterviewConfig: 5..240
    expect(c.max_questions! >= 1 && c.max_questions! <= 60).toBe(true);                 // 1..60
    expect(c.max_followups! >= 0 && c.max_followups! <= 3).toBe(true);                  // 0..3
    expect(p.selectMode).toBe("all"); expect(p.auto).toEqual({ on: false });
    expect(presetPlan("full", ctx(5))!.note).toMatch(/at most 5/);
  });
  it("resume round turns on the offline resume questions for the ready resume", () => {
    const p = presetPlan("resume", ctx(4, 7))!;
    expect(p.cfg).toEqual({ mode: "adaptive", strategy: "resume" });
    expect(p.auto).toEqual({ on: true, id: 7 });
  });
  it("is unavailable, with a reason, when there is nothing to build it from", () => {
    expect(presetDisabledReason("resume", ctx(4, null))).toMatch(/Add a resume/);
    expect(presetDisabledReason("resume", ctx(4, null), true)).toMatch(/still being read/);
    expect(presetPlan("resume", ctx(4, null))).toBeNull();
    expect(presetDisabledReason("quick", ctx(0))).toMatch(/question bank/);
    expect(presetPlan("full", ctx(0))).toBeNull();
    expect(presetDisabledReason("quick", ctx(2))).toBeNull();
  });
});

describe("activePreset", () => {
  it("marks the preset that was just applied", () => {
    for (const id of ["quick", "full"] as const) expect(activePreset(apply(base, id, ctx(12)), ctx(12))).toBe(id);
    expect(activePreset(apply(base, "resume", ctx(12, 3)), ctx(12, 3))).toBe("resume");
  });
  it("marks nothing for the untouched defaults", () => { expect(activePreset(base, ctx(12))).toBeNull(); });
  it("drops the mark as soon as a setting it controls changes", () => {
    const c = ctx(12, 3);
    const quick = apply(base, "quick", c);
    expect(activePreset({ ...quick, cfg: { ...quick.cfg, max_followups: 2 } }, c)).toBeNull();
    expect(activePreset({ ...quick, selectedIds: quick.selectedIds.slice(1) }, c)).toBeNull();
    expect(activePreset({ ...quick, selectMode: "all" }, c)).toBeNull();
    expect(activePreset({ ...quick, autoOn: true }, c)).toBeNull();
    const full = apply(base, "full", c);
    expect(activePreset({ ...full, cfg: { ...full.cfg, time_limit_minutes: 30 } }, c)).toBeNull();
    expect(activePreset({ ...full, cfg: { ...full.cfg, max_questions: 9 } }, c)).toBeNull();
    expect(activePreset({ ...full, cfg: { ...full.cfg, strategy: "mixed" } }, c)).toBeNull();
    expect(activePreset({ ...full, source: "both" }, c)).toBeNull();
    const res = apply(base, "resume", c);
    expect(activePreset({ ...res, autoOn: false }, c)).toBeNull();
    expect(activePreset({ ...res, cfg: { ...res.cfg, mode: "fixed" } }, c)).toBeNull();
  });
  it("matches Quick practice when the bank has fewer than 5 questions and all of them are chosen", () => {
    const c = ctx(3);
    expect(activePreset(apply(base, "quick", c), c)).toBe("quick");
  });
  it("never reports the resume preset without a ready resume", () => {
    expect(activePreset(apply(base, "resume", ctx(4, 3)), ctx(4, null))).toBeNull();
  });
});
