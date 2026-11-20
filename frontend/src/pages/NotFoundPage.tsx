import React from "react";
import { Link } from "react-router-dom";
import { FileQuestion, Home } from "lucide-react";
import { Button } from "@/components/ui/Button";

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-6">
      <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center text-muted-foreground mb-4">
        <FileQuestion className="h-8 w-8" />
      </div>
      <h1 className="text-3xl font-bold tracking-tight text-foreground">404</h1>
      <p className="text-base font-semibold text-foreground mt-1">Page Not Found</p>
      <p className="text-xs text-muted-foreground max-w-sm mt-1 mb-6">
        The requested diagnostic module or clinical route does not exist in the current interface.
      </p>
      <Link to="/">
        <Button size="sm" className="gap-2">
          <Home className="h-4 w-4" />
          Return to Dashboard
        </Button>
      </Link>
    </div>
  );
};
