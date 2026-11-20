import React, { useState } from "react";
import { Link, useLocation, Outlet } from "react-router-dom";
import {
  Home,
  Microscope,
  FileText,
  History,
  BookOpen,
  Info,
  Settings,
  Menu,
  X,
  ShieldCheck,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { SystemStatusBadge } from "@/components/common/SystemStatusBadge";

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Home", path: "/", icon: Home },
  { label: "New Analysis", path: "/analyze", icon: Microscope },
  { label: "My Reports", path: "/reports", icon: FileText },
  { label: "Analysis History", path: "/history", icon: History },
  { label: "Research & Knowledge Graph", path: "/research", icon: BookOpen },
  { label: "About the Platform", path: "/about", icon: Info },
  { label: "Settings", path: "/settings", icon: Settings },
];

export const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row">
      {/* Mobile Backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-slate-900/50 z-40 md:hidden backdrop-blur-sm print:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        className={cn(
          "fixed md:static inset-y-0 left-0 z-50 w-64 bg-card border-r border-border flex flex-col transition-transform duration-200 ease-in-out md:translate-x-0 print:hidden",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Sidebar Brand Header */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-border">
          <Link
            to="/"
            className="flex items-center gap-2.5 font-semibold text-foreground tracking-tight"
            onClick={() => setSidebarOpen(false)}
          >
            <div className="h-8 w-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-bold">
              <Microscope className="h-4 w-4" />
            </div>
            <div>
              <span className="text-base font-bold text-foreground">OralOnco</span>
              <span className="text-xs text-primary font-medium ml-1">AI</span>
            </div>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-1 rounded-md text-muted-foreground hover:text-foreground md:hidden"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
            Clinical Assessment Suite
          </div>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.path === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(item.path);

            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0",
                    isActive ? "text-primary-foreground" : "text-muted-foreground"
                  )}
                />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Diagnostic Decision Support Disclaimer Footer */}
        <div className="p-4 border-t border-border bg-muted/20">
          <div className="flex items-start gap-2">
            <ShieldCheck className="h-4 w-4 text-primary mt-0.5 shrink-0" />
            <div className="text-[11px] leading-tight text-muted-foreground">
              <span className="font-semibold text-foreground block">
                Investigational CDSS
              </span>
              Pathologist review mandatory for clinical decisions.
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 print:block">
        {/* Global Top Header */}
        <header className="h-16 border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-30 flex items-center justify-between px-4 sm:px-6 print:hidden">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 rounded-md text-muted-foreground hover:bg-accent hover:text-foreground md:hidden"
              aria-label="Open navigation menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="hidden sm:block">
              <span className="text-xs font-medium text-muted-foreground">
                Oral Cancer AI Assessment & Reporting Platform
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <SystemStatusBadge />
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hidden lg:flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
              title="OpenAPI Backend Documentation"
            >
              <span>API Docs</span>
              <ExternalLink className="h-3 w-3" />
            </a>
            <div className="h-4 w-px bg-border hidden sm:block" />
            <ThemeToggle />
          </div>
        </header>

        {/* Page Content Outlet */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto print:p-0 print:m-0 print:max-w-none">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
