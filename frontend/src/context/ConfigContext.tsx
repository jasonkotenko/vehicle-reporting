import { createContext, useContext, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

interface ConfigContextValue {
  displayTimezone: string;
  loading: boolean;
}

const ConfigContext = createContext<ConfigContextValue>({
  displayTimezone: "Asia/Manila",
  loading: true,
});

export function ConfigProvider({ children }: { children: ReactNode }) {
  const { data, isLoading } = useQuery({
    queryKey: ["config"],
    queryFn: api.getConfig,
    staleTime: Infinity,
  });

  return (
    <ConfigContext.Provider
      value={{
        displayTimezone: data?.display_timezone ?? "Asia/Manila",
        loading: isLoading,
      }}
    >
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig(): ConfigContextValue {
  return useContext(ConfigContext);
}
