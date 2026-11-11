import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AnswerForm } from "@/features/qas/answer-form";
import { addAnswer, createQuestion } from "@/features/qas/qa-api";
import { QuestionForm } from "@/features/qas/question-form";
import type { QARecord } from "@/features/qas/qa-types";

const replace = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace, refresh }) }));
vi.mock("@/features/qas/qa-api", () => ({ createQuestion: vi.fn(), addAnswer: vi.fn() }));

const mockedCreateQuestion = vi.mocked(createQuestion);
const mockedAddAnswer = vi.mocked(addAnswer);

const unansweredQA: QARecord = {
  id: "qa-id",
  asked_by: "family-id",
  asked_by_display_name: "Family User",
  question: "Question text",
  is_proxy: false,
  answer: null,
  answered_by: null,
  answered_by_display_name: null,
  status: "unanswered",
  answers_count: 0,
  answers: [],
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

  it("submits the question with proxy flag and opens detail", async () => {
    const user = userEvent.setup();
    mockedCreateQuestion.mockResolvedValue(unansweredQA);
    render(<QuestionForm />);

    await user.type(screen.getByLabelText("问题"), "Question with details");
    await user.click(screen.getByLabelText("代问"));
    await user.click(screen.getByRole("button", { name: "提交问题" }));

    expect(mockedCreateQuestion).toHaveBeenCalledWith({
      question: "Question with details",
      is_proxy: true,
    });
    expect(replace).toHaveBeenCalledWith("/family/qas/qa-id");
    expect(refresh).toHaveBeenCalled();
  });

  it("submits an answer with proxy flag and refreshes page", async () => {
    const user = userEvent.setup();
    mockedAddAnswer.mockResolvedValue({
      ...unansweredQA,
      status: "answered",
      answers_count: 1,
      answers: [
        {
          id: "ans-id",
          qa_id: "qa-id",
          author_id: "owner-id",
          author_display_name: "Owner User",
          content: "Current answer",
          is_proxy: true,
          created_at: "2026-07-27T01:00:00Z",
          updated_at: "2026-07-27T01:00:00Z",
        },
      ],
    });
    render(<AnswerForm qa={unansweredQA} />);

    await user.type(screen.getByLabelText("回答"), "Current answer");
    await user.click(screen.getByLabelText("代回答"));
    await user.click(screen.getByRole("button", { name: "提交回答" }));

    expect(mockedAddAnswer).toHaveBeenCalledWith("qa-id", {
      content: "Current answer",
      is_proxy: true,
    });
    expect(refresh).toHaveBeenCalled();
  });

  it("submits an Owner question and opens the Owner detail", async () => {
    const user = userEvent.setup();
    mockedCreateQuestion.mockResolvedValue(unansweredQA);
    render(
      <QuestionForm
        newQuestionPath="/owner/qas/new"
        redirectBasePath="/owner/qas"
      />,
    );

    await user.type(screen.getByLabelText("问题"), "Owner question");
    await user.click(screen.getByRole("button", { name: "提交问题" }));

    expect(mockedCreateQuestion).toHaveBeenCalledWith({
      question: "Owner question",
      is_proxy: false,
    });
    expect(replace).toHaveBeenCalledWith("/owner/qas/qa-id");
    expect(refresh).toHaveBeenCalled();
  });

  it("rejects blank answer without sending a request", async () => {
    const user = userEvent.setup();
    render(<AnswerForm qa={unansweredQA} />);

    await user.click(screen.getByRole("button", { name: "提交回答" }));

    expect(screen.getByText("请输入回答。")).toBeInTheDocument();
    expect(mockedAddAnswer).not.toHaveBeenCalled();
  });
});
