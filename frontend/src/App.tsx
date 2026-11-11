import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
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

class RouteErrorBoundary extends React.Component<
  { resetKey: string; onReset: () => void; children: React.ReactNode },
  { hasError: boolean; errorMessage: string }
> {
  constructor(props: { resetKey: string; onReset: () => void; children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, errorMessage: "" };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, errorMessage: error?.message || "Unexpected rendering error" };
  }

  componentDidUpdate(prevProps: { resetKey: string }) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.hasError) {
      this.setState({ hasError: false, errorMessage: "" });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 max-w-xl mx-auto">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs text-center space-y-3">
            <h2 className="text-sm font-semibold text-slate-900">Unable to render this view</h2>
            <p className="text-xs text-slate-500">{this.state.errorMessage}</p>
            <div className="pt-2 flex items-center justify-center gap-2">
              <button
                onClick={() => {
                  this.setState({ hasError: false, errorMessage: "" });
                  this.props.onReset();
                }}
                className="px-3.5 py-1.5 rounded-md text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
              >
                Return to Dashboard
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

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

  const handleBack = () => {
    const idx = typeof window !== "undefined" ? window.history.state?.idx : 0;
    if (typeof idx === "number" && idx > 0) {
      navigate(-1);
    } else if (location.pathname.startsWith("/contracts/")) {
      navigate("/contracts");
    } else {
      navigate("/");
    }
  };

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
          onBack={location.pathname !== "/" ? handleBack : undefined}
        />
        <main className="flex-1 pb-12 overflow-y-auto">
          <RouteErrorBoundary resetKey={location.pathname} onReset={() => navigate("/")}>
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
              <Route path="/login" element={<Navigate to="/" replace />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </RouteErrorBoundary>
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
