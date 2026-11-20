import React from "react";
import { Activity } from "lucide-react";
import { useHealth } from "@/hooks/useHealth";
import { Badge } from "@/components/ui/Badge";

export const SystemStatusBadge: React.FC = () => {
  const { data: health, isLoading } = useHealth();

  if (isLoading) {
    return (
      <Badge
        variant="outline"
        className="gap-1.5 text-xs text-muted-foreground font-normal"
        title="Querying backend GET /health..."
      >
        <span className="h-2 w-2 rounded-full bg-slate-400 animate-pulse" />
        Checking API...
      </Badge>
    );
  }

  const isOk = health?.status === "ok" || health?.status === "healthy";
  const isExplicitlyDegraded = health?.status === "degraded";
  
  // Check if core API is online but cloud auxiliaries (Neo4j/Groq) are unconfigured
  const hasUnconfiguredAuxiliaries =
    isOk &&
    health?.services &&
    (health.services.neo4j_connected === false || health.services.groq_configured === false);

  if (isExplicitlyDegraded || (isOk && hasUnconfiguredAuxiliaries)) {
    return (
      <Badge
        variant="warning"
        className="gap-1.5 text-xs font-medium cursor-help"
        title={`Backend API online. Auxiliary services: Neo4j: ${
          health?.services?.neo4j_connected ? "connected" : "offline/unconfigured"
        }, Groq: ${health?.services?.groq_configured ? "ready" : "unconfigured"}`}
      >
        <span className="h-2 w-2 rounded-full bg-amber-500" />
        API Online (Degraded)
      </Badge>
    );
  }

  if (isOk) {
    return (
      <Badge
        variant="success"
        className="gap-1.5 text-xs font-medium cursor-help"
        title={`Backend API healthy (v${health?.version || "2.0.0"}). Model: ${health?.model || "EfficientNetB0"}`}
      >
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        API Online
      </Badge>
    );
  }

  return (
    <Badge
      variant="outline"
      className="gap-1.5 text-xs text-rose-600 dark:text-rose-400 border-rose-200 dark:border-rose-900/50 cursor-help"
      title="Backend server at http://localhost:8000 is unreachable or returned an error."
    >
      <Activity className="h-3 w-3" />
      API Offline
    </Badge>
  );
};
