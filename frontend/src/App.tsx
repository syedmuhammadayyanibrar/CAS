import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
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
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [pendingReviewsCount, setPendingReviewsCount] = useState(0);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    fetchReviews("PENDING")
      .then((data) => setPendingReviewsCount(data.length))
      .catch(() => {});
  }, [location.pathname]);

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
      <Sidebar pendingApprovalsCount={pendingReviewsCount} />
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          title={headerInfo.title}
          subtitle={headerInfo.subtitle}
          onNewContract={() => setIsModalOpen(true)}
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
      <AppLayout />
    </BrowserRouter>
  );
}
