# Open-Weight LLMs, Fine-Tuning and Training Data

**Objective:** eventually own a high-quality interview-specific model adapter, without assuming fine-tuning is automatically better. No training has yet been run for this repository.

## Model approach

1. **Baseline first:** benchmark one quality hosted model and one open-weight model with the same prompts, interview states, rubric and held-out conversations.
2. **Initial fine-tuning candidate:** Qwen3-4B or another *specific, license-verified checkpoint*. Validate model context length, tool/structured-output performance, reasoning mode and serving hardware.
3. **Train only if data and evaluation justify it.** Use supervised multi-turn interviewer demonstrations to teach response style, probes, transition judgment and interview discipline.
4. **RAG for knowledge:** job descriptions, role rubrics, approved technical references and candidate-authorized resume summaries; do not try to memorize an ever-changing knowledge base through SFT.
5. **Separate evaluator:** benchmark independently against expert-reviewed rubrics. Do not train the conversational model to invent definitive competence scores.
6. **Voice remains modular:** STT/LLM/TTS distinct; LLM fine-tuning does not make an end-to-end speech model.

## Data sourcing and permissions

- Seed with original synthetic scenario dialogues, expert-authored rubrics and contributor-created exercises.
- Do not copy premium question libraries, confidential interviews or private resumes.
- Record provenance, consent, license, role, difficulty, competency and version for every example.
- If real user sessions are considered for future training, collect **separate affirmative consent**, allow revocation according to policy, anonymize/curate and document limitations.
- Remove names, contact details, identifiable employer secrets and accidental PII; leakage testing required.

## Example training representation

Store a structured scenario in JSONL; use model-specific chat templates at training time:

\`\`\`json
{
  "id": "backend-cache-001",
  "role": "backend_engineer",
  "level": "mid",
  "scenario": "Cache outage and database overload",
  "history": [
    {"role": "interviewer", "content": "What happens if Redis becomes unavailable?"},
    {"role": "candidate", "content": "The service reads from the database."}
  ],
  "target_response": "That fallback can work. How would you prevent a sudden increase in database traffic from overwhelming it?",
  "skill": "adaptive_follow_up",
  "source": "original"
}
\`\`\`

Include strong, weak, partial, silent, adversarial, multilingual and clarification examples. Training targets should respect interviewer role, boundaries, latency and session budget.

## Data splits

- Train 70–80%; development 10–15%; **held-out test** 10–15% as an initial plan.
- Split by *scenario family/candidate biography and competency template*, not random turns; avoid near-duplicate leakage.
- Freeze evaluation prompts, reviewer guidelines and hidden cases before tuning.
- Prefer hundreds of high-quality multi-turn examples over thousands of noisy examples initially.

## Training pipeline

- Use [Unsloth](https://github.com/unslothai/unsloth) + PEFT/TRL with QLoRA where hardware supports the checkpoint.
- Train on an authorized GPU environment (e.g., Colab with appropriate resources or a rented GPU). **Codex Cloud writes/runs code but has no guaranteed training GPU.**
- Suggested *experiment starting values*, not defaults guaranteed optimal: 4-bit base, LoRA rank 16, alpha 32, learning rate 1e-4, 2–3 epochs, effective batch chosen by GPU memory, sequence length >= target conversation window.
- Log exact base checkpoint revision, tokenizer/chat template, environment, seeds, dataset fingerprint, hyperparameters and training/eval curves.
- Save adapters and manifests, not entire customer data. Verify adapters can load in selected inference runtime; no stale or hidden external provider calls.

## Evaluation before promoting a model

- Follow-up relevance, technical correctness, interview-state adherence, hallucination, response length, repetitiveness, instruction attacks, multilingual suitability.
- Separate deterministic tests from expert blind review; report sample sizes and inter-rater agreement.
- Measure end-to-end token cost, memory, GPU spend, p50/p95 voice/text latency and failure rates.
- Compare base model + excellent prompting, RAG base, SFT model, and when justified DPO candidates on **same** held-out set.
- Stop if benefits are not meaningful or regression exceeds threshold. Roll back via versioned feature flag.

## Serving and model control

- Start through a vendor-neutral/OpenAI-compatible adapter; support hosted models for comparison.
- Deploy quantized inference via vLLM or a compatible server only after evaluating hardware and licensing.
- Version adapters, prompt templates, rubrics and datasets independently; maintain rollback.
- No claims such as "fine-tuned", "92% accurate" or "own trained model" until training and tests actually occurred.

## Artifact targets

\`ml/datasets/\`: samples, provenance and quality manifest (non-sensitive only).
\`ml/training/\`: training configuration, reproducible script and Colab notebook.
\`ml/evaluation/\`: fixture set, automatic checks, blinded human rating guide, model-comparison report.
\`docs/model_cards/\`: checkpoint, intended uses, limits, hardware, license and results.

See [quality and tests](QUALITY_AND_TESTING.md), [license audit](LICENSE_AUDIT.md).
