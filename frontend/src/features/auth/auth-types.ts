export type UserRole = "family" | "owner";

export type CurrentUser = {
  id: string;
  login_name: string;
  display_name: string;
  role: UserRole;
};

export type CsrfResponse = {
  csrf_token: string;
};

export type LoginRequest = {
  login_name: string;
  password: string;
};

export type LoginResponse = {
  user: CurrentUser;
  csrf_token: string;
};
