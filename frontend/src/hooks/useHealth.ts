import { useQuery } from "@tanstack/react-query";
import { healthService } from "@/services/api";
import type { HealthStatus } from "@/types";

export const useHealth = () => {
  return useQuery<HealthStatus>({
    queryKey: ["backend-health"],
    queryFn: async () => {
      try {
        const data = await healthService.checkHealth();
        return data as HealthStatus;
      } catch {
        return {
          status: "error",
          version: "Unknown",
        } as HealthStatus;
      }
    },
    refetchInterval: 15000, // Refresh every 15 seconds
    refetchOnWindowFocus: true,
    retry: 1,
    staleTime: 10000,
  });
};
