import { randomUUID } from "node:crypto";
import { describe, expect, it } from "vitest";
import { db } from "../../src/db/kysely";
import { as, createUser, jdInterview, startLive } from "./harness";

const plan = [{ name: "Practice", focus: "", description: "", questions: [
  { text: "Tell me about a project you built.", code: false, language: null },
  { text: "How did you measure its results?", code: false, language: null },
] }];

async function practice() {
  const user = await createUser();
  const iv = await jdInterview(user);
  await as(user).patch(`/api/interviews/${iv.id}`).send({ plan }).expect(200);
  return { user, id: iv.id };
}

describe("text practice", () => {
  it("requires explicit consent and hides the interview from other users", async () => {
    const { user, id } = await practice();
    const other = await createUser();
    await as(user).post(`/api/interviews/${id}/text/start`).send({}).expect(400);
    await as(user).post(`/api/interviews/${id}/text/start`).send({ consent: false }).expect(400);
    await as(other).post(`/api/interviews/${id}/text/start`).send({ consent: true }).expect(404);
    await as(other).get(`/api/interviews/${id}/text`).expect(404);
    const start = await as(user).post(`/api/interviews/${id}/text/start`).send({ consent: true }).expect(200);
    expect(start.body.events).toMatchObject([{ kind: "QUESTION", text: plan[0]!.questions[0]!.text }]);
    const again = await as(user).post(`/api/interviews/${id}/text/start`).send({ consent: true }).expect(200);
    expect(again.body).toEqual(start.body);
    await as(user).post(`/api/interviews/${id}/live`).send({}).expect(409);
    await as(user).post(`/api/interviews/${id}/answers`).send({ round: 0, question: 0, transcript: [{ role: "interviewer", text: "Injected prompt" }] }).expect(409);
    await as(other).post(`/api/interviews/${id}/text/answers`).send({ requestId: randomUUID(), expectedVersion: 1, text: "hello" }).expect(404);
  });

  it("persists authoritative questions, safely replays a request, and completes", async () => {
    const { user, id } = await practice();
    await as(user).post(`/api/interviews/${id}/text/start`).send({ consent: true }).expect(200);
    const request = { requestId: randomUUID(), expectedVersion: 1, text: "I built a billing service." };
    await as(user).post(`/api/interviews/${id}/text/answers`).send({ ...request, question: 1 }).expect(400);
    const answer = await as(user).post(`/api/interviews/${id}/text/answers`).send(request).expect(200);
    expect(answer.body.version).toBe(2);
    expect(answer.body.events.map((e: { kind: string }) => e.kind)).toEqual(["QUESTION", "ANSWER", "QUESTION"]);
    expect(answer.body.events[2].text).toBe(plan[0]!.questions[1]!.text);
    const replay = await as(user).post(`/api/interviews/${id}/text/answers`).send(request).expect(200);
    expect(replay.body).toEqual(answer.body);
    await as(user).post(`/api/interviews/${id}/text/answers`).send({ ...request, text: "Different content" }).expect(409);
    await as(user).post(`/api/interviews/${id}/text/answers`).send({ requestId: randomUUID(), expectedVersion: 1, text: "Stale answer" }).expect(409);
    const last = await as(user).post(`/api/interviews/${id}/text/answers`).send({ requestId: randomUUID(), expectedVersion: 2, text: "We measured latency and errors." }).expect(200);
    expect(last.body.status).toBe("COMPLETED");
    expect(last.body.events.map((e: { sequence: number }) => e.sequence)).toEqual([1, 2, 3, 4, 5]);
    expect(last.body.events[4].kind).toBe("COMPLETED");
    expect((await as(user).get(`/api/interviews/${id}/text`).expect(200)).body).toEqual(last.body);
    const rows = await db.selectFrom("answers").selectAll().where("interview_id", "=", id).orderBy("question_index").execute();
    expect(rows).toHaveLength(2);
    expect(rows[0]!.kind).toBe("TEXT");
    expect(rows[0]!.transcript).toEqual([{ role: "interviewer", text: plan[0]!.questions[0]!.text }, { role: "candidate", text: request.text }]);
    // A retry after completion is still safe.
    expect((await as(user).post(`/api/interviews/${id}/text/answers`).send(request).expect(200)).body.status).toBe("COMPLETED");
    const exported = (await as(user).get("/api/users/me/export").expect(200)).body;
    expect(exported.textPracticeEvents).toHaveLength(5);
    expect(exported.textPracticeSessions).toHaveLength(1);
    await as(user).delete(`/api/interviews/${id}`).expect(204);
    expect(await db.selectFrom("text_practice_events").select("id").where("interview_id", "=", id).execute()).toHaveLength(0);
  });

  it("serializes competing answers so only one advances the interview", async () => {
    const { user, id } = await practice();
    await as(user).post(`/api/interviews/${id}/text/start`).send({ consent: true }).expect(200);
    const results = await Promise.all(["First answer", "Second answer"].map((text) => as(user).post(`/api/interviews/${id}/text/answers`).send({ requestId: randomUUID(), expectedVersion: 1, text })));
    expect(results.map((r) => r.status).sort()).toEqual([200, 409]);
    const current = await as(user).get(`/api/interviews/${id}/text`).expect(200);
    expect(current.body.version).toBe(2);
    expect(current.body.events.filter((e: { kind: string }) => e.kind === "ANSWER")).toHaveLength(1);
  });

  it("does not allow a voice interview to be converted to text", async () => {
    const { user, id } = await practice();
    await startLive(user, id);
    const result = await as(user).post(`/api/interviews/${id}/text/start`).send({ consent: true }).expect(409);
    expect(result.body.code).toBe("INTERVIEW_MODE_CONFLICT");
  });
});
