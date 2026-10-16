export const MAX_POST_COMMENT_LENGTH = 2000;

export type PostCommentRecord = {
  id: string;
  post_id: string;
  author_id: string;
  author_display_name: string;
  body: string;
  created_at: string;
};

export type PostCommentPage = {
  items: PostCommentRecord[];
  total: number;
  offset: number;
  limit: number;
};

export type PostCommentCreateInput = {
  body: string;
};

export type PostCommentListParams = {
  offset?: number;
  limit?: number;
};
