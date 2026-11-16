import { useEffect, useMemo, useRef, useState } from "react";
import { api, resumesApi } from "../api";
import { speaker } from "../audio";
import Icon, { Stop, type IconName } from "../components/Icon";
import ActiveInterviews, { isActive } from "../components/ActiveInterviews";
import { ErrorNotice, OptionCards, Section, Seg, Switch, topicClass, useAsync, useToast } from "../components/ui";
import type { DraftQuestion, GenSettings, InterviewConfig, MixOrder, Question } from "../types";
import ResumeQuestionsPanel from "../components/ResumeQuestionsPanel";
import { takeIntent } from "../intent";
import { DEFAULT_FOCUS, MIX_LABEL, interviewMinutes, mixSequence, sessionCounts, toInput, validQuestion, type Source } from "../resumeHelpers";
import type { SystemVoice } from "../systemVoices";
import { estimateInterviewCost, fmtUsd } from "../aiHelpers";
import { describeTopics } from "../practice";
import { LEVELS, LEVEL_LABEL, STRATEGIES, levelLabel, minutesLabel, resumeStrategyAvailable, strategyLabel } from "../intel";
import { openSettings } from "../settingsTab";
import { PRESET_IDS, PRESET_INFO, activePreset, presetDisabledReason, presetPlan, type PresetId } from "../presets";
import { shortVoiceName, useSpeaker, useSystemVoices } from "./useSpeaker";

const KEY = "lai.setup";
const DEFAULTS: InterviewConfig = {
  title: "Practice Interview - 1", interview_type: "technical", question_ids: null, order: "supplied", max_followups: 2,
  voice: "default", speech_speed: 1, strictness: "balanced", feedback_mode: "at_end", question_audio: "auto", mic_enabled: false,
  mode: "fixed", strategy: "progressive", start_level: "intermediate", max_questions: 10, time_limit_minutes: null, focus_topic: null,
};
const STRATEGY_ICON: Record<string, IconName> = { progressive: "trend", deep_dive: "target", practical: "briefcase", conceptual: "layers", mixed: "shuffle", resume: "file" };
const load = (): InterviewConfig => { try { const { title: _t, feedback_mode: _f, include_bank: _b, mix: _m, ...saved } = JSON.parse(localStorage.getItem(KEY) || "{}"); return { ...DEFAULTS, ...saved, question_ids: null, focus_topic: null }; } catch { return DEFAULTS; } };
// the resume part of the setup (settings + reviewed questions) survives a page refresh within this tab
const DRAFT_KEY = "lai.setup.resume";
interface ResumeDraft { auto: { on: boolean; count: number; id: number | null }; source: Source; gen: GenSettings; questions: DraftQuestion[]; mix: MixOrder; saveToBank: boolean }
const loadDraft = (): Partial<ResumeDraft> => { try { return JSON.parse(sessionStorage.getItem(DRAFT_KEY) || "{}"); } catch { return {}; } };
const SOURCE_LABEL: Record<Source, string> = { bank: "Question bank", resume: "Resume", both: "Both" };   // the title is never remembered: each interview gets its own
const takePreselect = (): { setId: number; ids: number[]; label?: string; skipped?: { topic: string; untagged: boolean }[] } | null => { try { const v = localStorage.getItem("lai.preselect"); localStorage.removeItem("lai.preselect"); return v ? JSON.parse(v) : null; } catch { return null; } };
/** Topics of the bank questions that will be used (none when the bank is not used). */
const useBankTopics = (source: Source, mode: "all" | "selected", all: Question[], chosen: Question[]) => (source === "resume" ? [] : (mode === "all" ? all : chosen).map((q) => q.topic ?? ""));
const TYPES = { technical: "Technical", hr: "HR", scenario: "Scenario-based", mixed: "Mixed" } as const;
const STRICT_DESC = { lenient: "Credits partial understanding", balanced: "Fair, like a real interviewer", strict: "Expects precision and depth" } as const;

/** Short names; when two voices share one (macOS has en-US and en-GB "Eddy"), the region is added: "Eddy · UK". */
function labelVoices(voices: SystemVoice[]) {
  const short = voices.map((v) => shortVoiceName(v.name));
  return voices.map((v, i) => {
    const clash = short.filter((s) => s === short[i]).length > 1;
    const region = v.lang.split(/[-_]/)[1]?.toUpperCase() ?? v.lang;
    return { id: v.id, label: clash ? `${short[i]} · ${region}` : short[i], full: `${v.name} (${v.lang})` };
  });
}

