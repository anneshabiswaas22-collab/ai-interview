import { useEffect, useState } from "react";
import { ApiError, resumesApi } from "../api";
import { CONFIDENCE_TONE, SOURCE_TONE, groupSkills, monthsLabel, sourceLabel, sourceRef, yearsLabel } from "../intel";
import type { CandidateIntel, CandidateSkill } from "../types";
import Icon from "./Icon";
import { CardsSkeleton } from "./Loaders";
import { fmtShort, scoreClass } from "./ui";

function SkillItem({ s }: { s: CandidateSkill }) {
  return (
    <li className="cp-skill">
      <div className="cp-skill-h"><b>{s.name}</b>{s.category && <span className="badge">{s.category}</span>}
        <span className={`badge ${CONFIDENCE_TONE[s.confidence] ?? ""}`}>{s.confidence} confidence</span>{s.listed && <span className="muted small">listed</span>}
        {s.aliases.length > 0 && <span className="muted small">also: {s.aliases.join(", ")}</span>}</div>
      {s.confidence_reason && <div className="small muted">{s.confidence_reason}</div>}
      {s.used_in.length > 0 && <div className="small">Used in: {s.used_in.join("; ")}</div>}
      {s.sources.length > 0 && <div className="cp-src" aria-label={`Where ${s.name} appears`}>{s.sources.map((x, i) => <span key={i} className={`src-${SOURCE_TONE[x.status] || "none"}`}>{sourceRef(x)} · {sourceLabel(x.status)}</span>)}</div>}
    </li>
  );
}

/** Skills in three groups; the first non-empty group (normally "High confidence") starts open, the others folded. */
function SkillGroups({ skills }: { skills: CandidateSkill[] }) {
  const groups = groupSkills(skills);
  const [open, setOpen] = useState<Record<string, boolean>>(() => ({ [groups[0]?.key ?? "high"]: true }));
  return (
    <div className="cp-groups">
      {groups.map((g) => {
        const on = !!open[g.key];
        return (
          <div className="cp-group" key={g.key} data-testid={`cp-group-${g.key}`}>
            <h3 className="cp-group-h"><button type="button" aria-expanded={on} aria-controls={`cp-g-${g.key}`} onClick={() => setOpen((o) => ({ ...o, [g.key]: !on }))}>
              <Icon name="chevl" className="cp-chev" /><span>{g.label}</span><span className="cp-count">{g.skills.length}</span></button></h3>
            <ul className="cp-skills" id={`cp-g-${g.key}`} hidden={!on}>{g.skills.map((s) => <SkillItem key={s.name} s={s} />)}</ul>
          </div>
        );
      })}
    </div>
  );
}

