import type { AxiosError, InternalAxiosRequestConfig } from "axios";
import axios from "axios";

import { useAuthStore } from "@/store/authStore";
import type { ApiSuccess } from "@/types/api";

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean };

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("bms_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined;
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("bms_refresh_token");
      if (refresh && !original.url?.includes("/auth/token/refresh/")) {
        try {
          const { data } = await axios.post<
            ApiSuccess<{ tokens: { access: string; refresh?: string } }>
          >(`${baseURL}/auth/token/refresh/`, { refresh });
          const access = data.data.tokens.access;
          const nextRefresh = data.data.tokens.refresh ?? refresh;
          localStorage.setItem("bms_access_token", access);
          localStorage.setItem("bms_refresh_token", nextRefresh);
          useAuthStore.setState({ accessToken: access });
          original.headers.Authorization = `Bearer ${access}`;
          return api(original);
        } catch {
          useAuthStore.getState().clearSession();
        }
      } else {
        useAuthStore.getState().clearSession();
      }
    }
    return Promise.reject(error);
  },
);

export function getApiErrorMessage(error: unknown, fallback = "Request failed.") {
  if (!axios.isAxiosError(error)) return fallback;
  const payload = error.response?.data as
    | { message?: string; errors?: Record<string, string[] | string> }
    | undefined;
  if (payload?.message) return payload.message;
  const errors = payload?.errors;
  if (errors) {
    const first = Object.values(errors)[0];
    if (Array.isArray(first) && first[0]) return String(first[0]);
    if (typeof first === "string") return first;
  }
  return fallback;
}
