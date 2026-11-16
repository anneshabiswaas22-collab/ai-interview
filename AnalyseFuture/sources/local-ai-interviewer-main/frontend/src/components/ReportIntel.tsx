import { classLabel, CLASS_TONE, decisionLabel, deltaInfo, endReasonLabel, levelChanged, levelLabel, strategyLabel, timelineRows } from "../intel";
import type { Classification, Report } from "../types";
import { CLAIM_VERDICT_TONE } from "../resumeHelpers";
import Icon from "./Icon";
import { scoreClass } from "./ui";

const tone = (s: number | null) => (s == null ? "mute" : s >= 7 ? "ok" : s >= 5 ? "warn" : "bad");
const BAR_TONE: Record<string, string> = { ok: "ok", blue: "blue", warn: "warn", bad: "bad", "": "mute" };

function Bar({ label, value, max, cls, text }: { label: string; value: number | null; max: number; cls: string; text: string }) {
  return (
    <div className="ri-bar"><span>{label}</span>
      <div className="track" role="img" aria-label={`${label}: ${text}`}>{value != null && <i className={cls} style={{ width: `${Math.max(2, Math.min(100, (value / max) * 100))}%` }} />}</div>
      <b>{text}</b></div>
  );
}

export type IntelPart = "overview" | "skills" | "adaptive";

/** Does the learning plan exist? (the Overview tab pairs it with the topic chart) */
export const hasLearningPlan = (r: Report) => (r.intelligence?.learning_plan.length ?? 0) > 0;
/** Does the "Skills & progress" tab have anything in it? */
export const hasSkillsContent = (r: Report) => {
  const it = r.intelligence;
  return !!(r.skills?.some((k) => k.average != null) || (r.progress ?? []).some((p) => p.average_score != null) || (it && (it.classifications.some((c) => c.count > 0) || it.difficulty.some((d) => d.questions > 0)
    || (it.profiles?.length ?? 0) > 0 || (it.conceptual_vs_practical && (it.conceptual_vs_practical.conceptual != null || it.conceptual_vs_practical.practical != null)) || (it.evidence && (it.evidence.quotes > 0 || it.evidence.unverified_misconceptions > 0))
    || (it.consistency && (it.consistency.flags.length > 0 || it.consistency.adjustments.length > 0)))));
};

/** The resume claims card (how well each resume claim was defended). */
export function ResumeClaims({ r }: { r: Report }) {
  if (!r.resume_claims || r.resume_claims.length === 0) return null;
  return (
    <div className="card" data-testid="resume-claims">
      <div className="row between"><h2>Resume claims</h2><span className="muted small">How well you defended what your resume says · weakest first</span></div>
      <div className="rz-claims">
        {r.resume_claims.map((c) => (
          <div className="rz-claim" key={`${c.resume_id}-${c.section}-${c.label}`}>
            <div className="grow">
              <div className="rz-claim-t">{c.label || c.section}</div>
              <div className="muted small">{c.resume_name}{c.resume_deleted ? " (deleted resume)" : ""}{c.section ? ` › ${c.section}` : ""} · {c.question_numbers.map((n) => `Q${n}`).join(", ")}</div>
              <div className="small rz-tip"><Icon name="target" size={13} />{c.tip}</div>
            </div>
            <span className={`mark ${scoreClass(c.average_score)}`}>{c.average_score}</span>
            <span className={`badge ${CLAIM_VERDICT_TONE[c.verdict] ?? ""} rz-verdict`}>{c.verdict}</span>
          </div>
        ))}
      </div>
      <p className="muted small" style={{ margin: "8px 0 0" }}>Solid 7+ · Shaky 5–7 · Weak below 5. Skipped and unanswered questions are not counted.</p>
    </div>
  );
}

