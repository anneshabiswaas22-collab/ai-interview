/**
 * A transactional handoff from Postgres to the existing BullMQ scoring queue. The
 * dispatcher is at-least-once: a crash after enqueue can result in a repeated attempt.
 * Stable job IDs and the scoring handler's answer-version check make retries safe.
 */
import type { Transaction } from "kysely";
import { captureError } from "../core/logger";
import { db } from "../db/kysely";
import type { DB } from "../db/types";
import { enqueue } from "./registry";

type ScoreDispatch = (answerId: string, version: string) => Promise<void>;

/** Call in the same transaction that creates/updates the answer. */
export async function recordScoreDispatch(trx: Transaction<DB>, answerId: string, version: Date): Promise<void> {
  await trx.insertInto("score_dispatch_outbox").values({ answer_id: answerId, answer_version: version })
    .onConflict((oc) => oc.column("answer_id").doUpdateSet({ answer_version: version, created_at: new Date() })).execute();
}

async function enqueueScore(answerId: string, version: string): Promise<void> {
  // BullMQ job IDs may not contain colons; the id is stable for this answer version.
  await enqueue("interview.score", { answerId, version }, { jobId: `score-${answerId}-${new Date(version).getTime()}` });
}

/** Delete a dispatch only after the queue accepts it, and only for that exact version. */
export async function dispatchScore(answerId: string, send: ScoreDispatch = enqueueScore): Promise<boolean> {
  const item = await db.selectFrom("score_dispatch_outbox").selectAll().where("answer_id", "=", answerId).executeTakeFirst();
  if (!item) return false;
  await send(item.answer_id, item.answer_version.toISOString());
  // A newer answer may have replaced this row while the queue call was in flight.
  await db.deleteFrom("score_dispatch_outbox").where("answer_id", "=", item.answer_id).where("answer_version", "=", item.answer_version).execute();
  return true;
}

/** Scheduled worker recovery; a failed queue call leaves its row for the next run. */
export async function dispatchPendingScores(limit = 100): Promise<number> {
  const due = await db.selectFrom("score_dispatch_outbox").select("answer_id").orderBy("created_at").orderBy("answer_id").limit(limit).execute();
  let sent = 0;
  for (const item of due) {
    try { if (await dispatchScore(item.answer_id)) sent++; }
    catch (err) { captureError(err, { where: "score-outbox.dispatch", answerId: item.answer_id }); }
  }
  return sent;
}
