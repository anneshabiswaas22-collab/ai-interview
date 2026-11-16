import { useEffect, useRef, useState } from "react";
import { fmtClock, levelLabel, remainingNow, strategyLabel, timeWarning } from "../intel";
import type { InterviewState } from "../types";
import Icon from "./Icon";

/** Seconds left on the time limit, counted down here once a second and re-synced to the server's number on every state update. null = no limit. */
export function useRemaining(st: InterviewState | null): number | null {
  const base = st?.time?.remaining_s ?? null;
  const stamp = useRef(Date.now());
  const [now, setNow] = useState(Date.now());
  useEffect(() => { stamp.current = Date.now(); setNow(Date.now()); }, [st, base]);      // every new state is the truth again
  const running = base != null && st?.status === "in_progress";
  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [running]);
  return running ? remainingNow(base, stamp.current, now) : base;
}

/** The quiet strip under the interview header: adaptive facts (topic, level, strategy) and the remaining time. Renders nothing for a fixed interview without a limit. */
export default function RunInfo({ st, remaining }: { st: InterviewState; remaining: number | null }) {
  const ad = st.mode === "adaptive" ? st.adaptive : null;
  const item = st.current?.item;
  if (!ad && remaining == null) return null;
  const warn = timeWarning(remaining);
  return (
    <div className="runinfo" data-testid="runinfo" role="group" aria-label="Interview details">
      {ad && <>
        {item?.topic && <span className="ri"><span className="k">Topic</span><b>{item.topic}</b></span>}
        <span className="ri"><span className="k">Level</span><b>{levelLabel(ad.level)}</b>{ad.target_difficulty && <span className="muted"> · aiming for {ad.target_difficulty}</span>}</span>
        <span className="ri"><span className="k">Strategy</span><b>{strategyLabel(ad.strategy)}</b>{ad.strategy === "deep_dive" && ad.focus_topic && <span className="muted"> · {ad.focus_topic}</span>}</span>
      </>}
      {remaining != null && (
        <span className={`ri time ${warn ? "warn" : ""}`} title="No new question starts after the time limit">
          <Icon name="hourglass" size={14} /><span className="k">Time left</span>
          <b role="timer" aria-label={`Time left ${fmtClock(remaining)}`}>{fmtClock(remaining)}</b>
        </span>
      )}
      {remaining === 0 && <span className="ri timeup">Time is up: finish this answer; no new question will start.</span>}
    </div>
  );
}

export function WhyThisQuestion({ reason }: { reason: string | null | undefined }) {
  if (!reason) return null;
  return <div className="why-q" data-testid="why-question"><Icon name="route" size={13} /><span><b>Why this question:</b> {reason}</span></div>;
}
