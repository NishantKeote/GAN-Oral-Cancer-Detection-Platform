import React from "react";
import { Server, Sliders, Moon, Sun } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { useTheme } from "@/contexts/ThemeContext";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const configuredUrl = import.meta.env.VITE_API_BASE_URL;
  const apiBaseUrl =
    configuredUrl && configuredUrl.trim() !== ""
      ? configuredUrl
      : typeof window !== "undefined"
      ? `${window.location.origin} (Same-Origin)`
      : "http://localhost:8000";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Platform Settings & Configuration
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          System telemetry, model hyperparameters, and client interface preferences.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Appearance Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sun className="h-4 w-4 text-primary" />
              Interface Theme
            </CardTitle>
            <CardDescription>
              Select light or dark visualization mode for clinical environments.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3">
              <Button
                variant={theme === "light" ? "default" : "outline"}
                size="sm"
                onClick={() => setTheme("light")}
                className="gap-2 flex-1"
              >
                <Sun className="h-4 w-4" />
                Light Mode (Default)
              </Button>
              <Button
                variant={theme === "dark" ? "default" : "outline"}
                size="sm"
                onClick={() => setTheme("dark")}
                className="gap-2 flex-1"
              >
                <Moon className="h-4 w-4" />
                Dark Mode
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Preference is persisted across sessions in your browser's localStorage.
            </p>
          </CardContent>
        </Card>

        {/* Backend API Configuration */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Server className="h-4 w-4 text-primary" />
              Backend Connection
            </CardTitle>
            <CardDescription>
              FastAPI orchestration endpoint configuration.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-foreground">API Base URL</label>
              <div className="mt-1 font-mono text-xs bg-muted/50 p-2 rounded border border-border">
                {apiBaseUrl}
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Badge variant="outline">FastAPI REST</Badge>
              <Badge variant="outline">CORS Enabled</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Classifier Hyperparameters */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sliders className="h-4 w-4 text-primary" />
              Classifier Decision Hyperparameters
            </CardTitle>
            <CardDescription>
              Operating boundaries calibrated during validation on histopathology cohorts.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-3 rounded-md bg-muted/40 border border-border">
                <div className="text-xs text-muted-foreground">Optimal Cut-off Boundary</div>
                <div className="text-lg font-bold text-foreground mt-0.5">0.850266</div>
                <div className="text-[11px] text-muted-foreground mt-1">Youden's J / F1-calibrated</div>
              </div>

              <div className="p-3 rounded-md bg-muted/40 border border-border">
                <div className="text-xs text-muted-foreground">Target Convolutional Layer</div>
                <div className="text-lg font-bold text-foreground mt-0.5 font-mono">top_conv</div>
                <div className="text-[11px] text-muted-foreground mt-1">(None, 7, 7, 1280)</div>
              </div>

              <div className="p-3 rounded-md bg-muted/40 border border-border">
                <div className="text-xs text-muted-foreground">Input Tile Dimension</div>
                <div className="text-lg font-bold text-foreground mt-0.5 font-mono">224 x 224</div>
                <div className="text-[11px] text-muted-foreground mt-1">RGB (3 channels)</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