/** One tab's worth of the report beyond the scorecard: learning plan (Overview); difficulty, concept vs practice, progress, reliability, profiles (Skills & progress); timeline, resume coverage and claims (Adaptive). Each part renders only when the report has it. */
export default function ReportIntel({ r, part }: { r: Report; part: IntelPart }) {
  const it = r.intelligence, ad = r.adaptive, rc = r.resume_coverage;
  const prog = (r.progress ?? []).filter((p) => p.average_score != null);
  const cls = (it?.classifications ?? []).filter((c) => c.count > 0);
  const clsTotal = cls.reduce((n, c) => n + c.count, 0);
  const diff = (it?.difficulty ?? []).filter((d) => d.questions > 0);
  const cvp = it?.conceptual_vs_practical;
  const profiles = it?.profiles ?? [];
  const ev = it?.evidence, cons = it?.consistency;
  const hasCvp = !!cvp && (cvp.conceptual != null || cvp.practical != null);
  const end = endReasonLabel(ad?.end_reason ?? r.interview.end_reason);
  const skills = part === "skills", adaptive = part === "adaptive";
  return (
    <>
      {skills && (cls.length > 0 || diff.length > 0) && (
        <div className="ri-split" data-testid="ri-breakdown">
          {cls.length > 0 && (
            <section className="card" aria-labelledby="ri-cls">
              <h2 id="ri-cls" style={{ margin: 0 }}>Answer quality</h2><div className="muted small">How each graded answer was classified</div>
              <div style={{ marginTop: 8 }}>{cls.map((c) => <Bar key={c.key} label={classLabel(c.key)} value={c.count} max={Math.max(1, clsTotal)} cls={BAR_TONE[CLASS_TONE[c.key as Classification] ?? ""]} text={`${c.count}`} />)}</div>
            </section>
          )}
          {diff.length > 0 && (
            <section className="card" aria-labelledby="ri-diff">
              <h2 id="ri-diff" style={{ margin: 0 }}>Performance by difficulty</h2><div className="muted small">Average score of the questions at each level</div>
              <div style={{ marginTop: 8 }}>{diff.map((d) => <Bar key={d.difficulty} label={`${d.difficulty.charAt(0).toUpperCase()}${d.difficulty.slice(1)} (${d.questions})`} value={d.average_score} max={10} cls={tone(d.average_score)} text={d.average_score != null ? d.average_score.toFixed(1) : "—"} />)}</div>
            </section>
          )}
        </div>
      )}

      {skills && (hasCvp || profiles.length > 0) && (
        <div className="ri-split" data-testid="ri-skillsplit">
          {hasCvp && cvp && (
            <section className="card" aria-labelledby="ri-cvp">
              <h2 id="ri-cvp" style={{ margin: 0 }}>Conceptual vs practical</h2>
              <div style={{ marginTop: 8 }}>
                <Bar label="Conceptual" value={cvp.conceptual} max={10} cls={tone(cvp.conceptual)} text={cvp.conceptual != null ? cvp.conceptual.toFixed(1) : "—"} />
                <Bar label="Practical" value={cvp.practical} max={10} cls={tone(cvp.practical)} text={cvp.practical != null ? cvp.practical.toFixed(1) : "—"} />
              </div>
              {cvp.summary && <p className="muted small" style={{ margin: 0 }}>{cvp.summary}</p>}
            </section>
          )}
          {profiles.length > 0 && (
            <section className="card" aria-labelledby="ri-prof">
              <h2 id="ri-prof" style={{ margin: 0 }}>Evaluation profiles used</h2><div className="muted small">Each answer is graded with the profile that fits its topic</div>
              <div style={{ marginTop: 8 }}>{profiles.map((p) => <Bar key={p.key} label={`${p.label} (${p.answers})`} value={p.average_score} max={10} cls={tone(p.average_score)} text={p.average_score != null ? p.average_score.toFixed(1) : "—"} />)}</div>
            </section>
          )}
        </div>
      )}

      {skills && prog.length > 0 && (
        <section className="card" data-testid="ri-progress" aria-labelledby="ri-progress-h">
          <div className="row between"><h2 id="ri-progress-h" style={{ margin: 0 }}>Progress since your last attempt</h2><span className="muted small">per topic, against your latest earlier report</span></div>
          <div style={{ marginTop: 6 }}>
            {prog.map((p) => {
              const d = deltaInfo(p.delta);
              return (
                <div className="ri-prog" key={p.topic}>
                  <span><b>{p.topic}</b></span>
                  <span className="muted small">{p.previous != null ? <>{p.previous.toFixed(1)} → <b style={{ color: "var(--text)" }}>{p.average_score!.toFixed(1)}</b>{p.previous_interview_id ? <> · <a href={`#/report/${p.previous_interview_id}`}>earlier report</a></> : null}</> : <b style={{ color: "var(--text)" }}>{p.average_score!.toFixed(1)}</b>}</span>
                  {d ? <span className={`ri-delta ${d.tone}`} aria-label={`Change ${d.text}`}><span aria-hidden>{d.arrow}</span>{d.text}</span> : <span className="muted small">first time</span>}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {part === "overview" && it && it.learning_plan.length > 0 && (
        <section className="card" data-testid="ri-plan" aria-labelledby="ri-plan-h">
          <h2 id="ri-plan-h" style={{ margin: 0 }}>Learning plan</h2><div className="muted small">Your lowest-scoring skills first, with one thing to practise</div>
          <ol className="ri-plan">
            {it.learning_plan.map((l) => (
              <li key={l.skill}><b className={`mark ${scoreClass(l.average)}`}>{l.average != null ? l.average.toFixed(1) : "—"}</b><div><b>{l.skill}</b><div className="small">{l.action}</div></div></li>
            ))}
          </ol>
        </section>
      )}

      {skills && ((ev && (ev.quotes > 0 || ev.unverified_misconceptions > 0)) || (cons && (cons.flags.length > 0 || cons.adjustments.length > 0))) && (
        <section className="card" data-testid="ri-trust" aria-labelledby="ri-trust-h">
          <h2 id="ri-trust-h" style={{ margin: 0 }}>How reliable the grading was</h2>
          <ul className="tight small" style={{ marginBottom: 0 }}>
            {ev && ev.quotes > 0 && <li>{ev.verified} of {ev.quotes} evidence quote{ev.quotes === 1 ? "" : "s"} were found in your answers.</li>}
            {ev && ev.unverified_misconceptions > 0 && <li>{ev.unverified_misconceptions} possible error{ev.unverified_misconceptions === 1 ? "" : "s"} could not be found in your answers, so {ev.unverified_misconceptions === 1 ? "it was" : "they were"} not counted.</li>}
            {cons?.flags.map((f, i) => <li key={`f${i}`}>{f.message}</li>)}
            {cons?.adjustments.map((a, i) => <li key={`a${i}`}>Score adjustment: {a}</li>)}
          </ul>
        </section>
      )}

      {adaptive && ad && (
        <section className="card" data-testid="ri-adaptive" aria-labelledby="ri-ad-h">
          <div className="row between"><h2 id="ri-ad-h" style={{ margin: 0 }}>How the interview adapted</h2>
            <span className="muted small">{strategyLabel(ad.strategy)} · started {levelLabel(ad.start_level)} · finished {levelLabel(ad.final_level)}</span></div>
          {end && <p className="muted small" style={{ margin: "6px 0 0" }}>{end}{ad.pool_unused > 0 ? ` · ${ad.pool_unused} question${ad.pool_unused === 1 ? "" : "s"} left unused` : ""}.</p>}
          <ol className="ri-timeline" aria-label="Decisions in order">
            {timelineRows(ad.events).map((e, i) => {
              const moved = levelChanged(e);
              const dir = moved ? (["beginner", "intermediate", "advanced", "expert"].indexOf(e.level_after!) > ["beginner", "intermediate", "advanced", "expert"].indexOf(e.level_before!) ? "up" : "down") : "";
              return (
                <li key={i} className={dir}>
                  <div className="ri-tl-h">
                    <b>{e.question != null ? `Q${e.question}` : "Follow-up"}{e.topic ? ` · ${e.topic}` : ""}</b>
                    <span className="badge">{decisionLabel(e.decision)}</span>
                    {moved && <span className="badge accent"><Icon name="trend" size={12} />{levelLabel(e.level_before)} → {levelLabel(e.level_after)}</span>}
                  </div>
                  {e.reason && e.reason !== e.decision && <div className="small muted">{e.reason}</div>}
                </li>
              );
            })}
          </ol>
          {ad.level_history.length > 0 && (
            <details style={{ marginTop: 12 }}><summary className="small muted" style={{ cursor: "pointer" }}>Level changes ({ad.level_history.length})</summary>
              <ul className="tight small">{ad.level_history.map((l, i) => <li key={i}><b>After Q{l.after_question}: {levelLabel(l.from)} → {levelLabel(l.to)}.</b> {l.reason}</li>)}</ul></details>
          )}
        </section>
      )}

      {adaptive && rc && rc.claims_total > 0 && (
        <section className="card" data-testid="ri-coverage" aria-labelledby="ri-cov-h">
          <div className="row between"><h2 id="ri-cov-h" style={{ margin: 0 }}>Resume coverage</h2><span className="muted small">{rc.questions} resume question{rc.questions === 1 ? "" : "s"} asked</span></div>
          <p style={{ margin: "8px 0 0" }}><b>{rc.claims_discussed} of {rc.claims_total}</b> experiences and projects from your resume came up.</p>
          <div className="ri-meter" role="img" aria-label={`${rc.claims_discussed} of ${rc.claims_total} discussed`}><i style={{ width: `${(rc.claims_discussed / rc.claims_total) * 100}%` }} /></div>
          {rc.unexplored.length > 0 && <><div className="small muted">Not discussed yet, worth practising next:</div>
            <ul className="ri-unex">{rc.unexplored.map((u) => <li key={`${u.section}-${u.label}`}>{u.label}<span className="muted"> · {u.section}</span></li>)}</ul></>}
        </section>
      )}
      {adaptive && <ResumeClaims r={r} />}
    </>
  );
}
