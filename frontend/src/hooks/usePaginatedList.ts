import { useQuery } from "@tanstack/react-query";
import { useCallback, useState } from "react";

import { listResource, type ListParams } from "@/api/resource";

export function usePaginatedList<T>(
  key: string,
  path: string,
  extraParams?: ListParams,
) {
  const [page, setPage] = useState(1);
  const [search, setSearchRaw] = useState("");
  const setSearch = useCallback((value: string) => {
    setSearchRaw(value);
    setPage(1);
  }, []);

  const query = useQuery({
    queryKey: [key, "list", page, search, extraParams],
    queryFn: () =>
      listResource<T>(path, {
        page,
        search: search || undefined,
        ...extraParams,
      }),
  });

  return {
    ...query,
    page,
    setPage,
    search,
    setSearch,
    rows: query.data?.results ?? [],
    total: query.data?.count ?? 0,
  };
}
