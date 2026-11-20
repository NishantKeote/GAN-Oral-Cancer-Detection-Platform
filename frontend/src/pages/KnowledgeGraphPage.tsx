import React from "react";
import { Network, Database, BookOpen, Layers } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export const KnowledgeGraphPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Biomedical Knowledge Graph & Literature Index
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Explore structured disease ontology entities and peer-reviewed literature vector embeddings.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Dense Literature Index</CardDescription>
            <CardTitle className="text-base flex items-center justify-between">
              <span>FAISS IndexFlatIP</span>
              <BookOpen className="h-4 w-4 text-blue-600" />
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground space-y-2">
            <div><strong>Vectors:</strong> 189 chunks indexed</div>
            <div><strong>Embedding Model:</strong> all-MiniLM-L6-v2 (384-dim)</div>
            <div><strong>File Size:</strong> ~290 KB serialized</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Structured Graph Store</CardDescription>
            <CardTitle className="text-base flex items-center justify-between">
              <span>Neo4j AuraDB</span>
              <Database className="h-4 w-4 text-emerald-600" />
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground space-y-2">
            <div><strong>Protocol:</strong> bolt+s / neo4j+s</div>
            <div><strong>Entities:</strong> Disease, RiskFactor, Criteria</div>
            <div><strong>Resilience:</strong> Graceful degradation active</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs">Graph-Augmented LLM</CardDescription>
            <CardTitle className="text-base flex items-center justify-between">
              <span>Groq Report Engine</span>
              <Network className="h-4 w-4 text-primary" />
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground space-y-2">
            <div><strong>Model:</strong> llama-3.3-70b-versatile</div>
            <div><strong>Role:</strong> Clinical synthesis & evidence bounding</div>
            <div><strong>Fallback:</strong> Deterministic template fallback</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" />
            Interactive Graph Visualizer (Phase 2 Roadmap)
          </CardTitle>
          <CardDescription>
            Visual exploration of disease relationships, histological subtypes, and literature citations.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80 border border-dashed border-border rounded-lg flex flex-col items-center justify-center text-center p-6 bg-card/40">
            <Network className="h-12 w-12 text-muted-foreground/50 mb-3" />
            <h4 className="text-sm font-semibold text-foreground">
              Ontology Explorer Canvas
            </h4>
            <p className="text-xs text-muted-foreground max-w-md mt-1">
              Interactive node graph visualization powered by Cytoscape / ForceGraph will be connected in Phase 2C.
            </p>
            <div className="flex gap-2 mt-4">
              <Badge variant="outline">(:Disease)</Badge>
              <Badge variant="outline">(:RiskFactor)</Badge>
              <Badge variant="outline">(:DiagnosticCriteria)</Badge>
              <Badge variant="outline">(:Case)</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
