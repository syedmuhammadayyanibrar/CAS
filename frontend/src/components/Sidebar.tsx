import React, { useEffect } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  CheckSquare,
  Network,
  Zap,
  Database,
  PlayCircle,
  BarChart2,
  X,
} from "lucide-react";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  pendingApprovalsCount?: number;
}

export function Sidebar({
  isOpen,
  onClose,
  pendingApprovalsCount = 0,
}: SidebarProps) {
  const navItems = [
    { to: "/", label: "Dashboard", icon: LayoutDashboard },
    { to: "/contracts", label: "Contracts", icon: FileText },
    { to: "/approvals", label: "Approvals", icon: CheckSquare, badge: pendingApprovalsCount },
    { to: "/societies", label: "Societies", icon: Network },
    { to: "/automations", label: "Automations", icon: Zap },
    { to: "/memory", label: "Memory", icon: Database },
    { to: "/demo", label: "Interactive Demo", icon: PlayCircle },
    { to: "/evaluation", label: "Evaluation", icon: BarChart2 },
  ];

  // Close sidebar when Escape key is pressed
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Lock body scroll when sidebar drawer is open on mobile
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  return (
    <>
      {/* Backdrop overlay for tap-to-show behavior */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40 transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Slide-in Navigation Drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 sm:w-64 bg-white border-r border-[#E5E7EB] flex flex-col shrink-0 h-full shadow-2xl transition-transform duration-300 ease-in-out ${
          isOpen ? "translate-x-0" : "-translate-x-full pointer-events-none"
        }`}
        aria-label="Platform Navigation"
      >
        {/* Brand Header with Close Button */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-[#E5E7EB] gap-3 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-xs shadow-xs">
              CAS
            </div>
            <div>
              <div className="text-sm font-semibold text-[#111827] tracking-tight">
                Contract Agentic Society
              </div>
              <div className="text-[11px] text-[#6B7280]">
                Autonomous Legal Ops
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close sidebar"
            className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
            title="Close sidebar (Esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1 flex-1 overflow-y-auto">
          <div className="px-3 py-1.5 text-[10px] font-semibold text-[#9CA3AF] uppercase tracking-wider">
            Platform Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2.5 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-2 border-blue-600 rounded-l-none"
                      : "text-slate-600 hover:text-[#111827] hover:bg-slate-50"
                  }`
                }
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4 shrink-0 text-current" />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && item.badge > 0 ? (
                  <span className="px-1.5 py-0.5 bg-amber-50 border border-amber-200 text-amber-800 text-[10px] rounded-full font-bold">
                    {item.badge}
                  </span>
                ) : null}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer System Status */}
        <div className="p-4 border-t border-[#E5E7EB] bg-slate-50/70 flex items-center justify-between shrink-0">
          <span className="text-slate-500 text-xs">System Status</span>
          <span className="inline-flex items-center gap-1.5 text-emerald-700 text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Operational
          </span>
        </div>
      </aside>
    </>
  );
}
