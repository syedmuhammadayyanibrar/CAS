import React from "react";
import { Plus, Menu, X } from "lucide-react";

interface HeaderProps {
  title: string;
  subtitle?: string;
  onNewContract?: () => void;
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
  actions?: React.ReactNode;
}

export function Header({
  title,
  subtitle,
  onNewContract,
  onToggleSidebar,
  isSidebarOpen,
  actions,
}: HeaderProps) {
  return (
    <header className="h-16 border-b border-[#E5E7EB] bg-white/95 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-3 min-w-0">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            aria-label={isSidebarOpen ? "Close navigation menu" : "Open navigation menu"}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 hover:text-blue-600 transition-all shadow-2xs cursor-pointer group shrink-0"
            title={isSidebarOpen ? "Tap to hide sidebar" : "Tap to show sidebar"}
          >
            {isSidebarOpen ? (
              <X className="w-4 h-4 text-slate-500 group-hover:text-blue-600 transition-colors" />
            ) : (
              <Menu className="w-4 h-4 text-slate-500 group-hover:text-blue-600 transition-colors" />
            )}
            <span className="text-xs font-semibold select-none">
              {isSidebarOpen ? "Close" : "Menu"}
            </span>
          </button>
        )}

        <div className="min-w-0">
          <h1 className="text-sm font-semibold text-[#111827] truncate">{title}</h1>
          {subtitle && (
            <p className="text-[11px] text-[#6B7280] truncate hidden sm:block">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        {actions}

        {onNewContract && (
          <button
            onClick={onNewContract}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-medium shadow-xs transition-colors cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Upload Contract</span>
            <span className="sm:hidden">Upload</span>
          </button>
        )}
      </div>
    </header>
  );
}
