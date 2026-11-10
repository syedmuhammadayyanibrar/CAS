import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { LoginPage } from "./views/LoginPage";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { UploadModal } from "./components/UploadModal";
import { DashboardView } from "./views/DashboardView";
import { PortfolioView } from "./views/PortfolioView";
import { ContractWorkspaceView } from "./views/ContractWorkspaceView";
import { ApprovalsView } from "./views/ApprovalsView";
import { SocietiesView } from "./views/SocietiesView";
import { AutomationsView } from "./views/AutomationsView";
import { MemoryView } from "./views/MemoryView";
import { DemoWorkspaceView } from "./views/DemoWorkspaceView";
import { EvaluationCenterView } from "./views/EvaluationCenterView";
import { fetchReviews } from "./api/client";

function AppLayout() {
  const { isAuthenticated, isLoading, isGuest } = useAuth();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [pendingReviewsCount, setPendingReviewsCount] = useState(0);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (isAuthenticated && !isGuest) {
      fetchReviews("PENDING")
        .then((data) => setPendingReviewsCount(data.length))
        .catch(() => {});
    }
  }, [location.pathname, isAuthenticated, isGuest]);

  // Guests may use the dashboard, contracts (upload & workspace), demo and evaluation areas
  useEffect(() => {
    const allowedGuestRoute =
      ["/", "/contracts", "/demo", "/evaluation"].includes(location.pathname) ||
      location.pathname.startsWith("/contracts/");
    if (isGuest && !allowedGuestRoute) {
      navigate("/", { replace: true });
    }
  }, [isGuest, location.pathname, navigate]);

  // Automatically close sidebar when navigating to a new route
  useEffect(() => {
    setIsSidebarOpen(false);
  }, [location.pathname]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center text-slate-400 text-xs">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span>Verifying credentials & session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const getHeaderInfo = (): { title: string; subtitle?: string } => {
    const path = location.pathname;
    if (path === "/") {
      return {
        title: "Dashboard",
        subtitle: "Contract Operations & Multi-Agent Society Overview",
      };
    } else if (path === "/contracts") {
      return {
        title: "Contracts",
        subtitle: "Enterprise Portfolio & Agreement Management",
      };
    } else if (path.startsWith("/contracts/")) {
      return {
        title: "Contract Workspace",
        subtitle: "Multi-Agent Synthesis, Redlines & Audit",
      };
    } else if (path === "/approvals") {
      return {
        title: "Approvals",
        subtitle: "Human-in-the-Loop Review Gates",
      };
    } else if (path === "/societies") {
      return {
        title: "Agent Societies",
        subtitle: "Federated Multi-Agent Topologies & Capabilities",
      };
    } else if (path === "/automations") {
      return {
        title: "Automation Center",
        subtitle: "Fastn Connected Triggers & External Integrations",
      };
    } else if (path === "/memory") {
      return {
        title: "Memory & Precedent",
        subtitle: "Persistent Precedent Store & Organizational Grounding",
      };
    } else if (path === "/demo") {
      return {
        title: "Execution Demo",
        subtitle: "15-Stage Interactive Multi-Agent Walkthrough",
      };
    } else if (path === "/evaluation") {
      return {
        title: "Evaluation Center",
        subtitle: "30-Case Benchmark Suite & Ground-Truth Verification",
      };
    }
    return { title: "Contract Agentic Society" };
  };

  const headerInfo = getHeaderInfo();

  return (
    <div className="flex min-h-screen bg-[#F7F8FA] text-[#111827]">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        pendingApprovalsCount={pendingReviewsCount}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          title={headerInfo.title}
          subtitle={headerInfo.subtitle}
          onNewContract={() => setIsModalOpen(true)}
          onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
          isSidebarOpen={isSidebarOpen}
        />
        <main className="flex-1 pb-12 overflow-y-auto">
          <Routes>
            <Route path="/" element={<DashboardView />} />
            <Route path="/contracts" element={<PortfolioView />} />
            <Route path="/contracts/:id" element={<ContractWorkspaceView />} />
            <Route path="/approvals" element={<ApprovalsView />} />
            <Route path="/societies" element={<SocietiesView />} />
            <Route path="/automations" element={<AutomationsView />} />
            <Route path="/memory" element={<MemoryView />} />
            <Route path="/demo" element={<DemoWorkspaceView />} />
            <Route path="/evaluation" element={<EvaluationCenterView />} />
          </Routes>
        </main>
      </div>

      <UploadModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={(contractId) => {
          navigate(`/contracts/${contractId}`);
        }}
      />
    </div>
  );
}

export default function App() {
  const basename = window.location.pathname.startsWith("/ui") ? "/ui" : "";
  return (
    <BrowserRouter basename={basename}>
      <AuthProvider>
        <AppLayout />
      </AuthProvider>
    </BrowserRouter>
  );
}
