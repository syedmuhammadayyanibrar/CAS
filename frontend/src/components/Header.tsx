import React from "react";
import { Plus } from "lucide-react";

interface HeaderProps {
  title: string;
  subtitle?: string;
  onNewContract?: () => void;
  actions?: React.ReactNode;
}

export function Header({ title, subtitle, onNewContract, actions }: HeaderProps) {
  return (
    <header className="h-16 border-b border-[#E5E7EB] bg-white/95 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h1 className="text-sm font-semibold text-[#111827]">{title}</h1>
        {subtitle && <p className="text-[11px] text-[#6B7280]">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {actions}

        {onNewContract && (
          <button
            onClick={onNewContract}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-medium shadow-xs transition-colors cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Upload Contract</span>
          </button>
        )}
      </div>
    </header>
  );
}
