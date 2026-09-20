import asyncio
import os
import sys
import json
from rich.console import Console
from rich.panel import Panel

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.integrations.fastn_client import fastn_client
from backend.director.coordinator import cas_director
from backend.systems.contract_intelligence.system import contract_intelligence_system
from backend.systems.risk_intelligence.system import risk_intelligence_system
from backend.systems.negotiation_intelligence.system import negotiation_intelligence_system
from backend.systems.compliance_intelligence.system import compliance_intelligence_system
from backend.systems.obligation_intelligence.system import obligation_intelligence_system
from backend.systems.dispute_intelligence.system import dispute_intelligence_system
from backend.memory.cas_memory import cas_memory

console = Console(legacy_windows=False)


async def run_end_to_end_demo():
    contract_file = os.path.join(os.path.dirname(__file__), "../contracts/enterprise_saas_vendor_contract.txt")
    policy_file = os.path.join(os.path.dirname(__file__), "../policies/corporate_compliance_policy.json")

    with open(contract_file, "r", encoding="utf-8") as f:
        contract_text = f.read()

    cid = "CTR-DEMO-2026-SAAS"

    console.print(Panel.fit(
        "[bold cyan]CONTRACT AGENTIC SOCIETY (CAS)[/bold cyan]\n"
        "[dim]Autonomous Multi-Agent Federation & Negotiation Mesh[/dim]\n"
        "[green]Bidirectional Nervous System: Fastn MCP Platform (10 Workflows)[/green]\n"
        "[yellow]Sole Cognitive & Reasoning Engine: Google Gemini API[/yellow]",
        border_style="blue"
    ))

    # STAGE 1: Contract Intake via Fastn
    console.print("\n[bold yellow]> STAGE 1: Contract Intake through Fastn Public Inbound Webhook[/bold yellow]")
    s1 = await fastn_client.trigger_intake_webhook({
        "contractId": cid,
        "documentName": "enterprise_saas_vendor_contract.pdf",
        "source": "google_drive",
        "content": contract_text[:500]
    })
    console.print(f"[green][OK] Fastn Inbound Intake Triggered:[/green] Status={s1.get('status')}")

    # STAGE 2: Contract Intelligence Deconstruction
    console.print("\n[bold yellow]> STAGE 2: Contract Intelligence Deconstruction (System 1)[/bold yellow]")
    graph = await contract_intelligence_system.analyze_contract(contract_text, cid)
    console.print(f"[green][OK] Semantic Graph Built:[/green] {len(graph.clauses)} clauses, {len(graph.parties)} parties.")

    # STAGE 3: Risk Intelligence Adversarial Debate
    console.print("\n[bold yellow]> STAGE 3: Risk Intelligence Adversarial Debate (System 2)[/bold yellow]")
    risk = await risk_intelligence_system.analyze_risk(contract_text, cid)
    console.print(f"[green][OK] Adversarial Debate Completed:[/green] Score={risk.overall_risk_score:.2f}, Escalation={risk.requires_human_escalation}")

    # STAGE 4: Fastn Risk Escalation
    console.print("\n[bold yellow]> STAGE 4: Fastn Risk Escalation to Slack #legal-contract-risks[/bold yellow]")
    s4 = await fastn_client.execute_risk_escalation(
        contract_id=cid,
        severity="CRITICAL",
        risky_clause="Section 8.2 Asymmetric Cap",
        consequence="Uncapped liability exposure with $50k Vendor shield",
        evidence="Total liability shall be uncapped.",
        channel="#legal-contract-risks"
    )
    console.print(f"[green][OK] Fastn Slack Alert Dispatched:[/green] Status={s4.get('status')}")

    # STAGE 5: Negotiation Strategy & Redlines
    console.print("\n[bold yellow]> STAGE 5: Negotiation Intelligence Strategy (System 3)[/bold yellow]")
    strat = await negotiation_intelligence_system.plan_negotiation(
        contract=graph,
        objective="Cap liability at 12 months fees and delete uncapped indemnity.",
        contract_id=cid
    )
    console.print(f"[green][OK] Negotiation Redlines Formulated:[/green] {len(strat.positions)} redline positions generated.")

    # STAGE 6: Compliance Policy Audit
    console.print("\n[bold yellow]> STAGE 6: Compliance Intelligence Audit (System 4)[/bold yellow]")
    comp = await compliance_intelligence_system.audit_compliance(contract_text, policy_file, cid)
    console.print(f"[green][OK] Compliance Audit Complete:[/green] Status={comp.overall_status}, Violations={comp.violations_count}")

    # STAGE 7: Fastn Compliance Escalation
    console.print("\n[bold yellow]> STAGE 7: Fastn Compliance Breach Escalation[/bold yellow]")
    s7 = await fastn_client.execute_compliance_escalation(
        contract_id=cid,
        policy_name="Corporate Standard Vendor Policy v2.4",
        violations_count=comp.violations_count,
        violations=[v.model_dump() if hasattr(v, "model_dump") else v for v in comp.violations]
    )
    console.print(f"[green][OK] Fastn Compliance Escalated:[/green] Status={s7.get('status')}")

    # STAGE 8: CAS Director Dynamic Mesh Orchestration
    console.print("\n[bold yellow]> STAGE 8: CAS Director Dynamic Mesh Orchestration & Conflict Arbitration[/bold yellow]")
    mesh = await cas_director.orchestrate_mesh(
        contract_text=contract_text,
        contract_id=cid,
        commercial_objective="Cap liability at 12 months fees and delete uncapped indemnity.",
        policy_path=policy_file
    )
    console.print(f"[green][OK] Mesh Orchestration Completed:[/green] Conflicts={len(mesh.get('detected_conflicts', []))}, Status={mesh.get('status')}")

    # STAGE 9: Fastn HITL Approval Dispatch
    console.print("\n[bold yellow]> STAGE 9: Fastn Human-In-The-Loop Approval Dispatch (Slack + Email)[/bold yellow]")
    s9 = await fastn_client.execute_approval_dispatch(
        contract_id=cid,
        reason="Uncapped customer liability and compliance variances require executive sign-off.",
        requested_action="Approve bilateral 12-month cap compromise.",
        agent_conclusions=["Risk: CRITICAL (0.85)", "Compliance: 2 Violations"],
        reviewer_email="general_counsel@acme.com"
    )
    console.print(f"[green][OK] Fastn HITL Request Dispatched:[/green] Status={s9.get('status')}")

    # STAGE 10: Fastn Decision Archive
    console.print("\n[bold yellow]> STAGE 10: Fastn Decision Archive to Google Drive & Airtable[/bold yellow]")
    s10 = await fastn_client.execute_decision_archive(
        contract_id=cid,
        decision="APPROVED_WITH_CONDITIONS",
        decision_maker="General Counsel",
        society="CAS_FEDERATION",
        reason="12-month mutual fee cap accepted with mandatory SOC2 audit right.",
        evidence="Simulated risk dropped from 0.85 to 0.24.",
        resulting_action="EXECUTE_SIGNATURE"
    )
    console.print(f"[green][OK] Fastn Decision Archived:[/green] Status={s10.get('status')}")

    # STAGE 11: Obligation Scheduling & Fastn Calendar Sync
    console.print("\n[bold yellow]> STAGE 11: Obligation Intelligence Scheduling (System 5) & Fastn Sync[/bold yellow]")
    sched = await obligation_intelligence_system.register_obligations(contract_text, cid, "2026-10-01")
    s11 = await fastn_client.execute_obligation_sync(cid, [
        {"title": o.title, "party": o.party, "dueDate": o.due_date, "type": o.type}
        for o in sched.items
    ])
    console.print(f"[green][OK] Obligation Schedule Registered:[/green] {sched.total_obligations} obligations synced to Google Calendar via Fastn.")

    # STAGE 12: Fastn Inbound Event (External Counterparty Redline)
    console.print("\n[bold yellow]> STAGE 12: Fastn Inbound Event (External Counterparty Redline Return)[/bold yellow]")
    s12 = await fastn_client.trigger_inbound_negotiation(
        contract_id=cid,
        clause_reference="Section 8.2 Limitation of Liability",
        counterparty_proposal="NovaCloud agrees to mutual aggregate liability capped at 12 months fees ($240,000).",
        concession_offered="Withdrew unilateral liability shield; agreed to reciprocal dollar cap."
    )
    console.print(f"[green][OK] Fastn Inbound Webhook Received Redline:[/green] Status={s12.get('status')}")

    # STAGE 13: CAS Director Inbound Re-Routing & Strategy Adaptation
    console.print("\n[bold yellow]> STAGE 13: CAS Director Inbound Re-Routing & Strategy Adaptation[/bold yellow]")
    s13 = await cas_director.handle_inbound_negotiation(
        contract_id=cid,
        counterparty_proposal="NovaCloud agrees to mutual aggregate liability capped at 12 months fees ($240,000).",
        clause_reference="Section 8.2 Limitation of Liability",
        concession_offered="Withdrew unilateral liability shield; agreed to reciprocal dollar cap."
    )
    console.print(f"[green][OK] Director Adapted Strategy & Broadcasted Update via Fastn:[/green] Status={s13.get('status')}")

    # STAGE 14: Fastn Dispute Escalation
    console.print("\n[bold yellow]> STAGE 14: Fastn Dispute Escalation Dispatch (Litigation Alert)[/bold yellow]")
    s14 = await fastn_client.execute_dispute_escalation(
        contract_id=cid,
        dispute_risk="HIGH",
        ambiguities=["Section 14.1 SLA calculation conflicts with Section 4 credit remedy."],
        counterparty_stance="Vendor will argue upstream cloud outage is force majeure.",
        recommended_action="Harmonize SLA remedy language before execution."
    )
    console.print(f"[green][OK] Fastn Dispute Alert Dispatched:[/green] Status={s14.get('status')}")

    # STAGE 15: Dispute Intelligence Simulation & Precedent Memory
    console.print("\n[bold yellow]> STAGE 15: Dispute Intelligence Simulation (System 6) & Precedent Storage[/bold yellow]")
    disp = await dispute_intelligence_system.analyze_disputes(contract_text, cid, "Acme Global", "NovaCloud")
    await cas_memory.store(
        memory_type="PRECEDENT",
        content={
            "event": "DISPUTE_SIMULATION_COMPLETED",
            "contract_id": cid,
            "overall_dispute_risk": disp.overall_dispute_risk,
            "scenarios_count": len(disp.scenarios),
            "resolution": "Precedent recorded: enforce bilateral liability symmetry on all future vendor contracts."
        },
        tags=["dispute", "precedent", "liability"]
    )
    console.print(f"[green][OK] Dispute Intelligence Simulation Completed:[/green] {len(disp.scenarios)} crisis scenarios modeled, indexed in CAS Memory.")

    console.print(Panel.fit(
        "[bold green]FULL 15-STAGE BIDIRECTIONAL FEDERATION SCENARIO EXECUTED SUCCESSFULLY![/bold green]\n"
        "[white]Contract Agentic Society (CAS) nervous system fully operational across all 10 Fastn workflows.[/white]",
        border_style="green"
    ))


if __name__ == "__main__":
    asyncio.run(run_end_to_end_demo())
