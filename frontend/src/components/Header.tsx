import React from "react";
import { Plus, Menu, X, LogOut, Shield, User, Sparkles, ArrowLeft } from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface HeaderProps {
  title: string;
  subtitle?: string;
  onNewContract?: () => void;
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
  onBack?: () => void;
  actions?: React.ReactNode;
}

export function Header({
  title,
  subtitle,
  onNewContract,
  onToggleSidebar,
  isSidebarOpen,
  onBack,
  actions,
}: HeaderProps) {
  const { user, isGuest, logout } = useAuth();

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

        {onBack && (
          <button
            onClick={onBack}
            aria-label="Go back"
            title="Go back to previous page"
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 hover:text-blue-600 transition-all shadow-2xs cursor-pointer group shrink-0"
          >
            <ArrowLeft className="w-4 h-4 text-slate-500 group-hover:text-blue-600 transition-colors" />
            <span className="text-xs font-semibold select-none hidden sm:inline">Back</span>
          </button>
        )}

        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold text-[#111827] truncate">{title}</h1>
            {isGuest && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                Guest Mode
              </span>
            )}
          </div>
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
            title="Upload new contract"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-medium shadow-xs transition-colors cursor-pointer bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Upload Contract</span>
            <span className="sm:hidden">Upload</span>
          </button>
        )}

        {/* User Pill / Logout */}
        {user && (
          <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
            <div className="hidden md:flex flex-col text-right">
              <span className="text-xs font-medium text-slate-800 leading-tight">
                {user.name || user.email}
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                {user.role}
              </span>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 rounded-md text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
