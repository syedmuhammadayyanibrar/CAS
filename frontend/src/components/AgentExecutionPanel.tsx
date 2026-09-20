import React from "react";
import { ContractExecutionState } from "../api/client";
import { AgentJourney } from "./execution/AgentJourney";

export interface AgentExecutionPanelProps {
  execution: ContractExecutionState | null;
  isAnalyzing?: boolean;
  onReviewDecision?: () => void;
  className?: string;
}

export function AgentExecutionPanel(props: AgentExecutionPanelProps) {
  return <AgentJourney {...props} />;
}
