import React, { useState, useRef } from "react";
import {
  UploadCloud,
  FileImage,
  Microscope,
  CheckCircle2,
  AlertCircle,
  RotateCcw,
  Printer,
  ExternalLink,
  ChevronRight,
  ChevronLeft,
  BookOpen,
  FileText,
  User,
  ShieldCheck,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { analysisService } from "@/services/api";
import { XaiVisualizer } from "@/components/analysis/XaiVisualizer";
import { MarkdownReport } from "@/components/report/MarkdownReport";
import type { AnalysisResponse, PatientFormContext } from "@/types";

type Step = 1 | 2 | 3 | 4 | 5;

export const NewAnalysisPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form context matching backend schema
  const [formData, setFormData] = useState<PatientFormContext>({
    age: "",
    sex: "",
    tobacco: "",
    alcohol: "",
    lesion_site: "",
    magnification: "400x",
    research_question: "",
  });

  // Submission & Result States
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<string>("Initializing inference...");
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Handle Image File Selection
  const handleFileChange = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setAnalysisError("Please select a valid image file (JPEG, PNG, or TIFF).");
      return;
    }
    setImageFile(file);
    setImagePreviewUrl(URL.createObjectURL(file));
    setAnalysisError(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  // Submit Analysis to Real Backend API
  const handleSubmitAnalysis = async () => {
    if (!imageFile) {
      setAnalysisError("Please upload a histopathology image tile.");
      setCurrentStep(1);
      return;
    }

    setCurrentStep(4);
    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      setAnalysisProgress("1/4: Preprocessing tile & running EfficientNetB0 inference...");
      await new Promise((r) => setTimeout(r, 400));

      setAnalysisProgress("2/4: Computing Grad-CAM, ++, LayerCAM & HiResCAM attributions...");
      await new Promise((r) => setTimeout(r, 400));

      setAnalysisProgress("3/4: Querying FAISS vector index & Neo4j disease ontology...");
      const result = await analysisService.analyzeCase(imageFile, formData);

      setAnalysisProgress("4/4: Synthesizing clinical report...");
      setAnalysisResult(result);
      setCurrentStep(5);
    } catch (err: any) {
      setAnalysisError(
        err?.message ||
          "Analysis pipeline failed. Ensure the FastAPI backend is running on port 8000."
      );
      setCurrentStep(4);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const resetWorkflow = () => {
    setImageFile(null);
    if (imagePreviewUrl) {
      URL.revokeObjectURL(imagePreviewUrl);
    }
    setImagePreviewUrl(null);
    setFormData({
      age: "",
      sex: "",
      tobacco: "",
      alcohol: "",
      lesion_site: "",
      magnification: "400x",
      research_question: "",
    });
    setAnalysisResult(null);
    setAnalysisError(null);
    setCurrentStep(1);
  };

  // Backend Base URL for heatmap images (empty string for same-origin proxy/production)
  const apiBaseUrl =
    import.meta.env.VITE_API_BASE_URL !== undefined &&
    import.meta.env.VITE_API_BASE_URL !== ""
      ? import.meta.env.VITE_API_BASE_URL
      : "";

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Page Header (Screen only) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border print:hidden">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Guided Histopathology Analysis
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            5-step clinical workflow: Upload patch &rarr; Clinical context &rarr; Review &rarr; Analyze &rarr; Diagnostic plate.
          </p>
        </div>

        {currentStep === 5 && (
          <Button
            variant="outline"
            size="sm"
            onClick={resetWorkflow}
            className="gap-1.5 self-start sm:self-auto print:hidden"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            New Assessment
          </Button>
        )}
      </div>

      {/* Progress Step Indicator (Steps 1 to 4 only, hidden on print) */}
      {currentStep < 5 && (
        <div className="grid grid-cols-4 gap-2 text-center text-xs print:hidden">
          {[
            { num: 1, label: "1. Upload Tile" },
            { num: 2, label: "2. Clinical Context" },
            { num: 3, label: "3. Review" },
            { num: 4, label: "4. Execution" },
          ].map((s) => (
            <div
              key={s.num}
              className={`p-2 rounded border font-medium transition-colors ${
                currentStep === s.num
                  ? "border-primary bg-primary/10 text-primary"
                  : currentStep > s.num
                  ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-700 dark:text-emerald-400"
                  : "border-border bg-card text-muted-foreground"
              }`}
            >
              {s.label}
            </div>
          ))}
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 1: Upload Histopathology Image                                        */}
      {/* ========================================================================= */}
      {currentStep === 1 && (
        <Card className="border-border">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <UploadCloud className="h-4 w-4 text-primary" />
              Step 1: Upload Oral Histopathology Tile
            </CardTitle>
            <CardDescription className="text-xs">
              Select or drop an oral mucosal biopsy tile (stained H&E section, 224×224 pixels recommended).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-colors ${
                isDragging
                  ? "border-primary bg-primary/5"
                  : imageFile
                  ? "border-emerald-500/50 bg-emerald-500/5"
                  : "border-border hover:border-primary/50 bg-card/50"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/tiff"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileChange(e.target.files[0]);
                  }
                }}
              />

              {imagePreviewUrl ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="relative group">
                    <img
                      src={imagePreviewUrl}
                      alt="Biopsy Tile Preview"
                      className="h-48 w-48 object-cover rounded-lg border border-border shadow-sm"
                    />
                    <div className="absolute inset-0 bg-slate-900/40 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center text-white text-xs font-medium">
                      Click to replace
                    </div>
                  </div>
                  <div className="text-xs font-semibold text-foreground">{imageFile?.name}</div>
                  <div className="text-[11px] text-muted-foreground">
                    Size: {((imageFile?.size || 0) / 1024).toFixed(1)} KB • Click to choose a different tile
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <div className="h-12 w-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-1">
                    <UploadCloud className="h-6 w-6" />
                  </div>
                  <div className="text-sm font-semibold text-foreground">
                    Drag and drop your histopathology tile here
                  </div>
                  <div className="text-xs text-muted-foreground max-w-sm">
                    Supports PNG, JPEG, and TIFF format. Maximum size 20 MB.
                  </div>
                  <Button variant="outline" size="sm" className="mt-3 gap-1.5 pointer-events-none">
                    <FileImage className="h-3.5 w-3.5" />
                    Browse Files
                  </Button>
                </div>
              )}
            </div>

            {/* Step 1 Actions */}
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-muted-foreground">
                {imageFile ? "Image ready for context input." : "Please select an image to continue."}
              </span>
              <Button
                disabled={!imageFile}
                onClick={() => setCurrentStep(2)}
                className="gap-1.5"
              >
                Continue to Context <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ========================================================================= */}
      {/* STEP 2: Enter Sample / Patient Information                                */}
      {/* ========================================================================= */}
      {currentStep === 2 && (
        <Card className="border-border">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Microscope className="h-4 w-4 text-primary" />
              Step 2: Clinical & Sample Information
            </CardTitle>
            <CardDescription className="text-xs">
              Provide context to guide literature retrieval and clinical report synthesis (all optional).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-foreground">Patient Age</label>
                <input
                  type="text"
                  placeholder="e.g. 58"
                  value={formData.age}
                  onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                  className="mt-1 w-full px-3 py-2 rounded-md border border-input bg-background text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-foreground">Biological Sex</label>
                <select
                  value={formData.sex}
                  onChange={(e) => setFormData({ ...formData, sex: e.target.value })}
                  className="mt-1 w-full px-3 py-2 rounded-md border border-input bg-background text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">Select or leave blank...</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-foreground">Anatomical Lesion Site</label>
                <input
                  type="text"
                  placeholder="e.g. Left lateral tongue border, buccal mucosa"
                  value={formData.lesion_site}
                  onChange={(e) => setFormData({ ...formData, lesion_site: e.target.value })}
                  className="mt-1 w-full px-3 py-2 rounded-md border border-input bg-background text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-foreground">Microscope Magnification</label>
                <select
                  value={formData.magnification}
                  onChange={(e) => setFormData({ ...formData, magnification: e.target.value })}
                  className="mt-1 w-full px-3 py-2 rounded-md border border-input bg-background text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="400x">400x (High Power Field)</option>
                  <option value="200x">200x (Medium Power Field)</option>
                  <option value="100x">100x (Overview)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-foreground">Tobacco / Areca Nut History</label>
                <input
                  type="text"
                  placeholder="e.g. Smoking (20 pack-years), Betel nut chewing"
                  value={formData.tobacco}
                  onChange={(e) => setFormData({ ...formData, tobacco: e.target.value })}
                  className="mt-1 w-full px-3 py-2 rounded-md border border-input bg-background text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-foreground">Alcohol History</label>
                <input
                  type="text"
                  placeholder="e.g. Occasional, Heavy, None"
                  value={formData.alcohol}
                  onChange={(e) => setFormData({ ...formData, alcohol: e.target.value })}
                  className="mt-1 w-full px-3 py-2 rounded-md border border-input bg-background text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-foreground">
                Research / Diagnostic Inquiry (Guiding RAG Retrieval)
              </label>
              <textarea
                rows={2}
                placeholder="e.g. Check for keratin pearl formation, cellular pleomorphism, and invasive dyskeratosis."
                value={formData.research_question}
                onChange={(e) => setFormData({ ...formData, research_question: e.target.value })}
                className="mt-1 w-full px-3 py-2 rounded-md border border-input bg-background text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring resize-none"
              />
            </div>

            {/* Step 2 Actions */}
            <div className="flex items-center justify-between pt-2">
              <Button variant="outline" size="sm" onClick={() => setCurrentStep(1)} className="gap-1.5">
                <ChevronLeft className="h-4 w-4" /> Back to Image
              </Button>
              <Button onClick={() => setCurrentStep(3)} className="gap-1.5">
                Review Submission <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ========================================================================= */}
      {/* STEP 3: Review Submitted Information                                       */}
      {/* ========================================================================= */}
      {currentStep === 3 && (
        <Card className="border-border">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              Step 3: Review Case Submission
            </CardTitle>
            <CardDescription className="text-xs">
              Verify tile and clinical context before transmitting to the AI pipeline.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
              {/* Image Preview */}
              <div className="flex flex-col items-center text-center p-4 border border-border rounded-lg bg-card/60">
                <img
                  src={imagePreviewUrl!}
                  alt="Biopsy Patch"
                  className="h-40 w-40 object-cover rounded-lg border border-border shadow-sm mb-2"
                />
                <span className="text-xs font-semibold text-foreground">{imageFile?.name}</span>
                <span className="text-[11px] text-muted-foreground">
                  {((imageFile?.size || 0) / 1024).toFixed(1)} KB
                </span>
              </div>

              {/* Clinical Context Review */}
              <div className="md:col-span-2 space-y-2 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2.5 rounded border border-border bg-card">
                    <span className="text-muted-foreground block text-[10px] uppercase">Age</span>
                    <span className="font-semibold text-foreground">{formData.age || "Not specified"}</span>
                  </div>
                  <div className="p-2.5 rounded border border-border bg-card">
                    <span className="text-muted-foreground block text-[10px] uppercase">Biological Sex</span>
                    <span className="font-semibold text-foreground">{formData.sex || "Not specified"}</span>
                  </div>
                  <div className="p-2.5 rounded border border-border bg-card">
                    <span className="text-muted-foreground block text-[10px] uppercase">Lesion Site</span>
                    <span className="font-semibold text-foreground">{formData.lesion_site || "Not specified"}</span>
                  </div>
                  <div className="p-2.5 rounded border border-border bg-card">
                    <span className="text-muted-foreground block text-[10px] uppercase">Magnification</span>
                    <span className="font-semibold text-foreground">{formData.magnification}</span>
                  </div>
                </div>

                <div className="p-2.5 rounded border border-border bg-card">
                  <span className="text-muted-foreground block text-[10px] uppercase">Risk Factors</span>
                  <span className="text-foreground">
                    Tobacco: {formData.tobacco || "None noted"} • Alcohol: {formData.alcohol || "None noted"}
                  </span>
                </div>

                {formData.research_question && (
                  <div className="p-2.5 rounded border border-border bg-card">
                    <span className="text-muted-foreground block text-[10px] uppercase">Inquiry</span>
                    <span className="text-foreground italic">{formData.research_question}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Step 3 Actions */}
            <div className="flex items-center justify-between pt-2">
              <Button variant="outline" size="sm" onClick={() => setCurrentStep(2)} className="gap-1.5">
                <ChevronLeft className="h-4 w-4" /> Edit Context
              </Button>
              <Button onClick={handleSubmitAnalysis} className="gap-1.5 shadow-sm">
                <Microscope className="h-4 w-4" /> Start AI Analysis
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ========================================================================= */}
      {/* STEP 4: Execution / Progress State                                        */}
      {/* ========================================================================= */}
      {currentStep === 4 && (
        <Card className="border-border">
          <CardContent className="py-12">
            {isAnalyzing ? (
              <div className="flex flex-col items-center justify-center text-center space-y-4">
                <div className="h-16 w-16 rounded-full bg-primary/10 text-primary flex items-center justify-center animate-pulse">
                  <Microscope className="h-8 w-8 animate-spin" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-foreground">
                    Analyzing Histopathology Tile...
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1 max-w-sm">
                    {analysisProgress}
                  </p>
                </div>
                <div className="w-64 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary animate-pulse w-3/4 rounded-full" />
                </div>
              </div>
            ) : analysisError ? (
              <div className="flex flex-col items-center justify-center text-center space-y-3">
                <div className="h-12 w-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center">
                  <AlertCircle className="h-6 w-6" />
                </div>
                <h3 className="text-base font-bold text-foreground">Analysis Pipeline Error</h3>
                <p className="text-xs text-muted-foreground max-w-md">{analysisError}</p>
                <div className="flex gap-2 pt-2">
                  <Button variant="outline" size="sm" onClick={() => setCurrentStep(3)}>
                    Return to Review
                  </Button>
                  <Button size="sm" onClick={handleSubmitAnalysis} className="gap-1.5">
                    <RotateCcw className="h-3.5 w-3.5" /> Retry Request
                  </Button>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}

      {/* ========================================================================= */}
      {/* STEP 5: Analysis Results Page                                             */}
      {/* ========================================================================= */}
      {currentStep === 5 && analysisResult && (
        <div className="space-y-6">
          {/* Print-Only Clinical Document Header */}
          <div className="hidden print:block pb-4 mb-4 border-b-2 border-slate-900">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-xl font-bold text-black uppercase tracking-tight">
                  Oral Cancer AI Decision Support Assessment
                </h1>
                <p className="text-xs text-slate-600 mt-0.5">
                  Computer-Assisted Histopathology Evaluation & Research Report
                </p>
              </div>
              <div className="text-right text-xs text-slate-700">
                <div>Case Identifier: <strong className="font-mono">{analysisResult.case_id}</strong></div>
                <div>Generated: {new Date().toLocaleString()}</div>
              </div>
            </div>
          </div>

          {/* Diagnostic Assessment Banner */}
          <Card
            className={`border-2 print:border-slate-400 print:shadow-none print:break-inside-avoid ${
              analysisResult.prediction.toLowerCase().includes("oscc") ||
              analysisResult.class_index === 1
                ? "border-rose-500/40 bg-rose-500/5 print:bg-white"
                : "border-emerald-500/40 bg-emerald-500/5 print:bg-white"
            }`}
          >
            <CardHeader className="pb-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge
                    variant={
                      analysisResult.prediction.toLowerCase().includes("oscc") ||
                      analysisResult.class_index === 1
                        ? "destructive"
                        : "success"
                    }
                    className="text-xs px-2.5 py-0.5 font-bold"
                  >
                    AI Indication: {analysisResult.prediction}
                  </Badge>
                  <span className="text-xs text-muted-foreground font-mono print:text-black">
                    Case: {analysisResult.case_id}
                  </span>
                </div>

                <div className="flex items-center gap-2 print:hidden">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.print()}
                    className="text-xs gap-1.5"
                  >
                    <Printer className="h-3.5 w-3.5" />
                    Print Summary
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-card border border-border print:border-slate-300">
                  <span className="text-[11px] text-muted-foreground block font-medium print:text-slate-600">
                    Model Classification Score
                  </span>
                  <span className="text-2xl font-bold text-foreground print:text-black">
                    {analysisResult.oscc_probability.toFixed(4)}
                  </span>
                  <span className="text-[10px] text-muted-foreground block mt-0.5 print:text-slate-500">
                    Continuous activation on 224×224 patch
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-card border border-border print:border-slate-300">
                  <span className="text-[11px] text-muted-foreground block font-medium print:text-slate-600">
                    Operating Boundary Cut-off
                  </span>
                  <span className="text-2xl font-bold text-primary font-mono print:text-black">
                    {analysisResult.threshold.toFixed(6)}
                  </span>
                  <span className="text-[10px] text-muted-foreground block mt-0.5 print:text-slate-500">
                    Calibrated F1 optimal threshold
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-card border border-border print:border-slate-300">
                  <span className="text-[11px] text-muted-foreground block font-medium print:text-slate-600">
                    Decision Confidence
                  </span>
                  <span className="text-2xl font-bold text-foreground print:text-black">
                    {analysisResult.confidence_percent.toFixed(1)}%
                  </span>
                  <span className="text-[10px] text-muted-foreground block mt-0.5 print:text-slate-500">
                    Distance from threshold boundary
                  </span>
                </div>
              </div>

              {/* Crucial Explanatory Clarification Note */}
              <div className="p-2.5 rounded bg-muted/60 text-[11px] text-muted-foreground flex items-start gap-2 print:border print:border-slate-300">
                <AlertCircle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5 print:hidden" />
                <span>
                  <strong>Clinical Metric Note:</strong> The classification score ({analysisResult.oscc_probability.toFixed(4)}) is a raw mathematical model activation on this specific biopsy tile. It is <strong>not</strong> an adjusted clinical patient probability. Histopathological sign-off by a qualified board-certified pathologist remains necessary.
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Sample & Patient Clinical Context Card */}
          <Card className="print:border-slate-300 print:shadow-none print:break-inside-avoid">
            <CardHeader className="pb-2.5">
              <CardTitle className="text-sm flex items-center gap-2">
                <User className="h-4 w-4 text-primary" />
                Patient & Sample Clinical Context
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div className="p-2 rounded bg-muted/30 border border-border/50">
                  <span className="text-[10px] uppercase text-muted-foreground block font-medium">Age</span>
                  <span className="font-semibold text-foreground">
                    {analysisResult.patient_context?.age || formData.age || "Not specified"}
                  </span>
                </div>
                <div className="p-2 rounded bg-muted/30 border border-border/50">
                  <span className="text-[10px] uppercase text-muted-foreground block font-medium">Sex</span>
                  <span className="font-semibold text-foreground">
                    {analysisResult.patient_context?.sex || formData.sex || "Not specified"}
                  </span>
                </div>
                <div className="p-2 rounded bg-muted/30 border border-border/50">
                  <span className="text-[10px] uppercase text-muted-foreground block font-medium">Lesion Site</span>
                  <span className="font-semibold text-foreground">
                    {analysisResult.patient_context?.lesion_site || formData.lesion_site || "Not specified"}
                  </span>
                </div>
                <div className="p-2 rounded bg-muted/30 border border-border/50">
                  <span className="text-[10px] uppercase text-muted-foreground block font-medium">Magnification</span>
                  <span className="font-semibold text-foreground">
                    {analysisResult.patient_context?.magnification || formData.magnification || "400x"}
                  </span>
                </div>
              </div>

              {(analysisResult.patient_context?.tobacco || formData.tobacco || analysisResult.patient_context?.alcohol || formData.alcohol) && (
                <div className="mt-2 text-xs text-muted-foreground p-2 rounded bg-muted/20 border border-border/40">
                  <strong className="text-foreground">Risk History:</strong> Tobacco:{" "}
                  {analysisResult.patient_context?.tobacco || formData.tobacco || "None noted"} • Alcohol:{" "}
                  {analysisResult.patient_context?.alcohol || formData.alcohol || "None noted"}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Explainability Visualizations (XAI Suite) */}
          <Card className="print:border-slate-300 print:shadow-none print:break-inside-avoid">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Microscope className="h-4 w-4 text-primary" />
                Explainable AI (XAI) Feature Attribution
              </CardTitle>
              <CardDescription className="text-xs">
                Inspect side-by-side morphological feature attributions across the four supported Explainable AI algorithms.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <XaiVisualizer
                xai={analysisResult.xai}
                originalImageUrl={imagePreviewUrl!}
                apiBaseUrl={apiBaseUrl}
              />
            </CardContent>
          </Card>

          {/* Scientific Literature Retrieval (FAISS RAG) */}
          {analysisResult.literature_evidence && analysisResult.literature_evidence.length > 0 && (
            <Card className="print:border-slate-300 print:shadow-none print:break-inside-avoid">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-blue-600" />
                  Peer-Reviewed Scientific Literature References (RAG)
                </CardTitle>
                <CardDescription className="text-xs">
                  Semantically matched scientific excerpts from the indexed oral oncology literature corpus.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {analysisResult.literature_evidence.map((chunk, idx) => {
                  const title = chunk.metadata?.title || chunk.title || `Scientific Publication Reference #${idx + 1}`;
                  const authors = chunk.metadata?.authors || chunk.authors;
                  const year = chunk.metadata?.year || chunk.year;
                  const sourceUrl = chunk.metadata?.source_url || chunk.source_url;
                  const relevance = typeof chunk.similarity === "number"
                    ? chunk.similarity
                    : typeof chunk.score === "number"
                    ? chunk.score
                    : null;

                  return (
                    <div
                      key={chunk.chunk_id || idx}
                      className="p-3 rounded-lg border border-border bg-card/50 space-y-1.5 print:border-slate-300 print:bg-white"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-semibold text-foreground print:text-black">
                          {title}
                        </span>
                        {relevance !== null && (
                          <Badge variant="outline" className="text-[10px]">
                            Relevance: {(relevance * 100).toFixed(1)}%
                          </Badge>
                        )}
                      </div>

                      {(authors || year) && (
                        <div className="text-[11px] text-muted-foreground print:text-slate-600">
                          {authors} {authors && year ? "·" : ""} {year}
                        </div>
                      )}

                      <p className="text-xs text-muted-foreground italic border-l-2 border-primary/40 pl-2 mt-1 print:text-slate-700">
                        "{chunk.text}"
                      </p>

                      {sourceUrl && (
                        <a
                          href={sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] text-primary hover:underline mt-1 print:hidden"
                        >
                          <span>View Journal Article</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          )}

          {/* Synthesized Clinical Research Report (Formatted Markdown) */}
          <Card className="print:border-slate-300 print:shadow-none print:break-inside-avoid">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="h-4 w-4 text-emerald-600" />
                Synthesized Research Report
              </CardTitle>
              <CardDescription className="text-xs">
                Generated by {analysisResult.report?.provider || "Groq"} ({analysisResult.report?.model || "llama-3.3-70b-versatile"}) with bounded clinical reasoning.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {analysisResult.report?.text ? (
                <div className="p-4 rounded-lg bg-card border border-border print:border-slate-300 print:bg-white">
                  <MarkdownReport content={analysisResult.report.text} />
                </div>
              ) : (
                <div className="p-4 rounded-lg bg-muted/40 text-xs text-muted-foreground">
                  Standard report synthesis fallback active. Pathological confirmation recommended.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Mandatory Clinical Disclaimer Footer */}
          <div className="p-4 rounded-lg border border-border bg-muted/30 text-muted-foreground text-xs leading-relaxed space-y-1 print:border-slate-400 print:bg-white print:text-black">
            <div className="font-semibold text-foreground flex items-center gap-1.5 print:text-black">
              <ShieldCheck className="h-4 w-4 text-primary shrink-0" />
              Clinical Decision Support Disclaimer
            </div>
            <p>
              This report is for investigational research and academic decision support only. It does <strong>not</strong> constitute a definitive medical diagnosis. Deep learning classifications and Explainable AI saliency heatmaps require independent correlation with whole-slide histopathology, immunohistochemistry, and clinical examination by a qualified pathologist.
            </p>
          </div>

          {/* Bottom Action Controls (Screen only) */}
          <div className="flex items-center justify-between pt-2 print:hidden">
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.print()}
              className="gap-1.5"
            >
              <Printer className="h-3.5 w-3.5" /> Print Consultation Summary
            </Button>
            <Button size="sm" onClick={resetWorkflow} className="gap-1.5">
              <RotateCcw className="h-3.5 w-3.5" /> Start Another Analysis
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