/** Resume detail → Candidate profile: what the interviewer knows about you, built offline from your saved profile. `version` changes when the profile is saved, which refetches. */
export default function CandidateProfile({ id, version, onEdit }: { id: number; version: string | number; onEdit: () => void }) {
  const [d, setD] = useState<CandidateIntel | null>(null);
  const [err, setErr] = useState<{ code: string; message: string } | null>(null);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let alive = true;
    setErr(null);
    resumesApi.intelligence(id).then((x) => { if (alive) setD(x); }, (e: ApiError) => { if (alive) { setD(null); setErr({ code: e.code, message: e.message }); } });
    return () => { alive = false; };
  }, [id, version, tick]);

  if (err?.code === "resume_not_ready") return <div className="notice info" role="status"><b>Not ready yet.</b> {err.message}</div>;
  if (err) return <div className="notice error" role="alert">{err.message} <button className="linkbtn" onClick={() => setTick((t) => t + 1)}>Try again</button></div>;
  if (!d) return <CardsSkeleton n={2} label="Building the candidate profile…" />;

  const ex = d.extraction;
  const pct = ex.checked ? Math.round(((ex.verified + ex.partial * 0.5) / ex.checked) * 100) : null;
  return (
    <div className="cp" data-testid="candidate-profile">
      <p className="muted small" style={{ margin: 0 }}>Built on this computer from your saved resume content: no AI call, nothing is sent anywhere. {d.notes.join(" ")}</p>

      {d.injection_warnings.length > 0 && (
        <div className="notice warn" role="status" data-testid="cp-injection">
          <b>Instructions found inside the resume.</b> Text that looks like instructions to an AI was found. It is treated as plain text and never followed.
          <ul className="tight small">{d.injection_warnings.map((w) => <li key={w.line}>Line {w.line}: “{w.text}”</li>)}</ul>
        </div>
      )}

      <section className="card" aria-labelledby="cp-ex">
        <div className="row between"><h2 id="cp-ex" style={{ margin: 0 }}>Extraction quality</h2><span className={`badge ${CONFIDENCE_TONE[ex.confidence] ?? ""}`}>{ex.confidence} confidence</span></div>
        <p style={{ margin: "8px 0 0" }}>{ex.checked ? <><b>{ex.verified} of {ex.checked}</b> checked items were found word for word in the PDF text{ex.partial ? `, ${ex.partial} partly` : ""}{ex.not_found ? `, ${ex.not_found} not found` : ""}.</> : "Nothing could be checked against the PDF text."}</p>
        {pct != null && <div className="ri-meter" role="img" aria-label={`${pct}% matched`}><i style={{ width: `${pct}%` }} /></div>}
        {ex.not_found_examples.length > 0 && (
          <div className="small"><div className="muted">Examples that were not found in the text:</div><ul className="tight">{ex.not_found_examples.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
        )}
        {(ex.not_found > 0 || ex.partial > 0) && <p className="small muted" style={{ margin: 0 }}>If something looks wrong, correct it in the <button className="linkbtn" onClick={onEdit}>Content tab</button>; this view updates when you save.</p>}
      </section>

      <section className="card" aria-labelledby="cp-sk">
        <div className="row between"><h2 id="cp-sk" style={{ margin: 0 }}>Skills</h2><span className="muted small">{d.skills.length} found · confidence shows how well your resume backs each one up</span></div>
        {d.skills.length === 0 ? <p className="muted">No skills were found.</p> : (
          <SkillGroups skills={d.skills} />
        )}
      </section>

      <div className="cp-grid">
        <section className="card" aria-labelledby="cp-exp">
          <h2 id="cp-exp" style={{ margin: 0 }}>Experience</h2>
          <p style={{ margin: "8px 0 0" }}><b>{d.experience.roles}</b> role{d.experience.roles === 1 ? "" : "s"}{d.experience.years != null ? <> · about <b>{yearsLabel(d.experience.years)}</b></> : ""}</p>
          {(d.experience.current ?? []).length > 0 && <p className="small" style={{ margin: "4px 0 0" }}>Current: {d.experience.current.join("; ")}</p>}
          {d.experience.gaps.length > 0 && <p className="small muted" style={{ margin: "4px 0 0" }}>Time between roles: {d.experience.gaps.map((g) => `${g.from} → ${g.to} (${monthsLabel(g.months)})`).join("; ")}. Interviewers sometimes ask about this.</p>}
        </section>
        <section className="card" aria-labelledby="cp-pr">
          <h2 id="cp-pr" style={{ margin: 0 }}>Projects</h2>
          {d.projects.length === 0 ? <p className="muted">No projects found.</p> : d.projects.map((p) => (
            <div className="cp-proj" key={p.name} style={{ marginTop: 10 }}>
              <b>{p.name}</b>{p.source && <span className={`badge ${SOURCE_TONE[p.source.status] ?? ""}`} style={{ marginLeft: 8 }}>{sourceLabel(p.source.status)}</span>}
              <div className="small muted">{p.tech.length ? p.tech.join(", ") : "No technologies listed"} · {p.bullets} point{p.bullets === 1 ? "" : "s"}{p.has_metrics ? " · has numbers" : ""}</div>
            </div>
          ))}
        </section>
      </div>

      {d.relationships.length > 0 && (
        <section className="card" aria-labelledby="cp-rel">
          <h2 id="cp-rel" style={{ margin: 0 }}>Technologies used together</h2><div className="muted small">Pairs that appear in the same role or project</div>
          <div className="cp-rel">{d.relationships.map((r) => <span key={`${r.a}-${r.b}`} title={r.contexts.join("; ")}>{r.a}<i>+</i>{r.b}</span>)}</div>
        </section>
      )}

      {d.clarifications.length > 0 && (
        <section className="card" aria-labelledby="cp-clar" data-testid="cp-clar">
          <h2 id="cp-clar" style={{ margin: 0 }}>Worth preparing</h2><div className="muted small">Places where an interviewer may ask you to add detail. These are prompts to prepare, not problems with your resume.</div>
          <ul className="cp-clar">{d.clarifications.map((c, i) => (
            <li key={i}><div><b>{c.label}</b><span className="muted small"> · {c.section}</span></div><div className="small">{c.why}</div>{c.suggested_question && <div className="sq">You might be asked: {c.suggested_question}</div>}</li>
          ))}</ul>
        </section>
      )}

      {d.suggested_questions.length > 0 && (
        <section className="card" aria-labelledby="cp-sq" data-testid="cp-questions">
          <div className="row between"><h2 id="cp-sq" style={{ margin: 0 }}>Questions built from your resume</h2><span className="muted small">Each one is tied to a line you wrote</span></div>
          {d.suggested_questions.map((q, i) => (
            <details className="cp-q" key={i}>
              <summary>{q.text}</summary>
              <div className="small muted" style={{ marginTop: 6 }}>{q.topic ?? "General"} · {q.difficulty ?? "mixed"} · from {q.claim.section}{q.claim.label ? ` › ${q.claim.label}` : ""}</div>
              <blockquote>{q.claim.excerpt}</blockquote>
            </details>
          ))}
          <p className="small muted" style={{ marginBottom: 0 }}>Practice them: choose “Add questions from my resume automatically” when you start an interview.</p>
        </section>
      )}

      <div className="cp-grid">
        <section className="card" aria-labelledby="cp-hist">
          <h2 id="cp-hist" style={{ margin: 0 }}>Practice history</h2>
          {d.practice_history.length === 0 ? <p className="muted small">You have not practised with this resume yet.</p> : (
            <ul className="tight cp-hist" style={{ listStyle: "none", padding: 0 }}>{d.practice_history.map((h) => {
              const last = h.attempts[h.attempts.length - 1];
              return <li key={h.label}><b>{h.label}</b><span className="muted small">{h.attempts.length} attempt{h.attempts.length === 1 ? "" : "s"} · last {fmtShort(last.date)}</span>
                {last.average_score != null && <b className={`mark sm ${scoreClass(last.average_score)}`}>{last.average_score}</b>}{last.verdict && <span className="badge">{last.verdict}</span>}
                <a href={`#/report/${last.interview_id}`} className="small">report</a></li>;
            })}</ul>
          )}
        </section>
        <section className="card" aria-labelledby="cp-un">
          <h2 id="cp-un" style={{ margin: 0 }}>Not practised yet</h2>
          {d.unexplored.length === 0 ? <p className="muted small">Every experience and project has come up in an interview.</p> : <ul className="ri-unex">{d.unexplored.map((u) => <li key={`${u.section}-${u.label}`}>{u.label}<span className="muted"> · {u.section}</span></li>)}</ul>}
        </section>
      </div>
      <div className="small muted"><Icon name="shield" size={13} /> This view is computed fresh each time and is not stored separately.</div>
    </div>
  );
}
