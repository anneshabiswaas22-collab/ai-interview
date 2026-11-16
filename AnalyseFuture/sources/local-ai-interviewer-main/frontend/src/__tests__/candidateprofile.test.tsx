import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { CandidateIntel } from "../types";

const sk = (name: string, confidence: "high" | "medium" | "low") => ({ name, category: "Tools", listed: confidence !== "medium", used_in: confidence === "low" ? [] : ["Data engineer"], sources: [{ section: "Skills", label: "Skills", line: 3, status: "verified" as const }], aliases: [], confidence, confidence_reason: `${name} reason` });
const intel = { resume_id: 1, resume_name: "CV", skills: [sk("Python", "high"), sk("Airflow", "high"), sk("Spark", "medium"), sk("COBOL", "low")],
  projects: [], experience: { roles: 1, years: 2, gaps: [], current: [] }, relationships: [], clarifications: [], notes: [], injection_warnings: [], suggested_questions: [], practice_history: [], unexplored: [],
  extraction: { checked: 0, verified: 0, partial: 0, not_found: 0, score: null, confidence: "high", not_found_examples: [] } } as unknown as CandidateIntel;
vi.mock("../api", () => ({ ApiError: class extends Error {}, resumesApi: { intelligence: () => Promise.resolve(intel) } }));

import CandidateProfile from "../components/CandidateProfile";

describe("CandidateProfile skill groups", () => {
  it("shows High confidence open and the other groups folded, with counts, and every skill keeps its details", async () => {
    render(<CandidateProfile id={1} version={1} onEdit={() => {}} />);
    const high = await screen.findByRole("button", { name: /High confidence/ });
    const medium = screen.getByRole("button", { name: /Medium confidence/ }), listed = screen.getByRole("button", { name: /Listed only/ });
    expect(high).toHaveAttribute("aria-expanded", "true"); expect(medium).toHaveAttribute("aria-expanded", "false"); expect(listed).toHaveAttribute("aria-expanded", "false");
    expect(high).toHaveTextContent("2"); expect(medium).toHaveTextContent("1"); expect(listed).toHaveTextContent("1");
    expect(screen.getByText("Python")).toBeVisible(); expect(screen.getByText("Python reason")).toBeVisible();
    expect(screen.getByText("Spark")).not.toBeVisible(); expect(screen.getByText("COBOL")).not.toBeVisible();
    fireEvent.click(medium);
    expect(medium).toHaveAttribute("aria-expanded", "true"); expect(screen.getByText("Spark")).toBeVisible();
    expect(document.getElementById(medium.getAttribute("aria-controls")!)).toContainElement(screen.getByText("Spark"));
    fireEvent.click(high); await waitFor(() => expect(screen.getByText("Python")).not.toBeVisible());
  });
});
