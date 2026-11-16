/** Pure helpers for adaptive interviews, richer feedback and the report's intelligence sections (no React, no network). */
import type { AdaptiveEvent, Classification, Evaluation, FollowupKind, Level, Strategy, Turn } from "./types";

export const DIM_LABEL: Record<string, string> = {
  correctness: "Correctness", completeness: "Completeness", depth: "Depth", practical_application: "Practical use", clarity: "Clarity", production_awareness: "Production",
  conceptual_understanding: "Conceptual understanding", problem_solving: "Problem-solving", edge_cases: "Edge-case awareness", tradeoffs: "Trade-off analysis",
};
export const dimLabel = (k: string) => DIM_LABEL[k] ?? k.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

export const CLASS_LABEL: Record<Classification, string> = {
  correct: "Correct", correct_incomplete: "Correct but incomplete", partially_correct: "Partially correct", incorrect: "Incorrect", no_attempt: "No real attempt", uncertain: "Uncertain",
};
export const CLASS_TONE: Record<Classification, "ok" | "blue" | "warn" | "bad" | ""> = {
  correct: "ok", correct_incomplete: "blue", partially_correct: "warn", incorrect: "bad", no_attempt: "", uncertain: "",
};
export const classLabel = (k: string) => CLASS_LABEL[k as Classification] ?? k.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

export const FOLLOWUP_LABEL: Record<FollowupKind, string> = { probe_gap: "Probing a gap", clarify: "Clarifying", deepen: "Going deeper", scenario: "Practical scenario" };
export const followupLabel = (k: string | null | undefined) => (k ? FOLLOWUP_LABEL[k as FollowupKind] ?? null : null);

/** The kind of the follow-up now on screen: the kind recorded on the evaluation of the answer that led to it (or the adaptive decision). */
export function currentFollowupKind(thread: Turn[], turn: Turn | null, decision?: string | null): string | null {
  if (!turn || turn.kind !== "followup") return null;
  const prev = [...thread].filter((t) => t.seq < turn.seq && t.evaluation).pop();
  return followupLabel(prev?.evaluation?.followup_kind) ?? followupLabel(decision);
}

export const LEVELS: Level[] = ["beginner", "intermediate", "advanced", "expert"];
export const LEVEL_LABEL: Record<Level, string> = { beginner: "Beginner", intermediate: "Intermediate", advanced: "Advanced", expert: "Expert" };
export const levelLabel = (l: string | null | undefined) => (l ? LEVEL_LABEL[l as Level] ?? l : "");

export const STRATEGIES: { value: Strategy; title: string; desc: string }[] = [
  { value: "progressive", title: "Progressive", desc: "Starts easy and gets harder as you do well." },
  { value: "deep_dive", title: "Deep dive", desc: "Stays on one topic and goes deeper." },
  { value: "practical", title: "Practical", desc: "Favours real-world scenarios and applied questions." },
  { value: "conceptual", title: "Conceptual", desc: "Favours the ideas and theory behind the topic." },
  { value: "mixed", title: "Mixed", desc: "Alternates between topics and styles." },
  { value: "resume", title: "Resume-based", desc: "Questions about your own experience, from your resume." },
];
export const strategyLabel = (s: string | null | undefined) => STRATEGIES.find((x) => x.value === s)?.title ?? (s ?? "");
export const strategyDesc = (s: string) => STRATEGIES.find((x) => x.value === s)?.desc ?? "";

export const DECISION_LABEL: Record<string, string> = {
  start: "Opening question", switch_topic: "New topic", same_topic: "Same topic", deeper: "Going deeper", harder: "Harder", easier: "Easier", level_up: "Harder", level_down: "Easier",
  probe_gap: "Probing a gap", clarify: "Clarifying", deepen: "Going deeper", scenario: "Practical scenario", end_max: "Question limit reached", end_time: "Time limit reached",
  end_pool: "No questions left", end_user: "Ended by you", end: "Ended",
};
export const decisionLabel = (d: string) => DECISION_LABEL[d] ?? d.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

export const END_REASON_LABEL: Record<string, string> = {
  end_max: "All planned questions were asked", end_time: "The time limit was reached", end_pool: "No suitable questions were left", end_user: "You ended the interview", completed: "Completed",
};
export const endReasonLabel = (r: string | null | undefined) => (r ? END_REASON_LABEL[r] ?? r.replace(/_/g, " ") : null);

