"""Resume-to-Interview Intelligence: candidate profile, source references, clarification areas, injection flags, traceable questions."""
import copy
from datetime import date

from app.schemas import ResumeProfile
from app.services import candidate_profile as cp
from app.services import tech_implications as ti
from intel_fixtures import PROFILE, RAW_RESUME, ready_resume


def build(profile=PROFILE, raw=RAW_RESUME, **kw):
    return cp.build(1, "Resume 1", ResumeProfile.model_validate(profile), raw, today=date(2026, 11, 1), **kw)


def test_skills_are_deduplicated_across_aliases_with_evidence_based_confidence():
    skills = {s["name"]: s for s in build()["skills"]}
    assert "PostgreSQL" in skills and "Postgres" in skills["PostgreSQL"]["aliases"] and "Postgres" not in skills
    assert skills["Apache Airflow"]["confidence"] == "high" and "Data Engineer at Acme Corp" in skills["Apache Airflow"]["used_in"]
    assert skills["Apache Kafka"]["confidence"] == "medium"          # used in a project, not listed
    assert skills["Kubernetes"]["confidence"] == "low"               # listed only
    names = [s["name"].lower() for s in build()["skills"]]
    assert len(names) == len(set(names))


def test_duplicate_skills_in_the_resume_collapse():
    p = copy.deepcopy(PROFILE)
    p["skills"].append({"group": "Other", "items": ["python", "PYTHON", "Snowflake"]})
    skills = [s["name"].lower() for s in build(p)["skills"]]
    assert skills.count("python") == 1 and skills.count("snowflake") == 1


def test_sources_reference_the_raw_text_and_catch_reworded_content():
    data = build()
    claim = next(c for c in data["claims"] if c["text"].startswith("Developed an ETL"))
    assert claim["source"]["status"] == "verified" and claim["source"]["line"] == 5
    p = copy.deepcopy(PROFILE)
    p["experience"][0]["bullets"].append("Led a team of 40 engineers to build a quantum compiler.")      # not in the resume text
    q = build(p)
    fake = next(c for c in q["claims"] if "quantum" in c["text"])
    assert fake["source"]["status"] == "not_found"
    assert q["extraction"]["not_found"] >= 1 and any("quantum" in x for x in q["extraction"]["not_found_examples"])
    assert build()["extraction"]["confidence"] == "high"


def test_projects_experience_and_relationships():
    data = build()
    assert data["projects"][0]["name"] == "StreamWatch" and data["projects"][0]["has_metrics"]
    assert data["experience"]["roles"] == 2 and data["experience"]["gaps"] and data["experience"]["gaps"][0]["months"] >= 6
    pair = {(r["a"], r["b"]) for r in data["relationships"]}
    assert ("Apache Airflow", "Snowflake") in pair


def test_clarification_areas_are_neutral_and_specific():
    kinds = {a["kind"] for a in build()["clarifications"]}
    assert {"vague_contribution", "metric_needs_context", "team_vs_individual", "listed_skill_without_evidence", "role_without_detail", "timeline_gap"} <= kinds
    text = " ".join(a["why"] + a["suggested_question"] for a in build()["clarifications"]).lower()
    for word in ("lie", "fake", "dishonest", "exaggerat", "fabricat"):
        assert word not in text


def test_prompt_injection_in_the_resume_is_flagged_and_never_becomes_a_question():
    data = build()
    assert data["injection_warnings"] and data["injection_warnings"][0]["line"] == 16
    assert not any("ignore previous" in q["text"].lower() or "10/10" in q["text"] for q in data["suggested_questions"])


def test_questions_are_grounded_in_real_claims_and_technologies():
    qs = build(question_limit=20)["suggested_questions"]
    assert len(qs) == 20
    for q in qs:
        assert q["claim"]["excerpt"] and q["claim"]["label"] and q["resume_id"] == 1
    airflow = [q for q in qs if q["topic"] == "Apache Airflow"]
    assert airflow and all("Data Engineer at Acme Corp" in q["claim"]["label"] and "Airflow" in q["claim"]["excerpt"] for q in airflow)
    assert any("idempotent" in q["text"] or "retried" in q["text"] for q in airflow)
    assert any(q["kind"].startswith("project_") and "StreamWatch" in q["text"] for q in qs)
    assert any(q["topic"] == "Snowflake" and "incremental" in q["text"].lower() for q in qs)


def test_questions_are_unique():
    texts = [q["text"] for q in build(question_limit=30)["suggested_questions"]]
    assert len(texts) == len(set(texts))


def test_technology_detection_avoids_false_positives():
    names = {h.tech.name for h in ti.detect("Configured CI/CD pipelines with GitHub Actions; wrote data models in dbt")}
    assert "ETL / data pipelines" not in names and "Machine learning models" not in names and "CI/CD" in names
    assert ti.canonical("Postgres")[0] == "PostgreSQL" and ti.canonical("Rust")[0] == "Rust"


def test_empty_resume_profile_produces_an_empty_but_valid_view():
    data = cp.build(1, "Empty", ResumeProfile(), "")
    assert data["skills"] == [] and data["suggested_questions"] == [] and data["extraction"]["score"] is None


def test_intelligence_endpoint_follows_user_corrections(client, container):
    rid = ready_resume(container)
    first = client.get(f"/api/resumes/{rid}/intelligence").json()
    assert any(s["name"] == "Kubernetes" for s in first["skills"]) and first["unexplored"]
    p = copy.deepcopy(PROFILE)
    p["skills"][1]["items"] = ["Airflow", "Snowflake"]                                      # the user removes skills they never used
    rev = client.get(f"/api/resumes/{rid}").json()["revision"]
    assert client.patch(f"/api/resumes/{rid}", json={"revision": rev, "profile": p}).status_code == 200
    after = client.get(f"/api/resumes/{rid}/intelligence").json()
    assert not any(s["name"] == "Kubernetes" for s in after["skills"])


def test_intelligence_requires_a_ready_resume_and_makes_no_model_call(client, container, fake):
    rid = ready_resume(container)
    with container.db.tx() as c:
        c.execute("UPDATE resumes SET status='structuring' WHERE id=?", (rid,))
    r = client.get(f"/api/resumes/{rid}/intelligence")
    assert r.status_code == 409 and r.json()["error"]["code"] == "resume_not_ready"
    with container.db.tx() as c:
        c.execute("UPDATE resumes SET status='ready' WHERE id=?", (rid,))
    assert client.get(f"/api/resumes/{rid}/intelligence").status_code == 200
    assert fake.chat_calls == [] and client.get("/api/resumes/999/intelligence").status_code == 404


def test_offline_resume_questions_respect_cloud_consent(client, container, set_id):
    rid = ready_resume(container)
    container.resumes.is_cloud = lambda: True                 # cloud mode on, this resume never consented
    body = {"set_id": None, "config": {"include_bank": False, "max_followups": 0}, "resume_auto": {"resume_id": rid, "count": 3}}
    r = client.post("/api/interviews", json=body)
    assert r.status_code == 409 and r.json()["error"]["code"] == "cloud_consent_required"
    with container.db.tx() as c:
        c.execute("UPDATE resumes SET consent_cloud=1 WHERE id=?", (rid,))
    assert client.post("/api/interviews", json=body).status_code == 201
