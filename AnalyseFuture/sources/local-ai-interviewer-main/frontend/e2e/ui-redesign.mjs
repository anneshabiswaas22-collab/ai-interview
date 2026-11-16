// Real-Chrome checks for the UI reorganisation: the sidebar never overlaps (any height, rail, phone drawer), Setup presets and the compact
// voice row, the tabbed Report (keyboard + remembered tab), and the Home "Next step" card. Isolated backend on :3100, throw-away data.
import { BASE, check, clickText, launch, reportIssues, sleep, startBackend } from "./lib.mjs";
import { seedHistory } from "./seed.mjs";

const be = await startBackend({ OLLAMA_API_KEY: "" });
seedHistory(be.dataDir);
const { browser, page, issues } = await launch({ width: 1280, height: 820 });
const api = (path, init) => fetch(BASE + path, { headers: { "content-type": "application/json" }, ...init }).then((r) => r.json());
const aria = (sel, name) => page.$eval(sel, (e, n) => e.getAttribute(n), name);
const checked = (title) => page.evaluate((t) => [...document.querySelectorAll("[data-testid=presets] .ocard")].find((b) => b.textContent.includes(t))?.getAttribute("aria-checked") === "true", title);
const sumRow = (key) => page.evaluate((k) => [...document.querySelectorAll(".sum-r")].find((r) => r.querySelector(".k")?.textContent.trim() === k)?.querySelector("b")?.textContent.trim(), key);

