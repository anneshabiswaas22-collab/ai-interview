"""Curated technical implications of technologies and engineering activities named on a resume.

Each entry lists questions an experienced interviewer would ask someone who claims to have used the technology: how it fails, how it
is operated, why it was chosen, what it costs. `{ctx}` is replaced by the resume context (a project name or "your role at Acme"),
so every question stays tied to the claim it came from. Questions are (text, difficulty, kind, what a credible answer covers).

This is deliberately a reviewed, static list: it works offline, costs no model call and never invents facts about the candidate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

Q = tuple[str, str, str, str]


@dataclass(frozen=True)
class Tech:
    name: str
    category: str
    pattern: re.Pattern
    questions: tuple[Q, ...]


def _t(name: str, category: str, aliases: str, *questions: Q, case_sensitive: bool = False) -> Tech:
    """Ambiguous names (React, Node) are matched case-sensitively so "React to customer escalations" is not React."""
    flags = 0 if case_sensitive else re.I
    return Tech(name, category, re.compile(rf"(?<![A-Za-z0-9])({aliases})(?![A-Za-z0-9])", flags), questions)


TECHS: list[Tech] = [
    _t("Apache Airflow", "Orchestration", r"airflow",
       ("How were the Airflow DAGs in {ctx} structured, and how were failed task runs retried and alerted on?", "medium", "failure_handling",
        "Retries with backoff, alerting/SLAs, task granularity, what happened to downstream tasks."),
       ("How did you make the Airflow tasks in {ctx} idempotent so that a re-run or backfill could not duplicate data?", "hard", "data_integrity",
        "Partition-scoped writes, overwrite/merge semantics, execution-date parameters, upserts."),
       ("Why was Airflow chosen to orchestrate {ctx} rather than cron or another orchestrator, and what did it cost you operationally?", "medium", "decision_tradeoff",
        "Dependencies, scheduling, observability vs. operational overhead of the scheduler/workers.")),
    _t("Snowflake", "Data warehouse", r"snowflake",
       ("How did you keep Snowflake warehouse costs under control in {ctx}?", "medium", "performance_cost",
        "Warehouse sizing, auto-suspend/resume, query profiling, clustering, avoiding full scans."),
       ("How was incremental loading into Snowflake implemented in {ctx}, and how were duplicates prevented?", "hard", "data_integrity",
        "Watermarks or streams, MERGE on keys, staging tables, deduplication rules.")),
    _t("Apache Spark", "Data processing", r"spark|pyspark",
       ("What performance problems did you hit with Spark in {ctx} (skew, shuffles, small files) and how did you fix them?", "hard", "performance_cost",
        "Partitioning, broadcast joins, salting skewed keys, caching, file compaction."),
       ("How did you test and validate the Spark jobs in {ctx} before they ran on production data?", "medium", "testing",
        "Unit tests on transformations, sample data, data-quality checks, schema validation.")),
    _t("Apache Kafka", "Streaming", r"kafka",
       ("What delivery guarantees did the Kafka consumers in {ctx} provide, and how did you handle duplicate or out-of-order messages?", "hard", "data_integrity",
        "At-least-once vs exactly-once, idempotent processing, offsets and commits, keys and ordering per partition."),
       ("How did you size partitions and monitor consumer lag for Kafka in {ctx}?", "medium", "scalability",
        "Throughput needs, consumer-group parallelism, lag alerts, rebalancing.")),
    _t("dbt", "Data transformation", r"dbt",
       ("How did you structure and test the dbt models in {ctx}?", "medium", "testing",
        "Staging/marts layering, schema and data tests, incremental models, documentation.")),
    _t("PostgreSQL", "Database", r"postgres(?:ql)?",
       ("How did you find and fix slow queries in PostgreSQL in {ctx}?", "medium", "performance_cost",
        "EXPLAIN ANALYZE, indexes, query rewrites, vacuum/statistics, connection pooling."),
       ("How were schema migrations rolled out on PostgreSQL in {ctx} without downtime or data loss?", "hard", "deployment",
        "Backwards-compatible steps, migration tooling, locking concerns, backfills, rollback.")),
    _t("MySQL", "Database", r"mysql",
       ("How did you design indexes for the main MySQL queries in {ctx}, and how did you verify they were used?", "medium", "performance_cost",
        "Selective/composite indexes, EXPLAIN, write overhead, covering indexes.")),
    _t("MongoDB", "Database", r"mongo(?:db)?",
       ("Why was MongoDB a good fit for the data in {ctx}, and how did you model documents versus references?", "medium", "decision_tradeoff",
        "Access patterns, embedding vs referencing, consistency needs, indexes.")),
    _t("Redis", "Cache", r"redis",
       ("How did you keep the Redis cache in {ctx} consistent with the source of truth, and what happened when it was unavailable?", "hard", "failure_handling",
        "Invalidation strategy, TTLs, cache-aside, stampede protection, graceful degradation.")),
    _t("Elasticsearch", "Search", r"elastic\s?search|opensearch",
       ("How did you design the index mappings and relevance tuning for search in {ctx}?", "medium", "architecture",
        "Analyzers, mappings, reindexing strategy, relevance testing.")),
    _t("Docker", "Containers", r"docker",
       ("How did you keep the Docker images in {ctx} small, secure and reproducible?", "medium", "security",
        "Multi-stage builds, pinned base images, non-root user, vulnerability scanning, layer caching.")),
    _t("Kubernetes", "Orchestration", r"kubernetes|k8s|eks|gke|aks",
       ("How were deployments, health checks and autoscaling configured on Kubernetes in {ctx}?", "hard", "deployment",
        "Rolling updates, readiness/liveness probes, resource requests/limits, HPA, rollback.")),
    _t("Terraform", "Infrastructure as code", r"terraform",
       ("How did you manage Terraform state and review infrastructure changes safely in {ctx}?", "medium", "deployment",
        "Remote state with locking, plan reviews, modules, environments, drift.")),
    _t("AWS", "Cloud", r"aws|amazon web services|ec2|s3|aws lambda|dynamodb|cloudwatch",
       ("Which AWS services did {ctx} rely on, and how did you handle permissions (IAM) and cost?", "medium", "security",
        "Least-privilege IAM roles, secrets handling, cost monitoring, service choices and why.")),
    _t("Google Cloud", "Cloud", r"gcp|google cloud|bigquery|cloud run|pub/?sub",
       ("How did you design and control the cost of the Google Cloud components in {ctx}?", "medium", "performance_cost",
        "Service choices, partitioning in BigQuery, quotas, budgets and monitoring.")),
    _t("Azure", "Cloud", r"azure",
       ("Which Azure services did {ctx} depend on, and how did you monitor and secure them?", "medium", "security",
        "Managed identities, Key Vault, monitoring/alerting, network rules.")),
    _t("React", "Frontend", r"React(?:\.js|JS)|React(?!\s+(?:to|quickly|promptly|swiftly|calmly|immediately)\b)|react\.js|reactjs",
       ("How was state managed in the React application in {ctx}, and how did you avoid unnecessary re-renders?", "medium", "architecture",
        "Local vs global state, memoisation, data fetching/caching, profiling."),
       ("How did you test the React components in {ctx}?", "medium", "testing",
        "Component tests, user-event style tests, mocking APIs, end-to-end coverage."), case_sensitive=True),
    _t("Node.js", "Backend", r"[Nn]ode\.js|[Nn]ode[Jj][Ss]|Express(?:\.js)?|express\.js",
       ("How did you handle errors and long-running work in the Node.js services in {ctx} without blocking the event loop?", "hard", "failure_handling",
        "Async error handling, worker threads/queues, timeouts, graceful shutdown."), case_sensitive=True),
    _t("FastAPI / Flask / Django", "Backend", r"fastapi|flask|django",
       ("How was the Python web API in {ctx} structured, validated and secured?", "medium", "architecture",
        "Request validation, authentication/authorisation, error handling, layering, tests.")),
    _t("REST APIs", "APIs", r"rest(?:ful)?\s?apis?|rest services",
       ("How did you version the APIs in {ctx} and keep them backward compatible for existing clients?", "medium", "decision_tradeoff",
        "Versioning scheme, additive changes, deprecation, contract tests."),
       ("How did the APIs in {ctx} handle retries, timeouts and duplicate requests?", "hard", "failure_handling",
        "Idempotency keys, timeouts, retry with backoff, rate limits.")),
    _t("GraphQL", "APIs", r"graphql",
       ("How did you prevent expensive or N+1 GraphQL queries in {ctx}?", "hard", "performance_cost",
        "DataLoader/batching, query depth/complexity limits, caching.")),
    _t("Microservices", "Architecture", r"micro-?services?",
       ("How did the microservices in {ctx} communicate, and how did you handle a downstream service failing?", "hard", "failure_handling",
        "Sync vs async calls, timeouts, circuit breakers, retries, eventual consistency, tracing.")),
    _t("CI/CD", "Delivery", r"ci/?cd|jenkins|github actions|gitlab ci|circleci",
       ("What did the CI/CD pipeline in {ctx} check before a change reached production, and how were releases rolled back?", "medium", "deployment",
        "Tests, linting, security scans, staged rollout, rollback mechanism.")),
    _t("Pandas", "Data analysis", r"pandas",
       ("What did you do when the pandas processing in {ctx} became too slow or ran out of memory?", "medium", "performance_cost",
        "Vectorisation, dtypes, chunking, moving to a database or distributed engine.")),
    _t("scikit-learn", "Machine learning", r"scikit-?learn|sklearn",
       ("How did you validate the scikit-learn models in {ctx} and guard against data leakage?", "hard", "testing",
        "Train/validation/test splits, cross-validation, pipelines fitting only on training data, metrics choice.")),
    _t("TensorFlow / PyTorch", "Deep learning", r"tensorflow|pytorch|keras",
       ("How did you decide the model in {ctx} was good enough to ship, and how was it monitored afterwards?", "hard", "testing",
        "Offline metrics vs business metric, baselines, error analysis, drift monitoring.")),
    _t("LLMs", "Machine learning", r"llms?|gpt(?:-\d)?|langchain|retrieval.augmented generation|large language models?|openai|ollama",
       ("How did you evaluate the quality of the LLM outputs in {ctx}, and how did you handle wrong or unsafe answers?", "hard", "testing",
        "Evaluation sets, human review, guardrails, grounding/citations, prompt-injection defences.")),
    _t("Tableau / Power BI", "Analytics", r"tableau|power\s?bi|looker",
       ("How did you make sure the numbers on the dashboards in {ctx} were correct and trusted?", "medium", "data_integrity",
        "Reconciliation with source, metric definitions, data-quality checks, refresh monitoring.")),
]

# Engineering activities (not tools) that carry their own implications.
ACTIVITIES: list[Tech] = [
    _t("ETL / data pipelines", "Data engineering", r"etl|elt|data pipelines?|etl pipelines?|data ingestion|ingestion pipelines?",
       ("How was the reliability of the pipeline in {ctx} monitored, and how would you have known it silently produced wrong data?", "hard", "failure_handling",
        "Freshness/volume/quality checks, alerting, reconciliation, lineage."),
       ("How did the pipeline in {ctx} handle late-arriving or changed source data?", "hard", "data_integrity",
        "Watermarks, reprocessing windows, CDC, upserts, backfills.")),
    _t("Migration", "Engineering", r"migrat(?:ed|ion|ing)",
       ("How did you plan and verify the migration in {ctx} so that nothing was lost or broken?", "medium", "failure_handling",
        "Dry runs, dual-writes or shadow reads, reconciliation, rollback plan, cut-over.")),
    _t("Performance optimisation", "Engineering", r"optimi[sz](?:ed|ation|ing)|latency|throughput",
       ("How did you find the bottleneck behind the optimisation in {ctx}, and how did you prove the improvement?", "medium", "performance_cost",
        "Profiling/measurement first, the specific change, before/after numbers under comparable load.")),
    _t("Real-time systems", "Engineering", r"real-?time|streaming|low-latency",
       ("What latency target did the real-time part of {ctx} have, and what happened under a traffic spike?", "hard", "scalability",
        "Explicit SLOs, back-pressure, buffering, autoscaling, degradation strategy.")),
    _t("Machine learning models", "Machine learning", r"ml models?|machine learning models?|classifiers?|prediction models?|recommendation (?:engine|system|model)s?|forecasting models?",
       ("What baseline did you compare the model in {ctx} against, and which metric told you it was better?", "medium", "decision_tradeoff",
        "Simple baseline, metric aligned with the business goal, statistical confidence.")),
]


@dataclass(frozen=True)
class Hit:
    tech: Tech
    activity: bool


def detect(text: str) -> list[Hit]:
    """Technologies and activities mentioned in a piece of resume text, in catalogue order, each once."""
    out: list[Hit] = []
    for t in TECHS:
        if t.pattern.search(text or ""):
            out.append(Hit(t, False))
    for a in ACTIVITIES:
        if a.pattern.search(text or ""):
            out.append(Hit(a, True))
    return out


def canonical(skill: str) -> tuple[str, str]:
    """(canonical name, category) of a skill; unknown skills keep their own name and category ''."""
    s = (skill or "").strip()
    for t in TECHS:
        m = t.pattern.fullmatch(s) if s else None
        if m or (t.pattern.search(s) and len(s) <= len(t.name) + 6):
            return t.name, t.category
    return s, ""
