import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useLocation, useNavigate } from "react-router-dom";

import { loginRequest } from "@/api/auth";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/store/authStore";
import {
  loginSchema,
  type LoginFormValues,
} from "@/validations/auth";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((s) => s.setSession);
  const [formError, setFormError] = useState<string | null>(null);

  const from =
    (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ||
    "/";

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    try {
      const data = await loginRequest(values.email.trim(), values.password);
      setSession({
        user: data.user,
        access: data.tokens.access,
        refresh: data.tokens.refresh,
      });
      navigate(from, { replace: true });
    } catch (error) {
      setFormError(getApiErrorMessage(error, "Invalid email or password."));
    }
  });

  return (
    <div className="relative flex min-h-full items-center justify-center overflow-hidden px-4 py-16">
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden
        style={{
          background:
            "radial-gradient(800px 420px at 15% 10%, rgba(15,118,110,0.18), transparent 55%), radial-gradient(700px 380px at 90% 0%, rgba(20,32,29,0.08), transparent 50%)",
        }}
      />

      <div className="relative w-full max-w-md animate-[fadeIn_320ms_ease-out] rounded-2xl border border-line bg-surface/95 p-8 shadow-[0_24px_60px_-32px_rgba(20,32,29,0.55)] backdrop-blur">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand text-sm font-bold text-white">
            BMS
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight text-ink">
              Business Management System
            </p>
            <p className="text-xs text-muted">Sign in to continue</p>
          </div>
        </div>

        <h1 className="text-2xl font-semibold tracking-tight text-ink">Welcome back</h1>
        <p className="mt-2 text-sm text-muted">
          Use your work email and password. Demo admin:{" "}
          <span className="font-medium text-ink">admin@bms.local</span>
        </p>

        <form onSubmit={onSubmit} className="mt-8 space-y-4" noValidate>
          <div>
            <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-ink">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              className="w-full rounded-lg border border-line bg-canvas px-3 py-2.5 text-sm text-ink outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
              placeholder="you@company.com"
              {...register("email")}
            />
            {errors.email && (
              <p className="mt-1.5 text-xs text-danger">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1.5 block text-sm font-medium text-ink"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              className="w-full rounded-lg border border-line bg-canvas px-3 py-2.5 text-sm text-ink outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
              placeholder="••••••••"
              {...register("password")}
            />
            {errors.password && (
              <p className="mt-1.5 text-xs text-danger">{errors.password.message}</p>
            )}
          </div>

          {formError && (
            <div
              role="alert"
              className="rounded-lg border border-danger/20 bg-danger/5 px-3 py-2 text-sm text-danger"
            >
              {formError}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-brand px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-deep disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isSubmitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
