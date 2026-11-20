import React from "react";
import { Link } from "react-router-dom";
import {
  UploadCloud,
  Microscope,
  FileText,
  Clock,
  ArrowRight,
  ShieldAlert,
  CheckCircle,
  HelpCircle,
  Layers,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/common/EmptyState";
import { useHealth } from "@/hooks/useHealth";

export const DashboardPage: React.FC = () => {
  const { data: health } = useHealth();
  const isOnline =
    health?.status === "ok" ||
    health?.status === "healthy" ||
    health?.status === "degraded";

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Welcome Heading & Clinical Platform Description */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-primary bg-primary/10 px-2 py-0.5 rounded">
              Clinical Decision Support
            </span>
            <span className="text-xs text-muted-foreground">• Version 1.0</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
            Oral Cancer AI Assessment & Reporting
          </h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            A computerized assistant for pathologists and clinicians to evaluate oral histopathology tiles, inspect morphological visual heatmaps, and review literature-grounded diagnostic reports.
          </p>
        </div>

        {/* Subtle Live Status Indicator */}
        <div className="flex items-center gap-2 self-start md:self-auto">
          <Badge
            variant={isOnline ? "success" : "outline"}
            className="text-xs px-2.5 py-1 gap-1.5 font-medium"
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isOnline ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
              }`}
            />
            {isOnline ? "Assessment Service Ready" : "Backend Offline"}
          </Badge>
        </div>
      </div>

      {/* Prominent Primary Call-to-Actions (Hero Actions) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Primary Action Card: Upload & Start Analysis */}
        <Card className="relative overflow-hidden border-primary/30 shadow-sm hover:shadow-md transition-shadow bg-gradient-to-br from-card via-card to-primary/5">
          <CardHeader className="pb-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center mb-2">
              <UploadCloud className="h-5 w-5" />
            </div>
            <CardTitle className="text-lg">Upload Histopathology Image</CardTitle>
            <CardDescription className="text-xs">
              Upload a 224×224 stained H&E tissue patch to begin AI-assisted classification and feature attribution.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-xs text-muted-foreground flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
              <span>Supports JPEG, PNG, and TIFF biopsy tile images</span>
            </div>
            <div className="text-xs text-muted-foreground flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
              <span>4 Explainable AI visualizations (Grad-CAM, ++, LayerCAM, HiResCAM)</span>
            </div>
            <div className="pt-2">
              <Link to="/analyze">
                <Button className="w-full gap-2 shadow-sm font-medium">
                  <Microscope className="h-4 w-4" />
                  Start New Analysis
                  <ArrowRight className="h-4 w-4 ml-auto" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Secondary Action Card: My Reports & Archive */}
        <Card className="border-border shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
          <CardHeader className="pb-3">
            <div className="h-10 w-10 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-2">
              <FileText className="h-5 w-5" />
            </div>
            <CardTitle className="text-lg">My Reports Archive</CardTitle>
            <CardDescription className="text-xs">
              Review diagnostic summaries, clinical research reports, and export PDF records for case discussions.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-xs text-muted-foreground flex items-center gap-2">
              <Clock className="h-4 w-4 text-blue-600 shrink-0" />
              <span>Access synthesized research reports and clinical impressions</span>
            </div>
            <div className="text-xs text-muted-foreground flex items-center gap-2">
              <Layers className="h-4 w-4 text-blue-600 shrink-0" />
              <span>Export print-ready consultation summaries with attribution plates</span>
            </div>
            <div className="pt-2">
              <Link to="/reports">
                <Button variant="outline" className="w-full gap-2 font-medium">
                  <FileText className="h-4 w-4" />
                  View Generated Reports
                  <ArrowRight className="h-4 w-4 ml-auto" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Intuitive 3-Step Instructions for Using the Platform */}
      <Card className="border-border/80">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <HelpCircle className="h-4 w-4 text-primary" />
            How to Use This Platform
          </CardTitle>
          <CardDescription className="text-xs">
            Simple 3-step workflow to obtain decision-support assessments for oral biopsy patches.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg border border-border bg-card/60 space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">
                  1
                </div>
                <h4 className="text-xs font-semibold text-foreground">Upload Histopathology Tile</h4>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Provide a stained 224×224 biopsy image patch. Tiles are checked for valid format and dimensions.
              </p>
            </div>

            <div className="p-4 rounded-lg border border-border bg-card/60 space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">
                  2
                </div>
                <h4 className="text-xs font-semibold text-foreground">Add Clinical Context</h4>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Enter optional patient details (age, biological sex, lesion site, risk history) to guide report synthesis.
              </p>
            </div>

            <div className="p-4 rounded-lg border border-border bg-card/60 space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">
                  3
                </div>
                <h4 className="text-xs font-semibold text-foreground">Review Assessment & Visuals</h4>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Inspect the model classification, 4 saliency heatmaps, matching scientific citations, and the clinical report.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Reports Section with Honest Empty State */}
      <Card>
        <CardHeader className="pb-3 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary" />
              Recent Reports
            </CardTitle>
            <CardDescription className="text-xs">
              Recently generated evaluations and assessment summaries.
            </CardDescription>
          </div>
          <Link to="/analyze">
            <Button size="sm" variant="outline" className="text-xs gap-1.5">
              <Microscope className="h-3.5 w-3.5" />
              New Analysis
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={<FileText className="h-8 w-8 text-muted-foreground/60" />}
            title="No Recent Reports Yet"
            description="Diagnostic evaluations performed during your session will appear here for quick review, visual inspection, and export."
            actionLabel="Start First Biopsy Assessment"
            onAction={() => window.location.assign("/analyze")}
          />
        </CardContent>
      </Card>

      {/* Prominent Clinical Decision Support Disclaimer */}
      <div className="p-4 rounded-lg border border-amber-500/20 bg-amber-500/5 text-amber-900 dark:text-amber-200 flex items-start gap-3">
        <ShieldAlert className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
        <div className="text-xs leading-relaxed space-y-1">
          <p className="font-semibold text-foreground">
            Clinical Decision Support Disclaimer
          </p>
          <p className="text-muted-foreground">
            This platform is an investigational computer-assisted tool intended solely for decision support and research. It does <strong>not</strong> provide a definitive medical diagnosis. All artificial intelligence assessments, heatmaps, and generated reports must be evaluated by a qualified pathologist in conjunction with whole-slide context, clinical history, and laboratory investigations.
          </p>
        </div>
      </div>
    </div>
  );
};