try {
  const sid = (await api("/api/sets"))[0].id;
  for (const [text, topic] of [["What is idempotency in ETL?", "ETL"], ["How do consumer groups scale?", "Kafka"], ["What does catchup do in Airflow?", "Airflow"], ["Explain a window function.", "SQL"],
    ["Why does skew slow a Spark join?", "Spark"], ["Star schema or data vault?", "Modeling"], ["How do micro-partitions prune?", "Snowflake"]])
    await api(`/api/sets/${sid}/questions`, { method: "POST", body: JSON.stringify({ text, topic, difficulty: "medium" }) });

  // ---------------------------------------------------------------- 1. the sidebar never overlaps
  const fits = () => page.evaluate(() => {
    const nav = document.querySelector(".sidebar nav"), foot = document.querySelector(".sb-foot"), items = [...nav.querySelectorAll(".sb-item")];
    const last = items[items.length - 1].getBoundingClientRect(), f = foot.getBoundingClientRect(), n = nav.getBoundingClientRect();
    return { navBottom: Math.round(n.bottom), footTop: Math.round(f.top), lastBottom: Math.round(last.bottom), scrolls: nav.scrollHeight > nav.clientHeight + 1, footVisible: f.bottom <= innerHeight + 1 };
  });
  await page.goto(BASE, { waitUntil: "networkidle0" });
  for (const [w, h, rail, label] of [[1280, 900, false, "900"], [1280, 820, false, "820"], [1280, 700, false, "700"], [1280, 640, false, "640"], [1280, 600, false, "600"], [1280, 820, true, "820 rail"], [1280, 640, true, "640 rail"], [1280, 600, true, "600 rail"]]) {
    await page.setViewport({ width: w, height: h });
    await page.evaluate((r) => { localStorage.setItem("lai.sidebar", r ? "collapsed" : "open"); }, rail);
    await page.goto(`${BASE}/#/home`, { waitUntil: "networkidle0" }); await page.reload({ waitUntil: "networkidle0" }); await sleep(300);
    const m = await fits();
    check(m.navBottom <= m.footTop + 1 && m.footVisible, `sidebar at ${label}px tall: the menu ends above the services/theme/profile area (menu ${m.navBottom} <= footer ${m.footTop})`);
    if (h >= 600) check(!m.scrolls && m.lastBottom <= m.footTop, `sidebar at ${label}px tall: every link, including "Model usage", is fully visible without scrolling (${m.lastBottom} <= ${m.footTop})`);
  }
  await page.evaluate(() => { localStorage.setItem("lai.sidebar", "open"); });
  for (const h of [560, 480]) {
    await page.setViewport({ width: 1280, height: h }); await page.reload({ waitUntil: "networkidle0" });
    const tiny = await fits();
    check(tiny.navBottom <= tiny.footTop + 1 && tiny.footVisible, `at ${h}px tall the menu never slides under the footer${tiny.scrolls ? " (it scrolls on its own)" : ""}`);
    if (h === 480) check(tiny.scrolls, "…and when there really is not enough room (480px) the menu scrolls on its own");
  }
  await page.setViewport({ width: 1280, height: 900 }); await page.reload({ waitUntil: "networkidle0" });
  check((await aria(".status-title", "aria-expanded")) === "true", "a tall window starts with the full services list open");
  await page.click(".status-title"); await sleep(100);
  check((await aria(".status-title", "aria-expanded")) === "false" && (await page.$$(".status span[title] .dot")).length === 0, "the services panel can be folded to its summary (it lists only what needs attention)");
  await page.setViewport({ width: 390, height: 844 }); await page.reload({ waitUntil: "networkidle0" });
  await page.click('button[aria-label="Open menu"]'); await sleep(450);
  const ph = await fits();
  check(ph.navBottom <= ph.footTop + 1 && ph.footVisible && !ph.scrolls, `phone drawer (844px): menu above the footer and fully visible (${ph.lastBottom} <= ${ph.footTop})`);
  await page.setViewport({ width: 1280, height: 820 });

  // ---------------------------------------------------------------- 2. setup: presets + compact voice row
  await page.goto(`${BASE}/#/setup`, { waitUntil: "networkidle0" }); await page.reload({ waitUntil: "networkidle0" });
  await page.waitForSelector('[data-testid="presets"]'); await sleep(400);
  const cards = await page.$$eval("[data-testid=presets] .ocard", (b) => b.map((x) => ({ t: x.querySelector(".oc-t").textContent, off: x.disabled, d: x.querySelector(".oc-d")?.textContent })));
  check(cards.map((c) => c.t).join("|") === "Quick practice|Full mock|Resume round", "three preset cards: Quick practice, Full mock, Resume round");
  check(cards[2].off && /resume/i.test(cards[2].d) && !cards[0].off && !cards[1].off, `Resume round is disabled without a ready resume and says why (“${cards[2].d}”)`);
  check(!(await checked("Quick practice")) && !(await checked("Full mock")), "no preset is marked active before one is chosen");
  await clickText(page, "[data-testid=presets] .ocard", "Quick practice"); await sleep(250);
  check(await checked("Quick practice"), "Quick practice is marked active after clicking it");
  check((await sumRow("Mode")) === "Fixed order" && (await sumRow("Questions")) === "5 · In order" && (await sumRow("Follow-ups")) === "Up to 1 each" && (await sumRow("Time limit")) === "No limit", "…and the settings below changed (fixed order, 5 questions in order, 1 follow-up, no limit)");
  check(/Selected \(5\)/.test(await page.evaluate(() => document.body.innerText)), "…the question picker shows Selected (5)");
  await page.click('[aria-label="Max follow-ups"] [aria-label="Max follow-ups: 2"]'); await sleep(200);
  check(!(await checked("Quick practice")), "changing a setting (follow-ups 1 → 2) drops the active mark");
  await clickText(page, "[data-testid=presets] .ocard", "Full mock"); await sleep(250);
  check(await checked("Full mock") && !(await checked("Quick practice")), "Full mock becomes the active preset");
  check((await sumRow("Mode")) === "Adaptive · Progressive" && (await sumRow("Time limit")) === "45 min" && (await sumRow("Follow-ups")) === "Up to 2 each" && /^Up to 7/.test((await sumRow("Questions")) ?? ""), `…adaptive, progressive, 45 min, 2 follow-ups, up to 7 questions (only 7 exist): ${await sumRow("Questions")}`);
  check(/only 7 questions/.test(await page.evaluate(() => document.querySelector(".presets-note")?.textContent ?? "")), "…and it says the bank has fewer than 8 questions");
  await page.click('[aria-label="Time limit"] [aria-label="30 minutes"]'); await sleep(200);
  check(!(await checked("Full mock")), "changing the time limit drops the active mark");

  check((await page.$$(".vchip")).length === 0 && (await page.$eval('[data-testid="voice-current"]', (e) => e.innerText)).trim().length > 0, "voice: only the chosen voice is shown, the list is folded");
  const prev = await page.$('[data-testid="voice-current"] button[aria-label^="Preview voice"]');
  check(!!prev, "voice: the chosen voice has its own ▶ preview button");
  check((await aria('[data-testid="voice-current"] .btn', "aria-expanded")) === "false", "voice: “Change voice” is a disclosure (aria-expanded=false)");
  await clickText(page, "button", "Change voice"); await sleep(250);
  check((await page.$$(".vchip")).length > 5 && (await page.$('input[aria-label="Search voices"]')) !== null, "voice: Change voice opens the searchable list inline (no dialog, no backdrop)");
  check((await page.$$(".overlay")).length === 0, "voice: no dimmed overlay");
  const clipped = await page.$$eval(".vchip .vn", (els) => els.filter((e) => e.scrollWidth > e.clientWidth + 1).length);
  check(clipped === 0, "voice: no voice name is cut off");
  const pick = await page.$eval(".vchip:not(.on)", (e) => e.getAttribute("aria-label"));
  await page.click(".vchip:not(.on)"); await sleep(300);
  check((await page.$$(".vchip")).length === 0 && (await page.$eval('[data-testid="voice-current"]', (e) => e.innerText)).includes(pick), `voice: choosing “${pick}” collapses the list and shows it as the chosen voice`);
  check((await page.evaluate(() => document.activeElement?.textContent)) === "Change voice", "voice: focus returns to the Change voice button");

  // ---------------------------------------------------------------- 3. report: tabs
  const rep = (await api("/api/interviews")).find((i) => i.has_report).id;
  await page.goto(`${BASE}/#/report/${rep}`, { waitUntil: "networkidle0" }); await page.waitForSelector('.rtabs [role="tab"]');
  const tabs = await page.$$eval('.rtabs [role="tab"]', (t) => t.map((x) => x.textContent));
  check(tabs.join("|") === "Overview|Questions|Skills & progress", `report tabs (no Adaptive tab for a non-adaptive report): ${tabs.join(", ")}`);
  const sel = () => page.$eval('.rtabs [role="tab"][aria-selected="true"]', (t) => t.textContent);
  check((await sel()) === "Overview" && (await page.$eval('.rpanel:not([hidden]) .hero', () => true).catch(() => false)), "Overview is the default tab and holds the score ring and stats");
  const visible = () => page.$$eval('.rpanel', (p) => p.filter((x) => !x.hidden).length);
  check((await visible()) === 1, "exactly one tab panel is visible");
  const inOverview = await page.evaluate(() => { const p = document.querySelector('.rpanel:not([hidden])'); return ["Overall feedback", "Strengths", "Knowledge gaps", "Recommendations", "Topic-wise Performance"].every((t) => p.innerText.includes(t)) && !p.innerText.includes("Insights"); });
  check(inOverview, "Overview: the merged feedback card (summary, strengths, gaps, recommendations) and topic performance; no separate Insights card");
  await page.focus('.rtabs [role="tab"][aria-selected="true"]'); await page.keyboard.press("ArrowRight"); await sleep(150);
  check((await sel()) === "Questions" && (await page.evaluate(() => document.activeElement?.getAttribute("role"))) === "tab", "ArrowRight moves to the next tab and keeps focus on the tab strip");
  check((await page.$eval('.rpanel:not([hidden]) [data-testid="scorecard"]', () => true).catch(() => false)), "Questions: the scorecard and the detailed per-question feedback");
  await page.keyboard.press("End"); await sleep(150);
  check((await sel()) === "Skills & progress", "End jumps to the last tab");
  await page.reload({ waitUntil: "networkidle0" }); await page.waitForSelector('.rtabs [role="tab"]');
  check((await sel()) === "Skills & progress", "the selected tab is remembered across a reload");
  check((await page.$eval("h1", (e) => e.textContent)) === "Interview Report" && (await page.$('a[download]')) !== null, "the header (title and exports) stays above the tabs");
  await page.evaluate(() => sessionStorage.clear());

  // ---------------------------------------------------------------- 4. home: next step
  await page.goto(`${BASE}/#/home`, { waitUntil: "networkidle0" }); await page.waitForSelector('[data-testid="next-step"]');
  check((await page.$eval('[data-testid="next-step"]', (e) => e.dataset.kind)) === "practice" && /Practise your weakest topics: /.test(await page.$eval('[data-testid="next-step"] h2', (e) => e.textContent)), "Home: with weak topics and nothing running, the Next step is to practise the weakest topics");
  await page.click('[data-testid="next-step"] button'); await page.waitForFunction(() => location.hash === "#/setup", { timeout: 8000 });
  check(true, "…and the button uses the existing practise flow (opens Setup with those questions preselected)");
  await page.waitForSelector('[data-testid="presets"]');
  check(/preselected|Practicing/.test(await page.evaluate(() => document.body.innerText)), "…Setup says which questions were preselected");
  const st = await api("/api/interviews", { method: "POST", body: JSON.stringify({ set_id: sid, config: { title: "Resume later", feedback_mode: "at_end", max_followups: 1, question_audio: "manual" } }) });
  await page.goto(`${BASE}/#/home`, { waitUntil: "networkidle0" }); await page.reload({ waitUntil: "networkidle0" }); await page.waitForSelector('[data-testid="next-step"]');
  const ns = await page.$eval('[data-testid="next-step"]', (e) => ({ kind: e.dataset.kind, t: e.innerText, href: e.querySelector("a")?.getAttribute("href") }));
  check(ns.kind === "continue" && /Continue Resume later/.test(ns.t) && /Question 1 of 7/.test(ns.t) && ns.href === `#/interview/${st.id}`, `Home: an interview in progress takes priority: “Continue Resume later”, question 1 of 7, linking to it`);
  check((await page.$$('[data-testid="next-step"], [data-testid="active-interview"]')).length === 1, "Home: the unfinished interview is announced once");
  reportIssues(issues, ["net::ERR_ABORTED"]);
} catch (e) { console.log("FAIL  exception: " + (e.stack || e)); process.exitCode = 1; }
finally { await browser.close(); be.proc.kill(); }
console.log(process.exitCode ? "\nSOME CHECKS FAILED" : "\nALL CHECKS PASSED");
