import type { ApiSuccess } from "@/types/api";
import type { AuthUser } from "@/types/auth";
import { api } from "@/api/client";

export type LoginResponse = {
  user: AuthUser;
  tokens: {
    access: string;
    refresh: string;
  };
};

export type TokenRefreshResponse = {
  tokens: {
    access: string;
    refresh?: string;
  };
};

export async function loginRequest(email: string, password: string) {
  const { data } = await api.post<ApiSuccess<LoginResponse>>("/auth/login/", {
    email,
    password,
  });
  return data.data;
}

export async function logoutRequest(refresh: string) {
  await api.post<ApiSuccess<null>>("/auth/logout/", { refresh });
}

export async function fetchMe() {
  const { data } = await api.get<ApiSuccess<AuthUser>>("/auth/me/");
  return data.data;
}

export async function refreshTokens(refresh: string) {
  const { data } = await api.post<ApiSuccess<TokenRefreshResponse>>(
    "/auth/token/refresh/",
    { refresh },
  );
  return data.data.tokens;
}
