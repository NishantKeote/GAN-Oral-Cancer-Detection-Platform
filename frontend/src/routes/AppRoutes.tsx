import React from "react";
import { Routes, Route } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { NewAnalysisPage } from "@/pages/NewAnalysisPage";
import { ReportsPage } from "@/pages/ReportsPage";
import { AnalysisHistoryPage } from "@/pages/AnalysisHistoryPage";
import { KnowledgeGraphPage } from "@/pages/KnowledgeGraphPage";
import { AboutPage } from "@/pages/AboutPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="analyze" element={<NewAnalysisPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="history" element={<AnalysisHistoryPage />} />
        <Route path="research" element={<KnowledgeGraphPage />} />
        <Route path="about" element={<AboutPage />} />
        <Route path="settings" element={<SettingsPage />} />
        {/* Legacy redirect aliases */}
        <Route path="knowledge-graph" element={<KnowledgeGraphPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};
