export type ListParams = Record<
  string,
  string | number | boolean | undefined | null
>;

export function cleanParams(params?: ListParams) {
  if (!params) return undefined;
  const out: Record<string, string | number | boolean> = {};
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    out[key] = value;
  }
  return out;
}
