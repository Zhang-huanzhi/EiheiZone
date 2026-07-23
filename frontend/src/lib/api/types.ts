export type FieldError = {
  field: string;
  message: string;
  type: string;
};

export type ApiErrorDetail = {
  code: string;
  message: string;
  field_errors: FieldError[];
  request_id: string;
};

export type ApiErrorResponse = {
  error: ApiErrorDetail;
};

export type HealthResponse = {
  status: "ok";
};
