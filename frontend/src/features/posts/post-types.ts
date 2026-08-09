export type PostVisibility = "public" | "family";

export type PostRecord = {
  id: string;
  author_id: string;
  author_display_name: string;
  title: string;
  body: string;
  visibility: PostVisibility;
  created_at: string;
  updated_at: string;
  images?: PostImageRecord[];
};

export type PostImageRecord = {
  id: string;
  url: string;
  position: number;
  width: number;
  height: number;
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
  image_ids?: string[];
};

export type PostUpdateInput = Partial<Pick<PostCreateInput, "title" | "body" | "visibility">>;

export type PostListParams = {
  offset?: number;
  limit?: number;
};
