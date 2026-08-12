import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { QADetail, QAList } from "@/features/qas/qa-display";
import type { QARecord } from "@/features/qas/qa-types";

const unansweredQA: QARecord = {
  id: "qa-id",
  asked_by: "family-id",
  asked_by_display_name: "Family User",
  question: "When is the next update?",
  answer: null,
  answered_by: null,
  answered_by_display_name: null,
  status: "unanswered",
  answered_at: null,
  created_at: "2026-07-27T00:00:00Z",
  updated_at: "2026-07-27T00:00:00Z",
};

describe("QA display", () => {
  it("shows an unanswered state without null actor or time text", () => {
    render(<QADetail qa={unansweredQA} />);

    expect(screen.getByText("待回答")).toBeInTheDocument();
    expect(screen.getByText("这个问题正在等待回答。")).toBeInTheDocument();
    expect(screen.queryByText(/null/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "回答" })).not.toBeInTheDocument();
  });

  it("shows one complete current answer with its Owner actor", () => {
    render(
      <QADetail
        qa={{
          ...unansweredQA,
          answer: "The update is ready.",
          answered_by: "owner-id",
          answered_by_display_name: "Owner User",
          status: "answered",
          answered_at: "2026-07-27T01:00:00Z",
        }}
      />,
    );

    expect(screen.getByText("已回答")).toBeInTheDocument();
    expect(screen.getByText("The update is ready.")).toBeInTheDocument();
    expect(screen.getByText(/Owner User 回答于/)).toBeInTheDocument();
  });

  it("shows the answer time only for answered list items", () => {
    render(
      <QAList
        detailBasePath="/family/qas"
        listPath="/family/qas"
        page={{
          items: [
            unansweredQA,
            {
              ...unansweredQA,
              id: "answered-qa-id",
              question: "What happened?",
              answer: "Everything is on schedule.",
              answered_by: "owner-id",
              answered_by_display_name: "Owner User",
              status: "answered",
              answered_at: "2026-07-27T01:00:00Z",
            },
          ],
          total: 2,
          offset: 0,
          limit: 20,
        }}
      />,
    );

    expect(screen.getByRole("link", { name: /When is the next update/ })).toHaveAttribute(
      "href",
      "/family/qas/qa-id",
    );
    expect(screen.getByRole("link", { name: /What happened/ })).toHaveAttribute(
      "href",
      "/family/qas/answered-qa-id",
    );
    expect(screen.getAllByText(/Family User/)).toHaveLength(2);
    expect(screen.getByText(/回答于/)).toBeInTheDocument();
    expect(screen.getAllByText(/回答于/)).toHaveLength(1);
    expect(screen.getByText("待回答")).toHaveClass("shrink-0");
  });
});
