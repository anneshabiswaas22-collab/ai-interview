import { describe, expect, it } from "vitest";
import { db } from "../../src/db/kysely";
import { dispatchScore, recordScoreDispatch } from "../../src/jobs/score-outbox";
import { as, createUser, jdInterview, startLive } from "./harness";

async function scoredAnswer() {
  const user = await createUser();
  const interview = await jdInterview(user);
  await startLive(user, interview.id);
  await as(user).post(`/api/interviews/${interview.id}/answers`).send({ round: 0, question: 0, transcript: [{ role: "candidate", text: "I built a small service." }], advance: false }).expect(202);
  const answer = await db.selectFrom("answers").selectAll().where("interview_id", "=", interview.id).executeTakeFirstOrThrow();
  return { user, interview, answer };
}

describe("score dispatch outbox", () => {
  it("rolls back with its transaction and preserves work when the queue is unavailable", async () => {
    const { answer } = await scoredAnswer();
    expect(await db.selectFrom("score_dispatch_outbox").selectAll().where("answer_id", "=", answer.id).execute()).toHaveLength(0);
    await expect(db.transaction().execute(async (trx) => {
      await recordScoreDispatch(trx, answer.id, answer.updated_at);
      throw new Error("rollback");
    })).rejects.toThrow("rollback");
    expect(await db.selectFrom("score_dispatch_outbox").selectAll().where("answer_id", "=", answer.id).execute()).toHaveLength(0);
    await db.transaction().execute((trx) => recordScoreDispatch(trx, answer.id, answer.updated_at));
    await expect(dispatchScore(answer.id, async () => { throw new Error("queue offline"); })).rejects.toThrow("queue offline");
    expect(await db.selectFrom("score_dispatch_outbox").selectAll().where("answer_id", "=", answer.id).execute()).toHaveLength(1);
    const sent: string[] = [];
    await dispatchScore(answer.id, async (id, version) => { sent.push(`${id}:${version}`); });
    expect(sent).toEqual([`${answer.id}:${answer.updated_at.toISOString()}`]);
    expect(await db.selectFrom("score_dispatch_outbox").selectAll().where("answer_id", "=", answer.id).execute()).toHaveLength(0);
  });

  it("does not erase a newer answer while an older version is being queued", async () => {
    const { answer } = await scoredAnswer();
    await db.transaction().execute((trx) => recordScoreDispatch(trx, answer.id, answer.updated_at));
    let entered!: () => void;
    let release!: () => void;
    const started = new Promise<void>((resolve) => { entered = resolve; });
    const gate = new Promise<void>((resolve) => { release = resolve; });
    const dispatch = dispatchScore(answer.id, async () => { entered(); await gate; });
    await started;
    const newer = new Date(answer.updated_at.getTime() + 1000);
    await db.transaction().execute((trx) => recordScoreDispatch(trx, answer.id, newer));
    release();
    await dispatch;
    const row = await db.selectFrom("score_dispatch_outbox").selectAll().where("answer_id", "=", answer.id).executeTakeFirstOrThrow();
    expect(row.answer_version.toISOString()).toBe(newer.toISOString());
    await db.deleteFrom("answers").where("id", "=", answer.id).execute();
    expect(await db.selectFrom("score_dispatch_outbox").selectAll().where("answer_id", "=", answer.id).execute()).toHaveLength(0);
  });
});
