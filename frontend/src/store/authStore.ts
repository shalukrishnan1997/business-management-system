import { create } from "zustand";

import type { AuthStatus, AuthUser } from "@/types/auth";

type AuthState = {
  user: AuthUser | null;
  accessToken: string | null;
  status: AuthStatus;
  setSession: (payload: {
    user: AuthUser;
    access: string;
    refresh: string;
  }) => void;
  setUser: (user: AuthUser) => void;
  clearSession: () => void;
  setStatus: (status: AuthStatus) => void;
  getRefreshToken: () => string | null;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: localStorage.getItem("bms_access_token"),
  status: "bootstrapping",
  setSession: ({ user, access, refresh }) => {
    localStorage.setItem("bms_access_token", access);
    localStorage.setItem("bms_refresh_token", refresh);
    localStorage.setItem("bms_user", JSON.stringify(user));
    set({ user, accessToken: access, status: "authenticated" });
  },
  setUser: (user) => {
    localStorage.setItem("bms_user", JSON.stringify(user));
    set({ user, status: "authenticated" });
  },
  clearSession: () => {
    localStorage.removeItem("bms_access_token");
    localStorage.removeItem("bms_refresh_token");
    localStorage.removeItem("bms_user");
    set({ user: null, accessToken: null, status: "anonymous" });
  },
  setStatus: (status) => set({ status }),
  getRefreshToken: () => localStorage.getItem("bms_refresh_token"),
}));
