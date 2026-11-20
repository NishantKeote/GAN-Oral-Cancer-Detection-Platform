import React from "react";
import { History, Search, Filter } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { Button } from "@/components/ui/Button";

export const AnalysisHistoryPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Analysis History & Audit Log
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Historical diagnostic evaluations and persisted Neo4j patient case records.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-1.5" disabled>
            <Filter className="h-3.5 w-3.5" />
            Filter
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5" disabled>
            <Search className="h-3.5 w-3.5" />
            Search Records
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <History className="h-4 w-4 text-primary" />
            Persisted Case Records
          </CardTitle>
          <CardDescription>
            Audit log of previously executed tile evaluations and attribution artifacts.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={<History className="h-8 w-8 text-muted-foreground" />}
            title="No Evaluation Records Yet"
            description="Diagnostic cases processed via POST /analyze will be logged and queryable here once live case persistence is enabled."
            actionLabel="Start First Analysis"
            onAction={() => window.location.assign("/analyze")}
          />
        </CardContent>
      </Card>
    </div>
  );
};
