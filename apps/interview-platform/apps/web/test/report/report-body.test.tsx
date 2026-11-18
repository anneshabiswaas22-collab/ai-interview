import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { AnswerFeedback, InterviewReport } from "@open-conversation/types";
import { ReportBody } from "@/components/report/report-body";

function report(feedback: AnswerFeedback): InterviewReport {
  return {
    interview: {
      id: "interview-1",
      title: "Practice",
      source: "JOB_DESCRIPTION",
      status: "COMPLETED",
      company: null,
      role: "Software engineer",
      domain: "Engineering",
      overallScore: null,
      questionCount: 1,
      answeredCount: 1,
      createdAt: "2026-11-18T00:00:00Z",
      completedAt: "2026-11-18T00:01:00Z",
    },
    candidateName: "Test candidate",
    domainRating: 70,
    communicationRating: null,
    overallRating: null,
    voiceSeconds: 0,
    rounds: [
      {
        name: "Project discussion",
        focus: "Reasoning",
        domainRating: 70,
        communicationRating: null,
        overallRating: null,
        questionCount: 1,
        answeredCount: 1,
      },
    ],
    questions: [
      {
        round: 0,
        question: 0,
        text: "How did you improve reliability?",
        code: false,
        answer: {
          round: 0,
          question: 0,
          kind: "TEXT",
          status: "SCORED",
          evaluationSource: "simulated",
          domainRating: 70,
          communicationRating: null,
          feedback,
          updatedAt: "2026-11-18T00:01:00Z",
        },
        transcript: null,
        submittedCode: null,
      },
    ],
    proctoring: null,
  };
}

const legacyFeedback: AnswerFeedback = {
  strengths: ["Legacy strength"],
  weaknesses: ["Legacy weakness"],
  suggestions: ["Legacy suggestion"],
  analysis: "Legacy analysis",
  correctedSnippet: null,
};

const feedback: AnswerFeedback = {
  ...legacyFeedback,
  textEvidence: {
    rubricVersion: "text-practice-v1",
    criteria: [
      {
        criterionId: "domain",
        score: 70,
        confidence: "low",
        evidence: [{ eventId: "answer-1", quote: "I added retry limits." }],
        observations: [
          {
            kind: "strength",
            text: "Describes a concrete reliability change.",
            evidenceIndexes: [0],
          },
        ],
      },
      {
        criterionId: "communication",
        score: null,
        confidence: "insufficient",
        evidence: [],
        observations: [],
      },
    ],
  },
};

async function openQuestion() {
  const row = screen.getByTestId("report-question-0-0");
  await userEvent.click(within(row).getByRole("button"));
  return row;
}

describe("ReportBody evidence feedback", () => {
  it("links each observation to its exact saved answer quotation and preserves demo labels", async () => {
    render(<ReportBody report={report(feedback)} />);
    expect(screen.getByText(/Some feedback is simulated/)).toBeVisible();
    const row = await openQuestion();
    expect(within(row).getByRole("button")).toHaveAttribute("aria-expanded", "true");
    expect(within(row).getByText(/Simulated demo feedback/)).toBeVisible();
    expect(within(row).getByText(/Describes a concrete reliability change/)).toBeVisible();
    const link = within(row).getByRole("link", { name: "Evidence 1" });
    const target = document.getElementById(link.getAttribute("href")!.slice(1));
    expect(target).not.toBeNull();
    expect(target).toHaveTextContent("Answer event answer-1");
    expect(within(target!).getByRole("blockquote")).toHaveTextContent("I added retry limits.");
    expect(within(row).getByText(/Score: 70 \/ 100/)).toBeVisible();
    expect(
      within(row).getByText(/Confidence is reported by the evaluator and is not calibrated/)
    ).toBeVisible();
    expect(within(row).queryByText("Legacy strength")).not.toBeInTheDocument();
  });

  it("shows insufficient evidence and n/a without displaying a fabricated score", async () => {
    render(<ReportBody report={report(feedback)} />);
    const row = await openQuestion();
    expect(within(row).getByRole("heading", { name: "Written communication" })).toBeVisible();
    expect(within(row).getByText(/Insufficient evidence to score/)).toBeVisible();
    expect(within(row).getByRole("button")).toHaveTextContent("Communication n/a");
    expect(within(row).getByRole("button")).not.toHaveTextContent("null");
    expect(within(row).queryByText(/Score: 0 \/ 100/)).not.toBeInTheDocument();
  });

  it("renders quoted markup and model observations as plain text", async () => {
    const malicious = structuredClone(feedback);
    malicious.textEvidence!.criteria[0]!.evidence[0]!.quote = '<img src=x onerror="alert(1)">';
    malicious.textEvidence!.criteria[0]!.observations[0]!.text = "<script>alert(1)</script>";
    const { container } = render(<ReportBody report={report(malicious)} />);
    const row = await openQuestion();
    expect(within(row).getByText('<img src=x onerror="alert(1)">')).toBeVisible();
    expect(within(row).getByText("<script>alert(1)</script>", { exact: false })).toBeVisible();
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("script")).toBeNull();
  });

  it("keeps legacy feedback readable when no evidence record is available", async () => {
    render(<ReportBody report={report(legacyFeedback)} />);
    const row = await openQuestion();
    for (const item of [
      "Legacy analysis",
      "Legacy strength",
      "Legacy weakness",
      "Legacy suggestion",
    ]) {
      expect(within(row).getByText(item)).toBeVisible();
    }
    expect(
      within(row).queryByRole("region", { name: "Written answer evidence" })
    ).not.toBeInTheDocument();
  });
});