/** "12:05" or "1:02:05" for a remaining/elapsed number of seconds. Negative or missing values read as 00:00. */
export function fmtClock(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  const mm = String(m).padStart(2, "0"), ss = String(r).padStart(2, "0");
  return h ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

/** In the last five minutes the clock turns to the warning colour (colour only: no blinking). */
export const TIME_WARNING_S = 300;
export const timeWarning = (remaining: number | null | undefined): boolean => remaining != null && remaining <= TIME_WARNING_S;

/** Seconds left now, counted down from the value the server sent `receivedAt` ms ago. null = no time limit. */
export function remainingNow(remaining_s: number | null | undefined, receivedAt: number, now: number): number | null {
  if (remaining_s == null) return null;
  return Math.max(0, Math.round(remaining_s - (now - receivedAt) / 1000));
}

export const minutesLabel = (m: number | null | undefined) => (m ? (m >= 60 && m % 60 === 0 ? `${m / 60} h` : m > 60 ? `${Math.floor(m / 60)} h ${m % 60} min` : `${m} min`) : "No limit");

/** Change versus the last attempt: arrow, signed text and a neutral tone (never red/green: a lower score is information, not a failure). */
export function deltaInfo(delta: number | null | undefined): { arrow: string; text: string; tone: "up" | "down" | "flat" } | null {
  if (delta == null) return null;
  const d = Math.round(delta * 10) / 10;
  if (d === 0) return { arrow: "→", text: "no change", tone: "flat" };
  return d > 0 ? { arrow: "↑", text: `+${d.toFixed(1)}`, tone: "up" } : { arrow: "↓", text: `−${Math.abs(d).toFixed(1)}`, tone: "down" };
}

/** Ordered timeline of the interviewer's decisions, one row per event, skipping the closing "end" marker (shown separately). */
export function timelineRows(events: AdaptiveEvent[]): AdaptiveEvent[] {
  return events.filter((e) => e.kind !== "end");
}
export const levelChanged = (e: AdaptiveEvent) => !!e.level_before && !!e.level_after && e.level_before !== e.level_after;

/** Weights as whole-percent shares, largest first; zero weights dropped. */
export function weightShares(w: Record<string, number> | undefined): { key: string; pct: number }[] {
  if (!w) return [];
  return Object.entries(w).filter(([, v]) => v > 0).map(([key, v]) => ({ key, pct: Math.round(v * 100) })).sort((a, b) => b.pct - a.pct);
}

/** Extra dimensions with a real score only (null/undefined are skipped), in a stable order. */
const DIM_ORDER = ["correctness", "completeness", "conceptual_understanding", "depth", "problem_solving", "edge_cases", "tradeoffs", "practical_application", "clarity", "production_awareness"];
export function shownDimensions(ev: Pick<Evaluation, "dimension_scores" | "production_relevant">): [string, number][] {
  return Object.entries(ev.dimension_scores)
    .filter((e): e is [string, number] => typeof e[1] === "number" && (e[0] !== "production_awareness" || ev.production_relevant))
    .sort((a, b) => (DIM_ORDER.indexOf(a[0]) + 1 || 99) - (DIM_ORDER.indexOf(b[0]) + 1 || 99));
}

/** Resume-based strategy needs resume questions (picked or built automatically). */
export const resumeStrategyAvailable = (resumeQuestionCount: number, autoOn: boolean, autoCount: number) => resumeQuestionCount > 0 || (autoOn && autoCount > 0);

// ------------------------------------------------------------------ candidate profile
export const SOURCE_LABEL: Record<string, string> = { verified: "found in the text", partial: "partly found", not_found: "not found in the text", unknown: "not checked" };
export const SOURCE_TONE: Record<string, "ok" | "warn" | "bad" | ""> = { verified: "ok", partial: "warn", not_found: "bad", unknown: "" };
export const sourceLabel = (s: string | null | undefined) => SOURCE_LABEL[s ?? "unknown"] ?? "not checked";
export type SkillGroupKey = "high" | "medium" | "listed";
export const SKILL_GROUP_LABEL: Record<SkillGroupKey, string> = { high: "High confidence", medium: "Medium confidence", listed: "Listed only" };
/** Candidate skills by how well the resume backs them up: high (listed and used), medium (used, not listed), listed only (low). Empty groups are left out. */
export function groupSkills<T extends { confidence: string }>(skills: T[]): { key: SkillGroupKey; label: string; skills: T[] }[] {
  const of = (k: SkillGroupKey) => skills.filter((s) => (k === "high" ? s.confidence === "high" : k === "medium" ? s.confidence === "medium" : s.confidence !== "high" && s.confidence !== "medium"));
  return (["high", "medium", "listed"] as const).map((key) => ({ key, label: SKILL_GROUP_LABEL[key], skills: of(key) })).filter((g) => g.skills.length > 0);
}

export const CONFIDENCE_TONE: Record<string, "ok" | "blue" | "warn"> = { high: "ok", medium: "blue", low: "warn" };
/** "Resume > Experience > Data Engineer, line 5" style reference. */
export const sourceRef = (s: { section?: string; label?: string; line?: number | null }) =>
  [s.section, s.label].filter(Boolean).join(" › ") + (s.line != null ? `${s.section || s.label ? ", " : ""}line ${s.line}` : "");
export const monthsLabel = (m: number) => (m >= 24 && m % 12 === 0 ? `${m / 12} years` : m >= 12 ? `${Math.floor(m / 12)} yr ${m % 12} mo` : `${m} month${m === 1 ? "" : "s"}`);
export const yearsLabel = (y: number | null | undefined) => (y == null ? "—" : `${Math.round(y * 10) / 10} year${Math.round(y * 10) / 10 === 1 ? "" : "s"}`);
