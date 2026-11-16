/** Which tabs the report page shows, and which one is remembered for a report (per tab session). */
import type { Report } from "./types";

export type ReportTab = "overview" | "questions" | "skills" | "adaptive";
export const TAB_LABEL: Record<ReportTab, string> = { overview: "Overview", questions: "Questions", skills: "Skills & progress", adaptive: "Adaptive" };

/** The adaptive tab exists only when there is an adaptive timeline or resume coverage / claims to show. */
export function hasAdaptive(r: Pick<Report, "adaptive" | "resume_coverage" | "resume_claims">): boolean {
  return !!r.adaptive || (r.resume_coverage?.claims_total ?? 0) > 0 || (r.resume_claims?.length ?? 0) > 0;
}
export function reportTabs(r: Pick<Report, "adaptive" | "resume_coverage" | "resume_claims">): ReportTab[] {
  return ["overview", "questions", "skills", ...(hasAdaptive(r) ? ["adaptive" as const] : [])];
}

const key = (id: number) => `lai.report.tab.${id}`;
export function readTab(id: number, tabs: ReportTab[]): ReportTab {
  try { const v = sessionStorage.getItem(key(id)); return tabs.find((t) => t === v) ?? "overview"; } catch { return "overview"; }
}
export function saveTab(id: number, tab: ReportTab) { try { sessionStorage.setItem(key(id), tab); } catch { /* ignore */ } }
