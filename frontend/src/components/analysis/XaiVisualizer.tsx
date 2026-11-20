import React, { useState } from "react";
import {
  Eye,
  AlertTriangle,
  Info,
  Sliders,
  Layers,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import type { XAISummary, XAIMethodResult } from "@/types";

interface XaiVisualizerProps {
  xai: XAISummary;
  originalImageUrl: string;
  apiBaseUrl: string;
  className?: string;
}

// Preserve exact backend method keys: Grad-CAM, Grad-CAM++, LayerCAM, HiResCAM
const XAI_METHODS: Array<{
  key: "Grad-CAM" | "Grad-CAM++" | "LayerCAM" | "HiResCAM";
  label: string;
  description: string;
}> = [
  {
    key: "Grad-CAM",
    label: "Grad-CAM",
    description:
      "Global-average-pooled gradient weighting on top_conv feature activations.",
  },
  {
    key: "Grad-CAM++",
    label: "Grad-CAM++",
    description:
      "Analytic higher-order positive derivative weighting for dense multi-region cellular atypia.",
  },
  {
    key: "LayerCAM",
    label: "LayerCAM",
    description:
      "Fine-grained spatial weighting retaining pixel-level positive gradient coordinates.",
  },
  {
    key: "HiResCAM",
    label: "HiResCAM",
    description:
      "Element-wise product of raw gradients and feature maps without spatial average distortion.",
  },
];

export const XaiVisualizer: React.FC<XaiVisualizerProps> = ({
  xai,
  originalImageUrl,
  apiBaseUrl,
  className = "",
}) => {
  const [activeMethod, setActiveMethod] = useState<
    "Grad-CAM" | "Grad-CAM++" | "LayerCAM" | "HiResCAM"
  >("Grad-CAM");
  const [viewMode, setViewMode] = useState<"overlay" | "heatmap">("overlay");
  const [imageErrors, setImageErrors] = useState<Record<string, boolean>>({});

  // Lookup method data with exact key matching and case-insensitive fallback
  const getMethodData = (
    key: string
  ): XAIMethodResult | undefined => {
    if (!xai || !xai.methods) return undefined;
    if (xai.methods[key]) return xai.methods[key];
    // Case-insensitive lookup fallback
    const foundEntry = Object.entries(xai.methods).find(
      ([k]) =>
        k.toLowerCase().replace(/[^a-z0-9]/g, "") ===
        key.toLowerCase().replace(/[^a-z0-9]/g, "")
    );
    return foundEntry ? foundEntry[1] : undefined;
  };

  const selectedData = getMethodData(activeMethod);
  const rawPath =
    viewMode === "overlay"
      ? selectedData?.overlay_url
      : selectedData?.heatmap_url;

  // Resolve absolute or relative URL and bypass ngrok interstitial for images if applicable
  const baseUrlResolved = rawPath
    ? rawPath.startsWith("http")
      ? rawPath
      : `${apiBaseUrl ? apiBaseUrl.replace(/\/$/, "") : ""}${rawPath}`
    : null;

  const isNgrokDomain =
    (baseUrlResolved && baseUrlResolved.includes("ngrok")) ||
    (typeof window !== "undefined" && window.location.hostname.includes("ngrok"));

  const resolvedImageUrl =
    baseUrlResolved && isNgrokDomain
      ? `${baseUrlResolved}${baseUrlResolved.includes("?") ? "&" : "?"}ngrok-skip-browser-warning=true`
      : baseUrlResolved;

  const currentKeyErrorKey = `${activeMethod}-${viewMode}`;
  const hasImageError = Boolean(imageErrors[currentKeyErrorKey]);

  const activeMethodMeta =
    XAI_METHODS.find((m) => m.key === activeMethod) || XAI_METHODS[0];

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Tab Switcher & View Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-border">
        {/* Method Selection Tabs (Grad-CAM, Grad-CAM++, LayerCAM, HiResCAM) */}
        <div className="flex flex-wrap items-center gap-1.5 p-1 bg-muted/70 rounded-lg">
          {XAI_METHODS.map((method) => {
            const isActive = activeMethod === method.key;
            const data = getMethodData(method.key);
            const isMethodOk = data?.status === "ok";

            return (
              <button
                key={method.key}
                type="button"
                onClick={() => setActiveMethod(method.key)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  isActive
                    ? "bg-card text-foreground shadow-sm ring-1 ring-border font-semibold"
                    : "text-muted-foreground hover:text-foreground hover:bg-card/50"
                }`}
                title={method.description}
              >
                <span>{method.label}</span>
                {data && !isMethodOk && (
                  <span className="ml-1 text-[10px] text-destructive">(!)</span>
                )}
              </button>
            );
          })}
        </div>

        {/* View Mode Toggle: Overlay vs Raw Heatmap */}
        <div className="flex items-center gap-1 self-end sm:self-auto print:hidden">
          <Button
            type="button"
            variant={viewMode === "overlay" ? "default" : "outline"}
            size="sm"
            onClick={() => setViewMode("overlay")}
            className="text-xs h-7 px-2.5 gap-1"
          >
            <Layers className="h-3 w-3" />
            Overlay (0.42 Red)
          </Button>
          <Button
            type="button"
            variant={viewMode === "heatmap" ? "default" : "outline"}
            size="sm"
            onClick={() => setViewMode("heatmap")}
            className="text-xs h-7 px-2.5 gap-1"
          >
            <Sliders className="h-3 w-3" />
            Grayscale Map
          </Button>
        </div>
      </div>

      {/* Side-by-Side Comparison Layout on Desktop, Stacked on Mobile */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        {/* Left Column: Original Biopsy Tile */}
        <div className="flex flex-col items-center p-4 rounded-xl border border-border bg-card/60 shadow-xs">
          <div className="w-full flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <Eye className="h-3.5 w-3.5 text-primary" />
              Original Biopsy Tile (H&E)
            </span>
            <Badge variant="outline" className="text-[10px] font-mono">
              224 × 224 RGB
            </Badge>
          </div>

          <div className="relative w-full max-w-[340px] aspect-square rounded-lg overflow-hidden border border-border bg-slate-950/5 flex items-center justify-center">
            {originalImageUrl ? (
              <img
                src={originalImageUrl}
                alt="Original Histopathology Tile"
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="text-xs text-muted-foreground">
                Original image unavailable
              </div>
            )}
          </div>

          <div className="w-full mt-2 text-[11px] text-muted-foreground text-center">
            Standard stained hematoxylin and eosin patch submitted for classification.
          </div>
        </div>

        {/* Right Column: Selected XAI Attribution Heatmap */}
        <div className="flex flex-col items-center p-4 rounded-xl border border-border bg-card/60 shadow-xs">
          <div className="w-full flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-primary" />
              {activeMethod} {viewMode === "overlay" ? "Overlay Blend" : "Raw Heatmap"}
            </span>
            <Badge variant="outline" className="text-[10px]">
              top_conv Layer
            </Badge>
          </div>

          <div className="relative w-full max-w-[340px] aspect-square rounded-lg overflow-hidden border border-border bg-slate-950/5 flex items-center justify-center">
            {hasImageError ? (
              // Explicit error state without hiding or replacing with original image
              <div className="w-full h-full p-4 flex flex-col items-center justify-center text-center bg-destructive/5 text-destructive border border-destructive/20 rounded-lg">
                <AlertTriangle className="h-7 w-7 mb-2 text-destructive shrink-0" />
                <span className="text-xs font-semibold text-foreground">
                  Attribution Image Failed to Load
                </span>
                <span className="text-[10px] text-muted-foreground mt-1 max-w-[240px] break-all font-mono">
                  Target: {rawPath || "Endpoint returned empty path"}
                </span>
                <span className="text-[10px] text-muted-foreground mt-1">
                  Ensure the backend artifact directory exists and the API is accessible.
                </span>
              </div>
            ) : resolvedImageUrl ? (
              <img
                src={resolvedImageUrl}
                alt={`${activeMethod} Attribution Visual`}
                className="w-full h-full object-contain"
                onError={() => {
                  setImageErrors((prev) => ({
                    ...prev,
                    [currentKeyErrorKey]: true,
                  }));
                }}
              />
            ) : (
              <div className="w-full h-full p-4 flex flex-col items-center justify-center text-center text-muted-foreground">
                <Info className="h-6 w-6 mb-1.5 text-muted-foreground" />
                <span className="text-xs font-medium">Attribution not generated</span>
                <span className="text-[10px] mt-0.5">
                  Method status: {selectedData?.status || "unavailable"}
                </span>
              </div>
            )}
          </div>

          {/* Saliency & Method Statistics Summary */}
          <div className="w-full mt-2 flex flex-col gap-1 text-[11px] text-muted-foreground">
            {selectedData?.statistics && (
              <div className="flex items-center justify-between border-t border-border/50 pt-1.5 font-mono text-[10px]">
                <span>Mean: {selectedData.statistics.mean.toFixed(3)}</span>
                <span>Std: {selectedData.statistics.std.toFixed(3)}</span>
                <span>Q90: {selectedData.statistics.q90.toFixed(3)}</span>
                <span>&ge;0.5: {(selectedData.statistics.fraction_at_or_above_0_5 * 100).toFixed(0)}%</span>
              </div>
            )}
            <div className="text-center text-[10px] text-muted-foreground mt-0.5">
              {activeMethodMeta.description}
            </div>
          </div>
        </div>
      </div>

      {/* Attribution Semantics Clinical Disclaimer */}
      <div className="p-3 rounded-lg border border-border/70 bg-muted/30 text-[11px] text-muted-foreground leading-relaxed flex items-start gap-2">
        <Info className="h-4 w-4 text-primary shrink-0 mt-0.5" />
        <div>
          <strong className="text-foreground">Attribution Interpretation Notice:</strong>{" "}
          Heatmaps represent mathematical gradient sensitivities (regions where features influenced the EfficientNetB0 classification score). They do <strong>not</strong> identify cancer cell boundaries, tumor contours, or confirm pathological tissue structures.
        </div>
      </div>
    </div>
  );
};
