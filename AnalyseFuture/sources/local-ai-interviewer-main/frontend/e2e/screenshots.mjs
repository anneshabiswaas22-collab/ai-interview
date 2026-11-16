// Regenerates the README screenshots (docs/assets/screenshots/*.png) from the REAL app, against an isolated backend with a fake
// local model and fictional seed data (never your data). Usage: cd frontend && npm run build && node e2e/screenshots.mjs
// Also renders docs/assets/social-preview.png (1280x640) from docs/assets/social-preview.html.
import { execFileSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import { join } from "node:path";
import { BASE, ROOT, VENV_PYTHON, clickText, launch, sleep, startBackend, waitText } from "./lib.mjs";
import { startFakeLlm } from "./fakellm.mjs";
import { seedHistory } from "./seed.mjs";

const OUT = join(ROOT, "docs", "assets", "screenshots");
mkdirSync(OUT, { recursive: true });

// A fictional candidate (no real person): used for the resume and adaptive-interview screenshots.
const RESUME_PY = `
import json, sys
sys.path[:0] = [sys.argv[2], sys.argv[2] + "/tests"]
from app.db import Database
from intel_fixtures import PROFILE, RAW_RESUME
db = Database(sys.argv[1] + "/interviewer.sqlite3")
now = "2026-11-10T10:00:00+00:00"
with db.tx() as c:
    c.execute("""INSERT INTO resumes(name, original_filename, stored_name, sha256, size_bytes, pages, status, raw_text, profile_json, ai_profile_json,
                 extraction_method, created_at, updated_at, job_id, revision) VALUES ('Data engineer CV','cv.pdf','demo.pdf','demo',100,1,'ready',?,?,?,'text',?,?,1,1)""",
              (RAW_RESUME, json.dumps(PROFILE), json.dumps(PROFILE), now, now))
`;

const llm = await startFakeLlm({ delayMs: 50 });
const be = await startBackend({ OLLAMA_HOST_URL: llm.url, TTS_PROVIDER: "system", STT_ENABLED: "0", OLLAMA_API_KEY: "" });
seedHistory(be.dataDir);
execFileSync(VENV_PYTHON, ["-c", RESUME_PY, be.dataDir, join(ROOT, "backend")], { stdio: "inherit" });
const { browser, page } = await launch({ width: 1280, height: 820 });
const shot = async (name, full = false) => { await sleep(400); await page.screenshot({ path: join(OUT, `${name}.png`), fullPage: full }); console.log("saved", name); };
const api = (path, init) => fetch(BASE + path, { headers: { "content-type": "application/json" }, ...init }).then((r) => r.json());
// a believable question bank (covering the seeded history's topics) and a fictional user name, so no first-run prompts show
const sid = (await api("/api/sets"))[0].id;
for (const [text, topic, difficulty] of [["What does catchup do in an Airflow DAG?", "Airflow", "easy"], ["How do micro-partitions affect query pruning in Snowflake?", "Snowflake", "medium"],
  ["Why does data skew slow down a Spark join and how do you fix it?", "Spark", "hard"], ["How do you remove duplicate rows while keeping the latest one?", "SQL", "medium"],
  ["When would you choose a star schema over a data vault?", "Modeling", "medium"]])
  await api(`/api/sets/${sid}/questions`, { method: "POST", body: JSON.stringify({ text, topic, difficulty }) });
await page.evaluateOnNewDocument(() => { try { localStorage.setItem("lai.name", "Alex"); } catch { /* ignore */ } });

try {
  await page.goto(`${BASE}/#/home`); await waitText(page, "Recent");
  await shot("dashboard");

  await page.goto(`${BASE}/#/setup`); await waitText(page, "Interview mode");
  await clickText(page, "button, [role=radio], label", "Adaptive");
  await page.evaluate(() => [...document.querySelectorAll("h2, h3")].find((h) => h.textContent.includes("Interview mode"))?.scrollIntoView({ block: "start" }));
  await page.evaluate(() => window.scrollBy(0, -90));
  await shot("setup-adaptive");

  const reports = await api("/api/interviews");
  const latest = reports.find((r) => r.has_report);
  await page.goto(`${BASE}/#/report/${latest.id}`); await waitText(page, "Topic-wise Performance");
  await shot("report");

  const resumes = await api("/api/resumes");
  await page.goto(`${BASE}/#/resumes/${resumes[0].id}`); await waitText(page, "Candidate profile");
  await clickText(page, "button, [role=tab]", "Candidate profile", { exact: true });
  await waitText(page, "Worth preparing", 20000);
  await shot("candidate-profile");


  const st = await api("/api/interviews", { method: "POST", body: JSON.stringify({ set_id: sid, config: { title: "Adaptive data engineering practice", mode: "adaptive",
    strategy: "resume", start_level: "intermediate", max_questions: 6, time_limit_minutes: 30, feedback_mode: "at_end", max_followups: 1, question_audio: "manual" },
    resume_auto: { resume_id: resumes[0].id, count: 3 } }) });
  await page.goto(`${BASE}/#/interview/${st.id}`); await waitText(page, "Why this question", 20000);
  await page.evaluate(() => { const t = document.querySelector("textarea"); if (t) { const set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set; set.call(t, "One DAG per source system, one task per table. Failed tasks retried three times with exponential backoff; after that an on-call alert went out with the failing task and run date."); t.dispatchEvent(new Event("input", { bubbles: true })); } });
  await shot("interview-adaptive");
  await api(`/api/interviews/${st.id}/end`, { method: "POST" });

  await page.setViewport({ width: 1280, height: 640 });
  await page.goto("file://" + join(ROOT, "docs", "assets", "social-preview.html"));
  await sleep(300);
  await page.screenshot({ path: join(ROOT, "docs", "assets", "social-preview.png") });
  console.log("saved social-preview");
} finally {
  await browser.close(); be.proc.kill(); await llm.stop();
}
