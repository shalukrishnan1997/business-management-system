import type { Paginated, ApiSuccess } from "@/types/api";
import { api } from "@/api/client";
import { cleanParams, type ListParams } from "@/utils/params";

export type { ListParams };
export { cleanParams };

export async function listResource<T>(path: string, params?: ListParams) {
  const { data } = await api.get<Paginated<T>>(path, { params: cleanParams(params) });
  return data;
}

export async function getResource<T>(path: string) {
  const { data } = await api.get<ApiSuccess<T>>(path);
  return data.data;
}

export async function createResource<T>(path: string, body: unknown) {
  const { data } = await api.post<ApiSuccess<T>>(path, body);
  return data.data;
}

export async function updateResource<T>(path: string, body: unknown) {
  const { data } = await api.patch<ApiSuccess<T>>(path, body);
  return data.data;
}

export async function deleteResource(path: string) {
  const { data } = await api.delete(path);
  return data;
}

export async function postAction<T = unknown>(path: string, body?: unknown) {
  const { data } = await api.post<ApiSuccess<T>>(path, body ?? {});
  return data.data;
}
