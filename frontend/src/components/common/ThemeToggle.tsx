import React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { Button } from "@/components/ui/Button";

export const ThemeToggle: React.FC<{ className?: string }> = ({
  className,
}) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className={className}
      title={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
      aria-label="Toggle theme"
    >
      {theme === "light" ? (
        <Moon className="h-4 w-4 text-slate-700 transition-transform duration-200" />
      ) : (
        <Sun className="h-4 w-4 text-amber-400 transition-transform duration-200" />
      )}
    </Button>
  );
};
