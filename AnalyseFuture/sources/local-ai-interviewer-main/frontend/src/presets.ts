/** Interview presets: one click fills the setup form. Pure functions, so the mapping and the "is this preset still active?" check are testable. */
import type { InterviewConfig } from "./types";
import type { Source } from "./resumeHelpers";

export type PresetId = "quick" | "full" | "resume";
export const PRESET_IDS: PresetId[] = ["quick", "full", "resume"];
export const QUICK_QUESTIONS = 5;

export const PRESET_INFO: Record<PresetId, { title: string; desc: string; icon: "bolt" | "clock" | "file" }> = {
  quick: { title: "Quick practice", desc: "5 questions in order, 1 follow‑up", icon: "bolt" },
  full: { title: "Full mock", desc: "Adaptive and progressive, 45 min, up to 8 questions, 2 follow‑ups", icon: "clock" },
  resume: { title: "Resume round", desc: "Adaptive questions about your resume", icon: "file" },
};

type CfgPart = Pick<InterviewConfig, "mode" | "strategy" | "max_questions" | "max_followups" | "time_limit_minutes" | "order">;

/** What the form currently holds, as far as presets care. */
export interface PresetState {
  cfg: Partial<CfgPart>;
  source: Source;
  selectMode: "all" | "selected";
  selectedIds: number[];
  autoOn: boolean;
}
/** What the page knows: the bank's question ids in order, and the ready resume a preset may use (null = none). */
export interface PresetContext { bankIds: number[]; resumeId: number | null }
export interface PresetPlan {
  cfg: Partial<CfgPart>;
  source?: Source;
  selectMode?: "all" | "selected";
  selectedIds?: number[];
  auto?: { on: boolean; id?: number };
  note?: string;
}

const same = (a: number[], b: number[]) => a.length === b.length && b.every((x) => a.includes(x));
const quickIds = (ctx: PresetContext) => ctx.bankIds.slice(0, QUICK_QUESTIONS);
const plural = (n: number) => `${n} question${n === 1 ? "" : "s"}`;

/** Why a preset cannot be used right now (null = it can). */
export function presetDisabledReason(id: PresetId, ctx: PresetContext, resumesPending = false): string | null {
  if (id === "resume") return ctx.resumeId == null ? (resumesPending ? "Your resume is still being read." : "Add a resume first.") : null;
  return ctx.bankIds.length === 0 ? "Add questions to your question bank first." : null;
}

/** The settings a preset puts in the form; null when it is unavailable. */
export function presetPlan(id: PresetId, ctx: PresetContext): PresetPlan | null {
  if (presetDisabledReason(id, ctx)) return null;
  if (id === "quick") {
    const ids = quickIds(ctx);
    return { cfg: { mode: "fixed", order: "supplied", max_followups: 1, time_limit_minutes: null }, source: "bank", selectMode: "selected", selectedIds: ids, auto: { on: false },
      note: ids.length < QUICK_QUESTIONS ? `Your question bank has only ${plural(ids.length)}, so this round uses ${ids.length === 1 ? "it" : `all ${ids.length}`}.` : undefined };
  }
  if (id === "full") {
    return { cfg: { mode: "adaptive", strategy: "progressive", time_limit_minutes: 45, max_questions: 8, max_followups: 2 }, source: "bank", selectMode: "all", auto: { on: false },
      note: ctx.bankIds.length < 8 ? `Your question bank has only ${plural(ctx.bankIds.length)}, so the interview can ask at most ${ctx.bankIds.length}.` : undefined };
  }
  return { cfg: { mode: "adaptive", strategy: "resume" }, auto: { on: true, id: ctx.resumeId! } };
}

/** The preset the form still matches exactly (null once the user changes any setting that a preset controls). */
export function activePreset(st: PresetState, ctx: PresetContext): PresetId | null {
  const c = st.cfg;
  if (c.mode === "fixed" && c.order === "supplied" && c.max_followups === 1 && (c.time_limit_minutes ?? null) === null && st.source === "bank" && !st.autoOn
    && st.selectMode === "selected" && ctx.bankIds.length > 0 && same(st.selectedIds, quickIds(ctx)) && !presetDisabledReason("quick", ctx)) return "quick";
  if (c.mode === "adaptive" && c.strategy === "progressive" && c.time_limit_minutes === 45 && c.max_questions === 8 && c.max_followups === 2 && st.source === "bank" && !st.autoOn
    && st.selectMode === "all" && !presetDisabledReason("full", ctx)) return "full";
  if (c.mode === "adaptive" && c.strategy === "resume" && st.autoOn && ctx.resumeId != null) return "resume";
  return null;
}