export default function Setup() {
  const toast = useToast();
  const sets = useAsync(() => api.sets(), []);
  const voices = useAsync(() => api.voices(), []);
  const health = useAsync(() => api.health(), []);
  const ai = useAsync(() => api.ai(), []);
  const hist = useAsync(() => api.interviews(), []);
  const active = (hist.data ?? []).filter(isActive);
  const [pre] = useState(takePreselect);
  const [resumeIntent] = useState(() => takeIntent(["resume-practice"]));
  const [draft0] = useState(loadDraft);
  const resumes = useAsync(() => resumesApi.list(), []);
  const ready = (resumes.data ?? []).filter((r) => r.status === "ready");
  const [source, setSource] = useState<Source>(resumeIntent ? "resume" : pre ? "bank" : draft0.source ?? "bank");
  const [gen, setGen] = useState<GenSettings>(() => ({ resume_ids: [], count: 8, focus: DEFAULT_FOCUS, depth: "standard", difficulty: "mixed", style: "manager", ...draft0.gen,
    ...(resumeIntent ? { resume_ids: resumeIntent.resumeIds } : {}) }));
  const [rqs, setRqs] = useState<DraftQuestion[]>(resumeIntent ? [] : draft0.questions ?? []);
  const [mix, setMix] = useState<MixOrder>(draft0.mix ?? "interleave");
  const [saveToBank, setSaveToBank] = useState(!!draft0.saveToBank);
  const [auto, setAuto] = useState<{ on: boolean; count: number; id: number | null }>({ on: false, count: 5, id: null, ...draft0.auto });
  useEffect(() => { try { sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ source, gen, questions: rqs, mix, saveToBank, auto })); } catch { /* ignore */ } }, [source, gen, rqs, mix, saveToBank, auto]);
  useEffect(() => {      // drop resumes that are gone or not ready; with one ready resume and nothing chosen, choose it
    if (!resumes.data) return;
    const ok = gen.resume_ids.filter((id) => ready.some((r) => r.id === id));
    if (ok.length !== gen.resume_ids.length || (!ok.length && ready.length === 1)) setGen((g) => ({ ...g, resume_ids: ok.length ? ok : ready.length === 1 ? [ready[0].id] : [] }));
    if (!ready.length && source !== "bank") setSource("bank");
    setAuto((a) => (a.on && !ready.length ? { ...a, on: false } : a.id != null && !ready.some((r) => r.id === a.id) ? { ...a, id: null } : a));
  }, [resumes.data]); // eslint-disable-line react-hooks/exhaustive-deps
  const [setId, setSetId] = useState<number | null>(pre?.setId ?? null);
  const [cfg, setCfg] = useState<InterviewConfig>(load);
  const [selected, setSelected] = useState<Set<number>>(new Set(pre?.ids ?? []));
  const [mode, setMode] = useState<"all" | "selected">(pre ? "selected" : "all");
  const [showPre, setShowPre] = useState(true);
  const [qsearch, setQsearch] = useState("");
  const [vsearch, setVsearch] = useState("");
  const [voiceOpen, setVoiceOpen] = useState(false);       // the searchable voice list is folded away until "Change voice"
  const [presetNote, setPresetNote] = useState<string | null>(null);
  const changeVoiceBtn = useRef<HTMLButtonElement>(null);
  const [busy, setBusy] = useState(false);
  const speech = useSpeaker();
  const isSystem = voices.data?.engine === "system";            // no Phonon here: use this computer's offline voices
  const sysVoices = useSystemVoices(isSystem);
  const vgrid = useRef<HTMLDivElement>(null);
  const qs = useAsync(() => (setId ? api.questions(setId) : Promise.resolve([] as Question[])), [setId]);
  const questions = useMemo(() => qs.data ?? [], [qs.data]);

  useEffect(() => { if (sets.data && setId == null) setSetId(sets.data[0]?.id ?? null); }, [sets.data, setId]);
  useEffect(() => { if (!pre) setSelected(new Set(questions.map((q) => q.id))); }, [qs.data]); // eslint-disable-line react-hooks/exhaustive-deps
  const voiceItems = useMemo<{ id: string; label: string; full: string }[]>(() => isSystem
    ? [{ id: "default", label: "System default", full: "System default voice" }, ...labelVoices(sysVoices ?? [])]
    : (voices.data?.voices ?? []).map((v) => ({ id: v, label: v, full: v })), [isSystem, sysVoices, voices.data]);
  useEffect(() => {
    if (!voices.data || (isSystem && sysVoices === null)) return;      // wait until the voice list is known
    let saved = false; try { saved = !!localStorage.getItem(KEY); } catch { /* ignore */ }
    const ids = voiceItems.map((v) => v.id);
    if (!ids.includes(cfg.voice)) setCfg((c) => ({ ...c, voice: voices.data!.default }));
    else if (!saved && !isSystem && cfg.voice === "default" && ids.includes("Hadley")) setCfg((c) => ({ ...c, voice: "Hadley" }));   // storyboard default voice
  }, [voices.data, sysVoices]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {   // bring the chosen voice into view inside the scrollable grid
    const g = vgrid.current; const el = g?.querySelector<HTMLElement>("[aria-checked=true]");
    if (g && el && !vsearch) g.scrollTop = Math.max(0, el.offsetTop - g.offsetTop - 8);
  }, [voices.data, sysVoices, voiceOpen]); // eslint-disable-line react-hooks/exhaustive-deps
  const titleTouched = useRef(false);
  const set = <K extends keyof InterviewConfig>(k: K, v: InterviewConfig[K]) => { if (k === "title") titleTouched.current = true; setCfg((c) => ({ ...c, [k]: v })); };
  useEffect(() => { const n = hist.data?.length; if (n !== undefined && !titleTouched.current) setCfg((c) => ({ ...c, title: `Practice Interview - ${n + 1}` })); }, [hist.data]);

  const chosen = useMemo(() => questions.filter((q) => selected.has(q.id)), [questions, selected]);
  const bankCount = mode === "all" ? questions.length : chosen.length;
  const goodRqs = rqs.filter(validQuestion);
  const counts = sessionCounts(source, bankCount, goodRqs.length);
  const adaptive = cfg.mode === "adaptive";
  const autoId = auto.id ?? ready[0]?.id ?? null;
  const autoOn = auto.on && autoId != null;
  const autoCount = autoOn ? auto.count : 0;
  const poolCount = counts.total + autoCount;                                     // every question the session can draw on
  const count = adaptive ? Math.min(poolCount, cfg.max_questions ?? 10) : poolCount;      // how many will actually be asked
  const resumeOk = resumeStrategyAvailable(goodRqs.length * (source === "bank" ? 0 : 1), autoOn, autoCount);
  const strategyBlocked = adaptive && cfg.strategy === "resume" && !resumeOk;
  const topicList = [...new Set([...useBankTopics(source, mode, questions, chosen), ...(source === "bank" ? [] : goodRqs.map((q) => q.topic ?? ""))].filter(Boolean))].sort();
  const cloud = health.data?.ai.mode === "cloud";
  const llmReady = cloud ? !!health.data?.ai.ready : !!health.data?.ollama.ok && !!health.data.llm.installed;
  const budgetToday = health.data?.ai.budget?.today;
  const estCost = cloud && ai.data ? estimateInterviewCost(ai.data.config, count, cfg.max_followups) : undefined;
  const estMin = interviewMinutes(count, cfg.max_followups);
  const estShown = cfg.time_limit_minutes ? Math.min(estMin, cfg.time_limit_minutes) : estMin;
  const voiceList = (voices.data ? voiceItems : [{ id: cfg.voice, label: cfg.voice, full: cfg.voice }]).filter((v) => v.full.toLowerCase().includes(vsearch.trim().toLowerCase()));
  const voiceLabel = voiceItems.find((v) => v.id === cfg.voice)?.label ?? cfg.voice;
  const voiceFull = voiceItems.find((v) => v.id === cfg.voice)?.full ?? cfg.voice;
  const chooseVoice = (id: string) => { set("voice", id); closeVoices(); };
  function closeVoices() { setVoiceOpen(false); setVsearch(""); requestAnimationFrame(() => changeVoiceBtn.current?.focus()); }

  // presets: one click fills the settings below; the card stays marked only while the form still matches it
  const bankIds = useMemo(() => [...questions].sort((a, b) => a.position - b.position).map((q) => q.id), [questions]);
  const presetCtx = { bankIds, resumeId: ready.length ? autoId : null };
  const activeId = activePreset({ cfg, source, selectMode: mode, selectedIds: [...selected], autoOn }, presetCtx);
  const applyPreset = (id: PresetId) => {
    const plan = presetPlan(id, presetCtx);
    if (!plan) return;
    setCfg((c) => ({ ...c, ...plan.cfg }));
    if (plan.source) setSource(plan.source);
    if (plan.selectMode) setMode(plan.selectMode);
    if (plan.selectedIds) setSelected(new Set(plan.selectedIds)); else if (plan.selectMode === "all") setSelected(new Set(questions.map((q) => q.id)));
    if (plan.auto) setAuto((a) => ({ ...a, on: plan.auto!.on, id: plan.auto!.id ?? a.id }));
    setShowPre(false);
    setPresetNote(`${PRESET_INFO[id].title} applied.${plan.note ? ` ${plan.note}` : ""} Fine-tune anything below.`);
  };
  const shownQs = questions.filter((q) => `${q.text} ${q.topic ?? ""}`.toLowerCase().includes(qsearch.trim().toLowerCase()));

  const previewVoice = (v: string) => {
    if (speech.key === `vp-${v}` && speech.status !== "idle") { speaker.stop(); return; }
    speaker.setRate(cfg.speech_speed);
    void speaker.play(`vp-${v}`, "Hello! I'll be your interviewer today. Let's begin with the first question.", v);
  };

  const useBank = source !== "resume";
  const canStart = !busy && count > 0 && active.length === 0 && (!useBank || !!setId) && (source === "bank" || goodRqs.length > 0 || autoOn) && !strategyBlocked;
  const start = async () => {
    if (!canStart) return;
    setBusy(true);
    try {
      try { localStorage.setItem(KEY, JSON.stringify({ ...cfg, title: undefined })); localStorage.setItem("lai.voice", cfg.voice); } catch { /* ignore */ }
      const resumeQs = source === "bank" ? [] : goodRqs.map(toInput);
      if (resumeQs.length && saveToBank) {
        try { const r = await resumesApi.saveToBank(resumeQs); if (r.added) toast("ok", `Saved ${r.added} question${r.added === 1 ? "" : "s"} to “${r.sets[0]?.name}”`); }
        catch (e) { toast("error", `Could not save to the question bank: ${(e as Error).message}`); }
      }
      const { strategy, start_level, max_questions, focus_topic, ...rest } = cfg;       // a fixed interview sends none of the adaptive settings
      const modeCfg = { mode: cfg.mode ?? "fixed", time_limit_minutes: cfg.time_limit_minutes ?? null,
        ...(adaptive ? { strategy, start_level, max_questions, focus_topic: strategy === "deep_dive" ? focus_topic || null : null } : {}) };
      const st = await api.createInterview(useBank ? setId : null, { ...rest, ...modeCfg, question_ids: mode === "all" ? null : chosen.map((q) => q.id), include_bank: useBank,
        mix: source === "both" || (autoOn && useBank) ? mix : "bank_first" }, resumeQs, autoOn ? { resume_id: autoId!, count: auto.count } : null);
      try { sessionStorage.removeItem(DRAFT_KEY); } catch { /* ignore */ }
      window.location.hash = `#/interview/${st.id}`;
    } catch (e) { toast("error", (e as Error).message); setBusy(false); hist.reload(); }
  };

  const summary: [string, string, string][] = [
    ["briefcase", "Type", TYPES[cfg.interview_type]],
    ["route", "Mode", adaptive ? `Adaptive · ${strategyLabel(cfg.strategy)}` : "Fixed order"],
    ...(adaptive ? [["trend", "Starting level", levelLabel(cfg.start_level)] as [string, string, string]] : []),
    ...(adaptive && cfg.strategy === "deep_dive" ? [["target", "Focus", cfg.focus_topic || "Largest topic"] as [string, string, string]] : []),
    ["list", "Questions", adaptive ? `Up to ${count}${poolCount > count ? ` of ${poolCount}` : ""}` : source === "bank" && !autoOn ? `${count} · ${cfg.order === "shuffled" ? "Shuffled" : "In order"}` : `${count} in total`],
    ...(source !== "bank" || autoOn ? [["doc", "From question bank", source === "resume" ? "—" : String(counts.bank)] as [string, string, string], ["file", "From resume", String(counts.resume + autoCount)] as [string, string, string]] : []),
    ["clock", "Time limit", minutesLabel(cfg.time_limit_minutes)],
    ...(!adaptive && (source === "both" || (autoOn && useBank)) ? [["shuffle", "Order", MIX_LABEL[mix]] as [string, string, string]] : []),
    ["msg", "Follow-ups", cfg.max_followups === 0 ? "None" : `Up to ${cfg.max_followups} each`],
    ["voice", "Voice", `${voiceLabel} · ${cfg.speech_speed}×`],
    ["target", "Strictness", cfg.strictness.charAt(0).toUpperCase() + cfg.strictness.slice(1)],
    ["cpu", "AI engine", cloud ? `Ollama Cloud` : "This computer"],
    ["eye", "Scores", "In the final report"],
  ];

  return (
    <div>
      <div className="pagehead">
        <div><h1>Start New Interview</h1><div className="muted">Configure your interview session</div></div>
      </div>
      <ActiveInterviews rows={active} onChanged={hist.reload} />
      {health.data && !llmReady && (
        <div className="notice error"><b>{cloud ? "Ollama cloud isn’t ready." : "The interview model isn’t ready."}</b> {cloud ? "Add your API key in Settings → AI models." : (health.data.ollama.error ?? health.data.llm.error)} You can still start, but answers can’t be evaluated until this is fixed.{" "}
          <button className="linkbtn" onClick={() => openSettings("ai")}>{cloud ? "Open AI settings" : "Use Ollama cloud instead"}</button></div>
      )}
      <ErrorNotice error={sets.error || qs.error} />
      {pre && showPre && (
        <div className="notice info row between" role="status">
          <span><b>Practicing {pre.label ?? "your selection"}</b> — {pre.ids.length} question{pre.ids.length === 1 ? "" : "s"} preselected in step 3 below.
            {pre.skipped && pre.skipped.length > 0 && <span className="muted"> Left out because you have no questions for {describeTopics(pre.skipped)} yet.</span>}</span>
          <button className="btn" onClick={() => { setMode("all"); setSelected(new Set(questions.map((q) => q.id))); setShowPre(false); }}>Use all questions instead</button>
        </div>
      )}

      <div className="setup-grid">
        <div className="setup-wrap"><div className="setup-main">
        <section className="setup-presets" aria-labelledby="presets-h" data-testid="presets">
          <div className="presets-h"><h2 id="presets-h">Start from a preset</h2><span className="muted small">Fills in the settings below. You can still change anything.</span></div>
          <OptionCards label="Interview preset" value={(activeId ?? "") as PresetId | ""} onChange={(v) => { if (v) applyPreset(v); }}
            options={PRESET_IDS.map((id) => {
              const why = presetDisabledReason(id, presetCtx, (resumes.data?.length ?? 0) > 0);
              return { value: id, title: PRESET_INFO[id].title, desc: why ?? PRESET_INFO[id].desc, icon: PRESET_INFO[id].icon, disabled: !!why || (id !== "resume" && qs.loading) };
            })} />
          {activeId && presetNote && <p className="hint presets-note" role="status">{presetNote}</p>}
        </section>
          <div className="setup-col">
          <Section step={1} icon="sparkle" title="Basics" desc="Name your session and choose the kind of interview">
            <div className="fld"><div className="lbl"><label htmlFor="title">Interview title</label></div>
              <input id="title" type="text" value={cfg.title} maxLength={120} onChange={(e) => set("title", e.target.value)} /></div>
            <div className="fld"><div className="lbl">Interview type<small>Shapes how answers are judged</small></div>
              <OptionCards label="Interview type" value={cfg.interview_type} onChange={(v) => set("interview_type", v)} options={[
                { value: "technical", title: "Technical", desc: "Concepts, coding, design, tools", icon: "briefcase" },
                { value: "hr", title: "HR", desc: "Behaviour, motivation, teamwork", icon: "users" },
                { value: "scenario", title: "Scenario-based", desc: "Investigate and design under pressure", icon: "route" },
                { value: "mixed", title: "Mixed", desc: "Judged per question automatically", icon: "layers" },
              ]} /></div>
          </Section>

          </div>
          <div className="setup-col">
          <Section step={2} icon="route" title="Interview mode" desc="A fixed list in order, or an interviewer that adapts to your answers">
            <div className="fld"><div className="lbl">Mode</div>
              <OptionCards label="Interview mode" cols={2} value={cfg.mode ?? "fixed"} onChange={(v) => set("mode", v)} options={[
                { value: "fixed", title: "Fixed order", desc: "Every chosen question, in the order you set. Nothing changes along the way.", icon: "list" },
                { value: "adaptive", title: "Adaptive", desc: "Picks each next question from your answers: harder when you do well, easier when you struggle.", icon: "trend" },
              ]} /></div>
            {adaptive && <>
              <div className="fld"><div className="lbl">Strategy<small>how the next question is chosen</small></div>
                <div className="ocards" data-cols="3" role="radiogroup" aria-label="Adaptive strategy" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))" }}>
                  {STRATEGIES.map((o) => {
                    const off = o.value === "resume" && !resumeOk;
                    return (
                      <button key={o.value} type="button" role="radio" aria-checked={cfg.strategy === o.value} disabled={off} className={`ocard ${cfg.strategy === o.value ? "on" : ""}`}
                        onClick={() => set("strategy", o.value)} title={off ? "Add resume questions first (step 3)" : undefined}>
                        <span className="oc-ic"><Icon name={STRATEGY_ICON[o.value]} /></span><span className="oc-t">{o.title}</span>
                        <span className="oc-d">{off ? "Needs resume questions: add some in step 3." : o.desc}</span>
                        <span className="oc-check" aria-hidden><Icon name="check" /></span>
                      </button>
                    );
                  })}
                </div></div>
              <div className="grid2" style={{ alignItems: "start" }}>
                <div className="fld"><div className="lbl">Starting level<small>{levelLabel(cfg.start_level)}</small></div>
                  <Seg label="Starting level" size="sm" value={cfg.start_level ?? "intermediate"} onChange={(v) => set("start_level", v)}
                    options={LEVELS.map((v) => ({ value: v, label: LEVEL_LABEL[v] }))} />
                  <div className="hint">The first question matches this level; it then moves up or down.</div></div>
                <div className="fld"><div className="lbl"><label htmlFor="maxq">Maximum questions</label><small>{poolCount ? `${poolCount} available` : "none chosen yet"}</small></div>
                  <input id="maxq" type="number" inputMode="numeric" min={1} max={60} value={cfg.max_questions ?? 10} style={{ width: 110 }}
                    onChange={(e) => set("max_questions", Math.max(1, Math.min(60, Math.round(Number(e.target.value)) || 1)))} />
                  <div className="hint">1 to 60. It can end sooner if the questions or the time run out.</div></div>
              </div>
              {cfg.strategy === "deep_dive" && (
                <div className="fld"><div className="lbl"><label htmlFor="focus">Focus topic</label><small>deep dive only</small></div>
                  <select id="focus" value={cfg.focus_topic ?? ""} onChange={(e) => set("focus_topic", e.target.value || null)}>
                    <option value="">Largest topic in my questions (default)</option>
                    {topicList.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                  <div className="hint">{topicList.length ? "The interviewer stays on this topic and goes deeper." : "Choose questions with topics in step 3 to pick one."}</div></div>
              )}
              {cfg.strategy === "resume" && !resumeOk && <div className="notice warn small" role="status" style={{ margin: 0 }}>Resume-based needs resume questions. Add some in step 3, or pick another strategy.</div>}
            </>}
            <div className="fld"><div className="lbl">Time limit<small>{minutesLabel(cfg.time_limit_minutes)}</small></div>
              <Seg label="Time limit" size="sm" value={cfg.time_limit_minutes ?? 0} onChange={(v) => set("time_limit_minutes", v === 0 ? null : v)}
                options={[0, 15, 30, 45, 60, 90].map((v) => ({ value: v, label: v === 0 ? "None" : `${v} min`, aria: v === 0 ? "No time limit" : `${v} minutes` }))} />
              <div className="hint">No new question starts after the limit; you can still finish the one you are on.</div></div>
          </Section>

          <Section step={3} icon="list" title="Questions" desc="Pick what you’ll be asked and in which order">
            <div className="fld"><div className="lbl">Question source{!ready.length && <small><a href="#/resumes">{(resumes.data?.length ?? 0) ? "Your resume is still being read" : "Add a resume"}</a> to get questions about your own experience</small>}</div>
              <Seg label="Question source" value={source} onChange={setSource} options={(["bank", "resume", "both"] as const).map((v) => ({ value: v, label: SOURCE_LABEL[v], icon: v === "bank" ? "list" : v === "resume" ? "file" : "layers", disabled: v !== "bank" && !ready.length }))} /></div>
            {source !== "resume" && <>
            <div className="row between">
              <Seg label="Select questions" value={mode} onChange={setMode} options={[
                { value: "all", label: `All questions (${questions.length})` }, { value: "selected", label: `Selected (${selected.size})` }]} />
              {!adaptive && <Seg label="Question order" value={cfg.order} onChange={(v) => set("order", v)} options={[
                { value: "supplied", label: "Supplied order", icon: "list" }, { value: "shuffled", label: "Shuffle", icon: "shuffle" }]} />}
            </div>
            {(sets.data?.length ?? 0) > 1 && (
              <div className="fld"><div className="lbl"><label htmlFor="qset">Question set</label></div>
                <select id="qset" aria-label="Question set" value={setId ?? ""} onChange={(e) => setSetId(Number(e.target.value))}>
                  {(sets.data ?? []).map((s) => <option key={s.id} value={s.id}>{s.name} ({s.question_count})</option>)}</select></div>
            )}
            {questions.length === 0 && !qs.loading && <div className="notice warn">This set is empty. <a href="#/questions">Add questions</a> first.</div>}
            {mode === "selected" && questions.length > 0 && (
              <div className="qpick">
                <div className="qpick-h">
                  <div className="searchbox"><Icon name="search" /><input type="search" aria-label="Search questions" placeholder="Search questions…" value={qsearch} onChange={(e) => setQsearch(e.target.value)} /></div>
                  <button className="btn" onClick={() => setSelected(new Set(questions.map((q) => q.id)))}>All</button>
                  <button className="btn" onClick={() => setSelected(new Set())}>None</button>
                </div>
                <div className="qpick-l">
                  {shownQs.map((q) => (
                    <label key={q.id}>
                      <input type="checkbox" checked={selected.has(q.id)} onChange={(e) => { const n = new Set(selected); e.target.checked ? n.add(q.id) : n.delete(q.id); setSelected(n); }} />
                      <span className="grow"><span className="muted">{q.position + 1}.</span> {q.text.length > 150 ? q.text.slice(0, 150) + "…" : q.text}</span>
                      {q.topic && <span className={`pill-tag ${topicClass(q.topic)}`}>{q.topic}</span>}
                    </label>
                  ))}
                  {shownQs.length === 0 && <div className="muted" style={{ padding: 16 }}>No questions match.</div>}
                </div>
              </div>
            )}
            </>}
            {source !== "bank" && ready.length > 0 && <>
              {source === "both" && <hr className="rz-hr" />}
              <ResumeQuestionsPanel resumes={ready} settings={gen} onSettings={setGen} questions={rqs} onQuestions={setRqs} saveToBank={saveToBank} onSaveToBank={setSaveToBank}
                cloud={!!cloud} aiConfig={ai.data?.config ?? null} onResumesChanged={() => void resumes.reload()} />
            </>}
            {ready.length > 0 && (
              <div className="auto-resume">
                <div className="trows"><div className={`trow2 ${autoOn ? "on" : ""}`}><span className="ti"><Icon name="file" /></span>
                  <div className="t"><b>Add questions from my resume automatically (offline)</b><span>Built instantly on this computer from the claims in your resume. No AI call, nothing is sent anywhere.</span></div>
                  <Switch label="Add questions from my resume automatically" checked={autoOn} onChange={(v) => setAuto((a) => ({ ...a, on: v, id: a.id ?? ready[0]?.id ?? null }))} /></div></div>
                {autoOn && (
                  <div className="auto-opts">
                    {ready.length > 1 && <div className="fld"><div className="lbl"><label htmlFor="auto-resume">Resume</label></div>
                      <select id="auto-resume" value={autoId ?? ""} onChange={(e) => setAuto((a) => ({ ...a, id: Number(e.target.value) }))}>{ready.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}</select></div>}
                    <div className="fld"><div className="lbl"><label htmlFor="auto-count">Number of questions</label><small>1 to 20</small></div>
                      <input id="auto-count" type="number" inputMode="numeric" min={1} max={20} value={auto.count} style={{ width: 100 }}
                        onChange={(e) => setAuto((a) => ({ ...a, count: Math.max(1, Math.min(20, Math.round(Number(e.target.value)) || 1)) }))} /></div>
                  </div>
                )}
              </div>
            )}
            {(source === "both" || (autoOn && useBank)) && !adaptive && (
              <div className="fld"><div className="lbl">Order<small>{(() => { const seq = mixSequence(mix, counts.bank, counts.resume); return mix === "shuffled" ? "all questions mixed at random" : seq.length ? `${seq.slice(0, 10).map((x) => (x === "B" ? "bank" : "resume")).join(" · ")}${seq.length > 10 ? " …" : ""}` : ""; })()}</small></div>
                <Seg label="Order of bank and resume questions" value={mix} onChange={setMix} options={(["resume_first", "bank_first", "interleave", "shuffled"] as const).map((v) => ({ value: v, label: MIX_LABEL[v] }))} />
                <div className="hint">“Supplied order / Shuffle” above still decides the order of the bank questions among themselves.</div></div>
            )}
          </Section>

                    <Section step={4} icon="voice" title="Interviewer" desc="Choose the voice and how much the interviewer probes">
            <div className="fld"><div className="lbl">Voice<small>{!voices.data ? "" : isSystem ? `${sysVoices === null ? "…" : sysVoices.length} offline voices on this computer` : `Phonon · ${voices.data.voices.length} voices`}</small></div>
              <div className="vcur" data-testid="voice-current">
                <span className="vcur-ic" aria-hidden="true"><Icon name="voice" /></span>
                <div className="vcur-t"><span className="vcur-k">Chosen voice</span><b>{voices.data ? voiceFull : <span className="skel" style={{ display: "inline-block", width: 120, height: 16 }} aria-hidden />}</b></div>
                <button type="button" className="vplay" disabled={!voices.data} aria-label={`Preview voice ${voiceFull}`} title={speech.key === `vp-${cfg.voice}` && speech.status !== "idle" ? "Stop" : "Preview"} onClick={() => previewVoice(cfg.voice)}>
                  {speech.key === `vp-${cfg.voice}` && speech.status === "loading" ? <span className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} /> : speech.key === `vp-${cfg.voice}` && speech.status !== "idle" ? <Stop /> : <Icon name="vol" size={15} />}</button>
                <button type="button" ref={changeVoiceBtn} className="btn" aria-expanded={voiceOpen} aria-controls="voice-panel" disabled={!voices.data} onClick={() => (voiceOpen ? closeVoices() : setVoiceOpen(true))}>{voiceOpen ? "Hide voices" : "Change voice"}</button>
              </div>
              {voiceOpen && (
                <div id="voice-panel" className="vpanel" onKeyDown={(e) => { if (e.key === "Escape") { e.stopPropagation(); closeVoices(); } }}>
                  <div className="vsearch"><Icon name="search" /><input type="search" aria-label="Search voices" placeholder="Search voices…" value={vsearch} autoFocus onChange={(e) => setVsearch(e.target.value)} /></div>
                  <div className="vgrid" role="radiogroup" aria-label="Voice" ref={vgrid}>
                    {voiceList.map((v) => {
                      const playing = speech.key === `vp-${v.id}` && speech.status !== "idle";
                      return (
                        <div key={v.id} role="radio" aria-checked={cfg.voice === v.id} aria-label={v.full} title={v.full} tabIndex={0} className={`vchip ${cfg.voice === v.id ? "on" : ""}`} onClick={() => chooseVoice(v.id)}
                          onKeyDown={(e) => { if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); chooseVoice(v.id); } }}>
                          <span className="vn">{v.label}</span>
                          <button className="vplay" aria-label={`Preview voice ${v.full}`} title={playing ? "Stop" : "Preview"} onClick={(e) => { e.stopPropagation(); previewVoice(v.id); }}>
                            {speech.key === `vp-${v.id}` && speech.status === "loading" ? <span className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} /> : playing ? <Stop /> : <Icon name="vol" size={15} />}</button>
                        </div>
                      );
                    })}
                    {voiceList.length === 0 && <div className="muted small">No voice matches “{vsearch}”.</div>}
                  </div>
                  <div className="hint">Press ▶ on any voice to hear it, or choose it to use it.</div>
                </div>
              )}
              {isSystem && sysVoices !== null && sysVoices.length === 0 && <div className="notice info small" style={{ marginTop: 8 }}>No offline voice was found, so questions will be shown as text only. Windows: Settings → Time &amp; language → Speech → Add voices. Linux: install <b>speech-dispatcher</b> and <b>espeak-ng</b>. Chrome’s online “Google” voices are never used.</div>}
              {voices.error && <div className="hint" style={{ color: "var(--bad)" }}>{voices.error}</div>}
              {speech.key?.startsWith("vp-") && speech.error && <div className="hint" style={{ color: "var(--bad)" }}>{speech.error}</div>}
            </div>
            <div className="grid2" style={{ alignItems: "start" }}>
              <div className="fld"><div className="lbl">Playback speed<small>{cfg.speech_speed}×</small></div>
                <Seg label="Playback speed" size="sm" value={cfg.speech_speed} onChange={(v) => { set("speech_speed", v); speaker.setRate(v); }}
                  options={[0.75, 1, 1.25, 1.5].map((v) => ({ value: v, label: `${v}×`, aria: `Speed ${v}x` }))} />
                <div className="hint">{isSystem ? "Applied by your computer’s voice." : "Phonon only speaks at 1×; the browser’s player adjusts speed."}</div></div>
              <div className="fld"><div className="lbl">Max follow-ups per question<small>{cfg.max_followups === 0 ? "off" : `up to ${cfg.max_followups}`}</small></div>
                <Seg label="Max follow-ups" size="sm" value={cfg.max_followups} onChange={(v) => set("max_followups", v)}
                  options={[0, 1, 2, 3].map((v) => ({ value: v, label: v === 0 ? "None" : String(v), aria: `Max follow-ups: ${v}` }))} />
                <div className="hint">A hard limit; follow-ups are only asked when they add value.</div></div>
            </div>
          </Section>
          <Section step={5} icon="target" title="Evaluation" desc="How strictly your answers are graded">
            <div className="fld"><div className="lbl">Strictness</div>
              <OptionCards label="Evaluation strictness" cols={3} value={cfg.strictness} onChange={(v) => set("strictness", v)} options={([
                ["lenient", "Lenient", "smile"], ["balanced", "Balanced", "target"], ["strict", "Strict", "bolt"]] as const).map(([value, title, ic]) => ({
                value, title, desc: STRICT_DESC[value], icon: ic === "smile" ? "check" : ic }))} /></div>
            <div className="notice info small" role="note" style={{ margin: 0 }}><b>Scores and feedback come at the end.</b> While you practice there is no score after each answer. When the interview is over you get every answer’s score, every follow-up’s score and your final score in one report.</div>
          </Section>

          <Section step={6} icon="settings" title="Experience" desc="Audio and input preferences">
            <div className="trows">
              <div className={`trow2 ${cfg.question_audio === "auto" ? "on" : ""}`}><span className="ti"><Icon name="vol" /></span>
                <div className="t"><b>Read each question aloud</b><span>Plays automatically when a question appears; otherwise use Play.</span></div>
                <Switch label="Read each question aloud automatically" checked={cfg.question_audio === "auto"} onChange={(v) => set("question_audio", v ? "auto" : "manual")} /></div>
              <div className={`trow2 ${cfg.mic_enabled ? "on" : ""}`}><span className="ti"><Icon name="mic" /></span>
                <div className="t"><b>Microphone input (speech to text)</b><span>{health.data?.stt.available ? `Transcribed offline with Whisper “${health.data.stt.model}”.` : `Unavailable — ${health.data?.stt.reason ?? "checking…"}`}</span></div>
                <Switch label="Enable microphone input" checked={cfg.mic_enabled} disabled={!health.data?.stt.available} onChange={(v) => set("mic_enabled", v)} /></div>
            </div>
          </Section>
          </div>
        </div></div>

        <aside className="summary" aria-label="Session summary">
          <div className="sum-h"><small>Session summary</small><h3>{cfg.title || "Untitled interview"}</h3></div>
          <div className="sum-b">{summary.map(([ic, k, v]) => <div className="sum-r" key={k}><span className="k"><Icon name={ic as never} />{k}</span><b>{v}</b></div>)}</div>
          <div className="sum-f">
            <div className={`ready ${llmReady ? "ok" : "bad"}`}><Icon name={llmReady ? (cloud ? "bolt" : "shield") : "alert"} />{cloud ? (llmReady ? `Cloud AI ready · ${health.data?.ai.grader_model}` : "Cloud AI not ready") : (llmReady ? "Local model ready · runs offline" : "Local model not ready")}</div>
            {cloud && llmReady && (
              <div className="notice info small" role="status" style={{ marginTop: 0 }} data-testid="cost-estimate">
                <b>Estimated cost: </b>{estCost === undefined ? "…" : estCost === null ? "unknown (a model has no price set)" : estCost === 0 ? "$0" : `up to ${fmtUsd(estCost)}`}
                <div className="muted">An upper bound for this interview. Your answers are sent to Ollama’s servers.</div>
              </div>
            )}
            {cloud && budgetToday?.reached && <div className="notice error small" role="alert" style={{ marginTop: 0 }}><b>Daily budget used up.</b> Answers will not be graded until you raise the limit in Settings → AI models or switch to the local model.</div>}
            {!cloud && llmReady && health.data?.memory?.tight && (
              <div className="notice warn small" role="status" style={{ marginTop: 0 }}>
                <b>Low free memory</b> — {health.data.memory.available_gb} GB free of {health.data.memory.total_gb} GB; the model needs about {health.data.memory.needs_gb} GB.
                Your computer may freeze for ~20 seconds while it loads. Closing browser tabs and other big apps first avoids that.
              </div>
            )}
            {active.length > 0 && <div className="notice warn small" role="status" style={{ marginTop: 0 }}><b>An interview is still active.</b> Continue or end “{active[0].title}” to start a new one.</div>}
            {count === 0 && <div className="notice warn small" role="status" style={{ marginTop: 0 }}>{source === "bank" ? "No questions selected yet." : rqs.length ? "Fix or remove the empty questions first." : "Generate and review your resume questions first."}</div>}
            <button className="btn primary big block" disabled={!canStart} onClick={start}>{busy ? "Starting…" : <>Start Interview <Icon name="arrowr" /></>}</button>
            <div className="est">{count ? <><span className="est-ic"><Icon name="clock" /></span><span>{adaptive ? "up to " : ""}<b>{count}</b> question{count === 1 ? "" : "s"} <i className="est-dot" aria-hidden="true" /> about <b>{estShown} min</b></span></> : <><span className="est-ic"><Icon name="list" /></span><span>Add questions to begin</span></>}</div>
          </div>
        </aside>
      </div>
    </div>
  );
}
