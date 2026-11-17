import { act, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { AuthResult } from "@open-conversation/types";
import { me } from "../fixtures";

const refreshSession = vi.fn();
vi.mock("@/lib/api", () => ({
  api: () => ({ refreshSession }),
  onSessionEnded: () => () => undefined,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/verify-email",
}));

import { AuthProvider, useAuth } from "@/lib/auth";
import { session } from "@/lib/session";

const verifiedSession: AuthResult = {
  accessToken: "newly-verified-session",
  expiresIn: 3600,
  user: me,
};

function Status() {
  const { status, user } = useAuth();
  return (
    <p>
      {status}:{user?.email ?? "none"}
    </p>
  );
}

function mount() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <AuthProvider>
        <Status />
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe("AuthProvider boot refresh", () => {
  beforeEach(() => {
    session.clear();
    refreshSession.mockReset();
  });

  it("keeps an accepted verification session when the older cookie-less refresh returns empty", async () => {
    let resolve!: (value: null) => void;
    refreshSession.mockReturnValue(
      new Promise<null>((done) => {
        resolve = done;
      })
    );
    mount();
    expect(refreshSession).toHaveBeenCalledTimes(1);

    act(() => session.apply(verifiedSession));
    expect(screen.getByText("signed-in:ada@example.org")).toBeInTheDocument();
    await act(async () => resolve(null));

    expect(session.getToken()).toBe(verifiedSession.accessToken);
    expect(screen.getByText("signed-in:ada@example.org")).toBeInTheDocument();
  });

  it("keeps a newer accepted session when the initial refresh fails on the network", async () => {
    let reject!: (reason: Error) => void;
    refreshSession.mockReturnValue(
      new Promise<null>((_, fail) => {
        reject = fail;
      })
    );
    mount();
    act(() => session.apply(verifiedSession));

    await act(async () => reject(new Error("network unavailable")));

    expect(session.getToken()).toBe(verifiedSession.accessToken);
    expect(screen.getByText("signed-in:ada@example.org")).toBeInTheDocument();
  });

  it("clears an unchanged expired session when the refresh returns empty", async () => {
    session.apply(verifiedSession);
    refreshSession.mockResolvedValue(null);
    mount();
    expect(await screen.findByText("signed-out:none")).toBeInTheDocument();
    expect(session.getToken()).toBeNull();
  });
});
