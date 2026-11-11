export type QAStatus = "unanswered" | "answered";

export type QAAnswerRecord = {
  id: string;
  qa_id: string;
  author_id: string;
  author_display_name: string;
  content: string;
  is_proxy?: boolean;
  created_at: string;
  updated_at: string;
};

export type QARecord = {
  id: string;
  asked_by: string;
  asked_by_display_name: string;
  question: string;
  is_proxy?: boolean;
  status: QAStatus;
  answers_count?: number;
  answers?: QAAnswerRecord[];
  answer?: string | null;
  answered_by?: string | null;
  answered_by_display_name?: string | null;
  answered_at?: string | null;
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
  is_proxy?: boolean;
};

export type QAAnswerInput = {
  content?: string;
  answer?: string;
  is_proxy?: boolean;
};

export type QAListParams = {
  offset?: number;
  limit?: number;
};
