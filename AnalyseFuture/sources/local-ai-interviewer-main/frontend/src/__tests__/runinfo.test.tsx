import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import RunInfo, { WhyThisQuestion } from "../components/RunInfo";
import type { InterviewState } from "../types";

const st = (over: Partial<InterviewState>) => ({ status: "in_progress", current: { item: { topic: "SQL" } }, ...over }) as unknown as InterviewState;

describe("RunInfo", () => {
  it("renders nothing for a fixed interview without a time limit", () => {
    const { container } = render(<RunInfo st={st({ mode: "fixed", adaptive: null })} remaining={null} />);
    expect(container).toBeEmptyDOMElement();
  });
  it("shows only the clock for a fixed interview with a limit", () => {
    render(<RunInfo st={st({ mode: "fixed", adaptive: null })} remaining={125} />);
    expect(screen.getByRole("timer")).toHaveTextContent("02:05");
    expect(screen.queryByText("Strategy")).toBeNull();
  });
  it("shows topic, level, target and strategy for an adaptive interview", () => {
    render(<RunInfo st={st({ mode: "adaptive", adaptive: { strategy: "deep_dive", level: "advanced", target_difficulty: "hard", focus_topic: "Joins" } as never })} remaining={null} />);
    const box = screen.getByTestId("runinfo");
    expect(box).toHaveTextContent("SQL"); expect(box).toHaveTextContent("Advanced"); expect(box).toHaveTextContent("aiming for hard"); expect(box).toHaveTextContent("Deep dive"); expect(box).toHaveTextContent("Joins");
    expect(screen.queryByRole("timer")).toBeNull();
  });
  it("says when time is up and renders the reason only when present", () => {
    render(<><RunInfo st={st({ mode: "fixed" })} remaining={0} /><WhyThisQuestion reason="Moving to SQL." /></>);
    expect(screen.getByText(/Time is up/)).toBeInTheDocument();
    expect(screen.getByTestId("why-question")).toHaveTextContent("Why this question: Moving to SQL.");
    const { container } = render(<WhyThisQuestion reason={null} />);
    expect(container).toBeEmptyDOMElement();
  });
  it("turns the clock to the warning colour in the last five minutes, and not before", () => {
    const { rerender } = render(<RunInfo st={st({ mode: "fixed" })} remaining={301} />);
    expect(screen.getByRole("timer").closest(".time")).not.toHaveClass("warn");
    rerender(<RunInfo st={st({ mode: "fixed" })} remaining={300} />);
    expect(screen.getByRole("timer").closest(".time")).toHaveClass("warn");
    rerender(<RunInfo st={st({ mode: "fixed" })} remaining={59} />);
    expect(screen.getByRole("timer").closest(".time")).toHaveClass("warn");
  });
  it("styles the time-is-up text with the same warning colour class", () => {
    render(<RunInfo st={st({ mode: "fixed" })} remaining={0} />);
    expect(screen.getByText(/Time is up/)).toHaveClass("timeup");
  });
});
