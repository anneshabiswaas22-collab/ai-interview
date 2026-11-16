/** The dashboard's single "Next step": continue what is running, else practise the weakest topics, else start an interview. */
import type { WeakTopic } from "./practice";
import type { HistoryRow, Stats } from "./types";

export const WEAK_BELOW = 7;
export const MAX_WEAK_TARGETS = 3;
const isActiveRow = (r: HistoryRow) => r.status === "in_progress" || r.status === "paused";

export type NextStep =
  | { kind: "continue"; row: HistoryRow; question: number; total: number }
  | { kind: "practice"; targets: WeakTopic[]; weak: WeakTopic[] }
  | { kind: "first" }
  | { kind: "another" };

/** Topics scoring below the bar, weakest first (the order the stats endpoint gives them). */
export const weakTopics = (stats: Pick<Stats, "topics"> | null | undefined): WeakTopic[] =>
  (stats?.topics ?? []).filter((t) => t.average_score < WEAK_BELOW).map((t) => ({ topic: t.topic, untagged: t.untagged }));

/** null while the history is unknown. `stats` may be missing (still loading or failed): the weak-topic step is then simply skipped. */
export function pickNextStep(rows: HistoryRow[] | null | undefined, stats: Pick<Stats, "topics"> | null | undefined): NextStep | null {
  if (!rows) return null;
  const open = rows.find(isActiveRow);
  if (open) return { kind: "continue", row: open, question: Math.min(open.total, open.answered + open.skipped + 1), total: open.total };
  const weak = weakTopics(stats);
  if (weak.length) return { kind: "practice", targets: weak.slice(0, MAX_WEAK_TARGETS), weak };
  return rows.length === 0 ? { kind: "first" } : { kind: "another" };
}

/** "Python, “SQL” and 1 more" is overkill for a headline: names only, comma separated. */
export const topicNames = (topics: WeakTopic[]) => topics.map((t) => (t.untagged ? "No topic set" : t.topic)).join(", ");
