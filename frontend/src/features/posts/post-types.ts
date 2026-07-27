export type PostVisibility = "public" | "family";

export type PostRecord = {
  id: string;
  title: string;
  body: string;
  visibility: PostVisibility;
  created_at: string;
  updated_at: string;
};

export type PostPage = {
  items: PostRecord[];
  total: number;
  offset: number;
  limit: number;
};

export type PostCreateInput = {
  title: string;
  body: string;
  visibility: PostVisibility;
};

export type PostUpdateInput = Partial<PostCreateInput>;

export type PostListParams = {
  offset?: number;
  limit?: number;
};
