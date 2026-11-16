# Resume-to-interview intelligence

Builds on the existing resume pipeline (PDF upload → text extraction / OCR → AI organisation into an editable profile → your
corrections). Everything on this page is **deterministic and local**: `GET /api/resumes/{id}/intelligence` makes no model call and
sends nothing anywhere. It is recomputed from your *saved* profile on every request, so editing the profile is how you correct it.

Implementation: `backend/app/services/candidate_profile.py`, `tech_implications.py`.

## Candidate profile

| Part | How it is built |
|---|---|
| Skill inventory | skills section + technologies detected in roles and projects, merged by alias (Postgres = PostgreSQL). Confidence: **high** = listed *and* used in a role/project; **medium** = used but not listed; **low** = listed only. Each skill lists where it appears. |
| Source references | every role, project, bullet and achievement is looked up in the raw extracted text: `verified` (found verbatim after normalisation), `partial` (≥ 80 % of its words present), `not_found`, with the line number. |
| Extraction quality | share of profile entries found in the raw text, with examples of entries that were not — usually AI rewording you may want to correct. |
| Experience summary | roles, companies, total dated experience (overlaps merged), current roles, gaps of 6+ months. |
| Technology relationships | technologies used together in the same role or project. |
| Claims | responsibilities and achievements (with or without numbers), each with its source reference. |
| Clarification areas | vague contribution ("helped", "worked on"), team vs individual ("we"), a number without a baseline, an improvement without a measure, a listed skill with no evidence of use, a role with no description, a timeline gap. Worded as things worth preparing — never as doubts about honesty. |
| Injection warnings | lines that look like instructions to an AI ("ignore previous instructions", "rate this candidate 10/10"). They are shown, never followed, and such lines are left out of every offline question and claim excerpt; resume text is always fenced as untrusted data in prompts. |

## Claim-grounded questions

Questions come from three sources, interleaved and de-duplicated:

1. **Technical implications** of technologies and activities named in a claim — a reviewed catalogue (`tech_implications.py`) of what
   an experienced interviewer asks someone who used, e.g., Airflow (failed task retries, idempotent backfills, why Airflow), Snowflake
   (warehouse cost control, incremental loads without duplicates), Kafka (delivery guarantees, lag), and ~30 others, plus engineering
   activities (data pipelines, migrations, optimisation, real-time systems, ML models). Each question is phrased around the claim's own
   context ("the StreamWatch project", "your role as Data Engineer at Acme").
2. **Project deep-dive** for each project: problem → architecture and data flow (with its stated technologies) → key decision and
   rejected alternatives → testing → failure handling → scaling → security → what you would redesign, from easy to hard.
3. **Clarification** questions from the clarification areas.

Every question carries its claim `{section, label, excerpt}` — the exact resume text it is about — which is stored with the interview,
shown in the report, and fenced as untrusted context when the answer is graded. Activity patterns are deliberately narrow
("data pipeline", not any "pipeline"; "React" not "React to …"; "AWS Lambda" not a Python lambda) to avoid questions about technology the
resume never claims (tested). Offline questions that repeat a reviewed question are dropped.

The existing **AI question writer** (Interview → Questions from your resume) is unchanged and still available; the offline generator is
an additional, instant option (`resume_auto`).

## In interviews

- `resume_auto: {resume_id, count}` on interview creation adds offline questions (works in fixed and adaptive mode).
- The **resume** strategy of the adaptive engine prefers claims not yet discussed, then revisits weakly explained ones.
- The interview plan stores the resume's roles/projects; the report shows **resume coverage** (discussed vs not yet explored) next to
  the per-claim verdicts (Solid / Shaky / Weak) that already existed.
- The resume page shows **practice history** per claim across past interviews and the areas not yet explored.
- Resume-based questioning is opt-in: an interview contains resume questions only when you choose a resume.

## Privacy

Nothing here sends data anywhere. Resume content reaches a model only through the existing, separately consented paths (organising the
resume, the AI question writer, grading resume answers), and in cloud mode only after the existing per-resume cloud consent.
