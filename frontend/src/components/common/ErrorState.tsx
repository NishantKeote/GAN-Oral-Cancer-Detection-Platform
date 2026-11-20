import React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Connection Error",
  message = "Failed to communicate with service. Please check network connectivity and backend status.",
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center rounded-lg border border-destructive/20 bg-destructive/5",
        className
      )}
    >
      <div className="h-10 w-10 rounded-full bg-destructive/10 flex items-center justify-center mb-3">
        <AlertCircle className="h-5 w-5 text-destructive" />
      </div>
      <h4 className="text-sm font-semibold text-foreground">{title}</h4>
      <p className="text-xs text-muted-foreground mt-1 max-w-md">{message}</p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="mt-4 gap-1.5"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Retry Request
        </Button>
      )}
    </div>
  );
};
