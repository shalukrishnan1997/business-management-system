import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { BrowserRouter } from "react-router-dom";

import { AuthBootstrap } from "@/features/auth/AuthBootstrap";
import { AppRouter } from "@/routes/AppRouter";

export default function App() {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthBootstrap>
          <AppRouter />
        </AuthBootstrap>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
