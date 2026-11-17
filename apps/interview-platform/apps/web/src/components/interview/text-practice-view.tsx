"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { isApiError } from "@open-conversation/api-client";
import type { TextPracticeAnswer, TextPracticeState } from "@open-conversation/types";
import { Button, Textarea } from "@open-conversation/ui";
import { PageBar } from "@/components/app/app-shell";
import { api } from "@/lib/api";
import { errorMessage } from "@/lib/errors";

export function TextPracticeView({ id }: { id: string }) {
  const [session, setSession] = useState<TextPracticeState | null>(null);
  const [readyToStart, setReadyToStart] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [consent, setConsent] = useState(false);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const pending = useRef<TextPracticeAnswer | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const next = await api().interviews.textPractice(id);
        if (active) setSession(next);
      } catch (e) {
        if (isApiError(e) && e.code === "TEXT_PRACTICE_NOT_FOUND") {
          try {
            const interview = await api().interviews.get(id);
            if (active) {
              if (interview.status === "READY") setReadyToStart(true);
              else setError("This interview is already in another mode or is not ready. Return to the plan to continue.");
            }
          } catch (inner) { if (active) setError(errorMessage(inner)); }
        } else if (active) setError(errorMessage(e));
      } finally { if (active) setLoading(false); }
    }
    void load();
    return () => { active = false; };
  }, [id]);

  async function start() {
    setBusy(true); setError("");
    try { setSession(await api().interviews.startTextPractice(id)); setReadyToStart(false); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }

  async function answer() {
    if (!session) return;
    const request = pending.current ?? { requestId: crypto.randomUUID(), expectedVersion: session.version, text: draft.trim() };
    pending.current = request;
    setBusy(true); setError("");
    try {
      setSession(await api().interviews.answerTextPractice(id, request));
      pending.current = null; setDraft("");
    } catch (e) {
      if (isApiError(e) && e.code === "TEXT_VERSION_CONFLICT") {
        pending.current = null;
        try { setSession(await api().interviews.textPractice(id)); } catch { /* Keep the draft and the original error. */ }
        setError("The interview changed in another tab. Review the current question before submitting your answer.");
      } else if (isApiError(e) && e.status > 0 && e.status < 500 && e.status !== 429) {
        pending.current = null; setError(errorMessage(e));
      } else {
        setError("We could not confirm whether your answer was saved. Retry the same answer safely.");
      }
    } finally { setBusy(false); }
  }

  const finished = session?.status === "COMPLETED";
  return (
    <div>
      <PageBar title="Text practice" />
      <main className="mx-auto max-w-[780px] px-4 pb-16 pt-8 sm:px-6">
        <h1 className="font-display text-[28px] font-semibold">Practice by typing</h1>
        <p className="mt-2 text-sm text-muted-foreground">Answer the planned questions in writing. No microphone or camera is used in this mode.</p>
        {loading ? <p className="mt-6" role="status">Loading your interview…</p> : null}
        {error ? <p className="mt-5 rounded-md border border-destructive/40 p-3 text-sm" role="alert">{error}</p> : null}
        {readyToStart ? (
          <div className="mt-8 rounded-lg border border-border p-5">
            <h2 className="font-semibold">Before you start</h2>
            <p className="mt-2 text-sm text-muted-foreground">Your written answers are saved with this interview and may be sent to the configured AI provider for practice feedback. Feedback can be inaccurate and is not a hiring decision. You can delete the interview from your account.</p>
            <label className="mt-4 flex items-start gap-2 text-sm"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1" /> <span>I agree to save my answers and use the configured provider for feedback.</span></label>
            <Button className="mt-5" disabled={!consent || busy} onClick={() => void start()}>Start text practice</Button>
          </div>
        ) : null}
        {session ? (
          <>
            <ol className="mt-8 space-y-4" aria-label="Interview conversation">
              {session.events.filter((event) => event.kind !== "COMPLETED").map((event) => (
                <li key={event.id} className="rounded-lg border border-border p-4">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-subtle-foreground">{event.kind === "QUESTION" ? `Question ${event.round + 1}.${event.question + 1}` : "Your answer"}</p>
                  <p className="whitespace-pre-wrap text-sm leading-6">{event.text}</p>
                </li>
              ))}
            </ol>
            {finished ? (
              <div className="mt-6"><p className="mb-4">Interview completed. Feedback may take a moment to appear.</p><Button asChild><Link href={`/i/${id}/report`}>View report</Link></Button></div>
            ) : (
              <div className="mt-6">
                <label htmlFor="practice-answer" className="mb-2 block text-sm font-semibold">Your answer</label>
                <Textarea id="practice-answer" value={draft} onChange={(e) => setDraft(e.target.value)} readOnly={!!pending.current} maxLength={8000} rows={6} placeholder="Write your answer here…" />
                <div className="mt-3 flex items-center gap-4"><Button onClick={() => void answer()} disabled={busy || !draft.trim()}>{pending.current ? "Retry answer" : "Submit answer"}</Button><span className="text-xs text-subtle-foreground">{draft.length}/8000 characters</span></div>
              </div>
            )}
          </>
        ) : null}
        <Link href={`/i/${id}`} className="mt-8 inline-block text-sm text-primary underline">Back to interview plan</Link>
      </main>
    </div>
  );
}
