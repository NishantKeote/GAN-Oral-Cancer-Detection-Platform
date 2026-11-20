export type Theme = "light" | "dark";

export interface NavigationItem {
  title: string;
  href: string;
  icon: string;
  badge?: string;
  description?: string;
}

export interface HealthServicesStatus {
  cnn_loaded?: boolean;
  faiss_loaded?: boolean;
  neo4j_connected?: boolean;
  groq_configured?: boolean;
  [key: string]: boolean | undefined;
}

export interface HealthStatus {
  status: "ok" | "healthy" | "degraded" | "error";
  phase?: string;
  model?: string;
  threshold?: number;
  xai_methods?: string[];
  services?: HealthServicesStatus;
  version?: string;
  timestamp?: string;
}

export interface PatientFormContext {
  age: string;
  sex: string;
  tobacco: string;
  alcohol: string;
  lesion_site: string;
  magnification: string;
  research_question: string;
}

export interface XAIMethodStats {
  min: number;
  max: number;
  mean: number;
  std: number;
  q90: number;
  fraction_at_or_above_0_5: number;
}

export interface XAIMethodResult {
  status: string;
  heatmap_path?: string;
  heatmap_url?: string;
  overlay_path?: string;
  overlay_url?: string;
  normalization?: string;
  statistics?: XAIMethodStats;
  error?: string;
}

export interface XAISummary {
  target: string;
  prediction_equivalence_verified: boolean;
  methods: Record<string, XAIMethodResult>;
  pairwise_similarity?: Record<string, any>;
  scope_note?: string;
}

export interface LiteratureEvidenceChunk {
  chunk_id: string;
  paper_id?: string;
  score?: number;
  similarity?: number;
  title?: string;
  authors?: string;
  year?: number | string;
  source_url?: string;
  text: string;
  metadata?: {
    title?: string;
    authors?: string;
    year?: number | string;
    source_url?: string;
    chunk_index?: number;
    [key: string]: any;
  };
}

export interface GroqReport {
  status: string;
  provider: string;
  model: string;
  generated_at: string;
  text?: string;
  error?: {
    code: string;
    message: string;
  };
}

export interface AnalysisResponse {
  case_id: string;
  filename: string;
  patient_context: Record<string, string>;
  research_question?: string;
  prediction: string;
  class_index: number;
  oscc_probability: number;
  threshold: number;
  decision_rule: string;
  confidence: number;
  confidence_percent: number;
  xai: XAISummary;
  graph_saved: boolean;
  graph_context: Array<Record<string, any>>;
  retrieval_query: string;
  literature_evidence: LiteratureEvidenceChunk[];
  errors: Array<Record<string, any>>;
  scope_note: string;
  report: GroqReport;
}
