export type QAStatus = "unanswered" | "answered";

export type QARecord = {
  id: string;
  asked_by: string;
  asked_by_display_name: string;
  question: string;
  answer: string | null;
  answered_by: string | null;
  answered_by_display_name: string | null;
  status: QAStatus;
  answered_at: string | null;
  created_at: string;
  updated_at: string;
};

export type QAPage = {
  items: QARecord[];
  total: number;
  offset: number;
  limit: number;
};

export type QACreateInput = {
  question: string;
};

export type QAAnswerInput = {
  answer: string;
};

export type QAListParams = {
  offset?: number;
  limit?: number;
};
