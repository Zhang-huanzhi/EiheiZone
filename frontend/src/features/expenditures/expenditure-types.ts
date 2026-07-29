export type ExpenditureRecord = {
  id: string;
  created_by: string;
  created_by_display_name: string;
  spent_on: string;
  amount: string;
  currency: string;
  category: string;
  description: string;
  created_at: string;
  updated_at: string;
};

export type ExpenditurePage = {
  items: ExpenditureRecord[];
  total: number;
  offset: number;
  limit: number;
};

export type ExpenditureCreateInput = {
  spent_on: string;
  amount: string;
  currency: string;
  category: string;
  description: string;
};

export type ExpenditureUpdateInput = Partial<ExpenditureCreateInput>;

export type ExpenditureListParams = {
  offset?: number;
  limit?: number;
};
