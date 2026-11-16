import { afterEach, describe, expect, it, vi } from "vitest";
import { hasAdaptive, readTab, reportTabs, saveTab } from "../reportTabs";

const none = { adaptive: null, resume_coverage: null, resume_claims: [] } as never;
afterEach(() => { sessionStorage.clear(); vi.restoreAllMocks(); });

describe("report tabs", () => {
  it("hides the Adaptive tab unless there is a timeline or resume coverage / claims", () => {
    expect(reportTabs(none)).toEqual(["overview", "questions", "skills"]);
    expect(hasAdaptive({ ...(none as object), adaptive: { events: [] } } as never)).toBe(true);
    expect(hasAdaptive({ ...(none as object), resume_coverage: { claims_total: 0 } } as never)).toBe(false);
    expect(hasAdaptive({ ...(none as object), resume_coverage: { claims_total: 3 } } as never)).toBe(true);
    expect(hasAdaptive({ ...(none as object), resume_claims: [{}] } as never)).toBe(true);
    expect(reportTabs({ ...(none as object), resume_claims: [{}] } as never)).toContain("adaptive");
  });
  it("remembers the tab per report and ignores a tab the report does not have", () => {
    const tabs = reportTabs(none);
    expect(readTab(5, tabs)).toBe("overview");
    saveTab(5, "skills"); expect(readTab(5, tabs)).toBe("skills"); expect(readTab(6, tabs)).toBe("overview");
    saveTab(5, "adaptive"); expect(readTab(5, tabs)).toBe("overview");
  });
  it("works when storage is blocked", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    expect(() => saveTab(1, "skills")).not.toThrow();
    expect(readTab(1, reportTabs(none))).toBe("overview");
  });
});
