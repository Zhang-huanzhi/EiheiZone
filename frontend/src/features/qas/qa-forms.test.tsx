import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AnswerForm } from "@/features/qas/answer-form";
import { createQuestion, upsertAnswer } from "@/features/qas/qa-api";
import { QuestionForm } from "@/features/qas/question-form";
import type { QARecord } from "@/features/qas/qa-types";

const replace = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace, refresh }) }));
vi.mock("@/features/qas/qa-api", () => ({ createQuestion: vi.fn(), upsertAnswer: vi.fn() }));

const mockedCreateQuestion = vi.mocked(createQuestion);
const mockedUpsertAnswer = vi.mocked(upsertAnswer);

const unansweredQA: QARecord = {
  id: "qa-id",
  asked_by: "family-id",
  asked_by_display_name: "Family User",
  question: "Question text",
  answer: null,
  answered_by: null,
  answered_by_display_name: null,
  status: "unanswered",
  answered_at: null,
  created_at: "2026-07-27T00:00:00Z",
  updated_at: "2026-07-27T00:00:00Z",
};

afterEach(() => {
  vi.clearAllMocks();
});

describe("QA forms", () => {
  it("rejects a blank question without sending a request", async () => {
    const user = userEvent.setup();
    render(<QuestionForm />);

    await user.click(screen.getByRole("button", { name: "提交问题" }));

    expect(screen.getByText("请输入问题。")).toBeInTheDocument();
    expect(mockedCreateQuestion).not.toHaveBeenCalled();
  });

  it("submits only the question and opens the created Family detail", async () => {
    const user = userEvent.setup();
    mockedCreateQuestion.mockResolvedValue(unansweredQA);
    render(<QuestionForm />);

    await user.type(screen.getByLabelText("问题"), "Question with details");
    await user.click(screen.getByRole("button", { name: "提交问题" }));

    expect(mockedCreateQuestion).toHaveBeenCalledWith({ question: "Question with details" });
    expect(replace).toHaveBeenCalledWith("/family/qas/qa-id");
    expect(refresh).toHaveBeenCalled();
  });

  it("submits one complete answer and returns to Owner management", async () => {
    const user = userEvent.setup();
    mockedUpsertAnswer.mockResolvedValue({
      ...unansweredQA,
      answer: "Current answer",
      answered_by: "owner-id",
      answered_by_display_name: "Owner User",
      status: "answered",
      answered_at: "2026-07-27T01:00:00Z",
    });
    render(<AnswerForm qa={unansweredQA} />);

    await user.type(screen.getByLabelText("回答"), "Current answer");
    await user.click(screen.getByRole("button", { name: "保存回答" }));

    expect(mockedUpsertAnswer).toHaveBeenCalledWith("qa-id", { answer: "Current answer" });
    expect(replace).toHaveBeenCalledWith("/owner/qas");
    expect(refresh).toHaveBeenCalled();
  });

  it("does not send an unchanged replacement answer", async () => {
    const user = userEvent.setup();
    render(
      <AnswerForm
        qa={{
          ...unansweredQA,
          answer: "Existing answer",
          answered_by: "owner-id",
          answered_by_display_name: "Owner User",
          status: "answered",
          answered_at: "2026-07-27T01:00:00Z",
        }}
      />,
    );

    await user.click(screen.getByRole("button", { name: "更新回答" }));

    expect(screen.getByRole("alert")).toHaveTextContent("没有需要保存的修改。");
    expect(mockedUpsertAnswer).not.toHaveBeenCalled();
  });
});
