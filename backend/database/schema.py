from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    JSON,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ContractModel(Base):
    __tablename__ = "contracts"

    id = Column(String(100), primary_key=True)
    title = Column(String(255), nullable=False, default="Untitled Contract")
    raw_text = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="INTAKE")  # INTAKE, ANALYZED, SIGNED, ACTIVE, RENEWAL_DUE
    governing_law = Column(String(100), nullable=True)
    effective_date = Column(String(50), nullable=True)
    expiration_date = Column(String(50), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ContractGraphModel(Base):
    __tablename__ = "contract_graphs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(100), ForeignKey("contracts.id"), unique=True, nullable=False)
    graph_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RiskReportModel(Base):
    __tablename__ = "risk_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(100), ForeignKey("contracts.id"), nullable=False)
    overall_score = Column(Float, default=0.0)
    requires_escalation = Column(Boolean, default=False)
    report_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ComplianceReportModel(Base):
    __tablename__ = "compliance_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(100), ForeignKey("contracts.id"), nullable=False)
    policy_name = Column(String(255), default="Corporate Policy")
    overall_status = Column(String(50), default="COMPLIANT")
    report_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class NegotiationStrategyModel(Base):
    __tablename__ = "negotiation_strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(100), ForeignKey("contracts.id"), nullable=False)
    primary_objective = Column(Text, nullable=False)
    strategy_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ObligationScheduleModel(Base):
    __tablename__ = "obligation_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(100), ForeignKey("contracts.id"), unique=True, nullable=False)
    total_obligations = Column(Integer, default=0)
    schedule_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DisputeAssessmentModel(Base):
    __tablename__ = "dispute_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(100), ForeignKey("contracts.id"), nullable=False)
    overall_dispute_risk = Column(String(50), default="MEDIUM")
    assessment_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CASMessageModel(Base):
    __tablename__ = "cas_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(100), unique=True, nullable=False)
    contract_id = Column(String(100), nullable=False)
    source_system = Column(String(100), nullable=False)
    target_system = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    confidence = Column(Float, default=1.0)
    priority = Column(String(50), default="MEDIUM")
    message_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(100), unique=True, nullable=False)
    contract_id = Column(String(100), nullable=True)
    society_or_source = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    details_json = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class HumanReviewModel(Base):
    __tablename__ = "human_reviews"

    review_id = Column(String(100), primary_key=True)
    contract_id = Column(String(100), ForeignKey("contracts.id"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING")
    reviewer_id = Column(String(100), nullable=True)
    decision_notes = Column(Text, nullable=True)
    review_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)


class CASMemoryModel(Base):
    __tablename__ = "cas_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_type = Column(String(50), nullable=False)  # CONTRACT, DECISION, NEGOTIATION, DISPUTE, CONFLICT
    reference_id = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False)
    content_json = Column(JSON, nullable=False)
    context_tags = Column(String(255), nullable=True)  # Comma-separated search tags
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FastnExecutionModel(Base):
    __tablename__ = "fastn_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(100), unique=True, nullable=False, index=True)
    workflow_slug = Column(String(100), nullable=False, index=True)
    workflow_id = Column(String(100), nullable=True)
    contract_id = Column(String(100), nullable=True, index=True)
    direction = Column(String(20), default="OUTBOUND", nullable=False)  # OUTBOUND, INBOUND
    connector = Column(String(50), nullable=False)  # slack, google_calendar, airtable, google_drive, webhook, grc_portal
    status = Column(String(50), default="SUCCESS", nullable=False)  # SUCCESS, FAILED, PENDING, RETRYING
    input_summary = Column(JSON, nullable=False, default=dict)
    output_summary = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    correlation_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class EvaluationRunModel(Base):
    __tablename__ = "evaluation_runs"

    run_id = Column(String(100), primary_key=True)
    run_number = Column(Integer, nullable=False, default=1)
    dataset_version = Column(String(50), default="1.0.0")
    number_of_cases = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    metrics_json = Column(JSON, nullable=False, default=dict)
    model_provider = Column(String(100), default="Google Gemini 2.5 Flash")
    cas_version = Column(String(50), default="1.0.0")
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EvaluationCaseResultModel(Base):
    __tablename__ = "evaluation_case_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), ForeignKey("evaluation_runs.run_id"), nullable=False, index=True)
    case_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), default="normal")
    status = Column(String(50), default="PASSED")  # PASSED, FAILED
    expected_json = Column(JSON, nullable=False, default=dict)
    actual_json = Column(JSON, nullable=False, default=dict)
    failure_reason = Column(Text, nullable=True)
    society = Column(String(100), nullable=True)
    workflow_score = Column(Float, default=100.0)
    execution_time_seconds = Column(Float, default=0.0)
    execution_trace_json = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

