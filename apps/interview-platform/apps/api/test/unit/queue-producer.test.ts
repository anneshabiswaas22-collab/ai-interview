import { createServer } from "node:net";
import { describe, expect, it } from "vitest";
import { config } from "../../src/core/config";
import { closeQueues, enqueue } from "../../src/jobs/registry";

describe("queue producer", () => {
  it("fails promptly when Redis is unavailable and allows a later attempt", async () => {
    // Reserve an unused local port, then close it before trying to connect.
    const server = createServer();
    await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
    const address = server.address();
    if (!address || typeof address === "string") throw new Error("No test port");
    await new Promise<void>((resolve, reject) => server.close((err) => err ? reject(err) : resolve()));
    const oldMode = config.JOBS_MODE;
    const oldUrl = config.REDIS_URL;
    config.JOBS_MODE = "queue";
    config.REDIS_URL = `redis://127.0.0.1:${address.port}`;
    try {
      const started = Date.now();
      await expect(enqueue("interview.score", { answerId: "test-answer", version: new Date().toISOString() })).rejects.toThrow();
      await expect(enqueue("interview.score", { answerId: "test-answer", version: new Date().toISOString() })).rejects.toThrow();
      expect(Date.now() - started).toBeLessThan(5_000);
    } finally {
      await closeQueues();
      config.JOBS_MODE = oldMode;
      config.REDIS_URL = oldUrl;
    }
  }, 10_000);
});
