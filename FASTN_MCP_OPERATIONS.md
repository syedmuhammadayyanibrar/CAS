# Fastn MCP Operations & Nervous System Audit Trail

## 1. Overview
The **Contract Agentic Society (CAS)** uses **Fastn MCP** as its external nervous system. While internal agent reasoning is powered solely by the **Google Gemini API**, and cross-society events are orchestrated via standardized `CASMessage` protocols, all interactions with external enterprise tools, SaaS integrations, and scheduled events are conducted through **Fastn Workflows, Webhooks, and Schedulers**.

- **Fastn Organization Domain:** `personal_867cccac2ec39658a401`
- **MCP Server:** `fastn`
- **Fastn Workflows Deployed:** 5 Production Workflows
- **Trigger Types Configured:** Webhook Triggers, Direct Workflow Executions, Scheduler Bindings

---

## 2. Deployed Fastn Workflows

| Workflow Name | Workflow ID | Version ID | Trigger Type | Endpoint / Target | Primary Function |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`cas-contract-intake`** | `wf_0c61baf31b93` | `wv_0fd022fed80b` | **Inbound Webhook** | `https://webhooks.fastn.dev/prod/triggers/personal_867cccac2ec39658a401/webhooks/1211f7a1-39c5-44da-9b3c-718fff44ad7d` | Ingests new contracts from external systems (Google Drive, DocuSign, email) |
| **`cas-risk-escalation`** | `wf_7330f03b75f6` | `wv_a66ff30e02f2` | Direct Execution | Slack / Alert Dispatch | Escalates Critical/High risks to enterprise risk committees |
| **`cas-approval-dispatch`** | `wf_5ccc14b11936` | `wv_cc951531fa27` | Direct Execution | Slack / Email / HITL Portal | Dispatches Human-In-The-Loop review requests |
| **`cas-obligation-sync`** | `wf_2783a17803cc` | `wv_9c43664ba704` | Direct Execution | Google Calendar / Airtable | Synchronizes post-signature deadlines and deliverables |
| **`cas-renewal-monitor`** | `wf_ef794f8dd239` | `wv_b12ec8139169` | Scheduler / Direct | Daily 09:00 UTC Cron | Evaluates contracts against impending renewal windows |

---

## 3. Fastn MCP Tool Execution Audit

### Operation 1: Creation & Deployment of `cas-contract-intake`
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__createWorkflow`)
  - `name`: `cas-contract-intake`
  - `description`: "Ingests contract metadata and raw text from external storage and feeds Contract Intelligence"
  - *Result:* Workflow created with ID `wf_0c61baf31b93`.
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__editWorkflowCode`)
  - Updated workflow logic to sanitize inbound contract JSON payloads, validate document types, and return intake confirmation.
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__publishWorkflow`)
  - Published version: `wv_0fd022fed80b`.
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__bind_webhook_trigger`)
  - Bound inbound webhook trigger.
  - *Generated Webhook URL:* `https://webhooks.fastn.dev/prod/triggers/personal_867cccac2ec39658a401/webhooks/1211f7a1-39c5-44da-9b3c-718fff44ad7d`

### Operation 2: Creation & Verification of `cas-risk-escalation`
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__createWorkflow`)
  - `name`: `cas-risk-escalation`
  - *Result:* Workflow ID `wf_7330f03b75f6`.
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__editWorkflowCode`)
  - Added conditional escalation logic for `severity === "CRITICAL" || severity === "HIGH"`.
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__publishWorkflow`)
  - Published version: `wv_a66ff30e02f2`.
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__executeWorkflow`)
  - **Live Verification Execution:**
    ```json
    {
      "workflowId": "wf_7330f03b75f6",
      "versionId": "wv_a66ff30e02f2",
      "input": {
        "contractId": "CTR-TEST-001",
        "severity": "CRITICAL",
        "clause": "Section 8.2 Asymmetric Cap",
        "consequence": "Unlimited Customer exposure with 1-month Vendor shield",
        "evidence": "Customer total aggregate liability shall be uncapped."
      }
    }
    ```
  - **Live Response Received from Fastn Platform:**
    ```json
    {
      "status": "ESCALATED_TO_HUMAN",
      "channel": "#legal-risk-alerts",
      "message": "Critical risk in Section 8.2 Asymmetric Cap escalated to General Counsel."
    }
    ```

### Operation 3: Creation & Deployment of `cas-approval-dispatch`
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__createWorkflow`)
  - `name`: `cas-approval-dispatch`
  - *Result:* Workflow ID `wf_5ccc14b11936`.
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__editWorkflowCode`) & `publishWorkflow`
  - Version: `wv_cc951531fa27`.
  - Dispatches interactive Slack notification blocks with "Approve" and "Reject" actions.

### Operation 4: Creation & Deployment of `cas-obligation-sync`
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__createWorkflow`)
  - `name`: `cas-obligation-sync`
  - *Result:* Workflow ID `wf_2783a17803cc`.
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__editWorkflowCode`) & `publishWorkflow`
  - Version: `wv_9c43664ba704`.
  - Iterates over post-signature obligations and schedules Google Calendar reminders and Airtable records.

### Operation 5: Creation & Deployment of `cas-renewal-monitor`
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__createWorkflow`)
  - `name`: `cas-renewal-monitor`
  - *Result:* Workflow ID `wf_ef794f8dd239`.
- **MCP Tool:** `call_mcp_tool` (`fastnPlatform__editWorkflowCode`) & `publishWorkflow`
  - Version: `wv_b12ec8139169`.
  - Checks contracts for notice period expiration windows (e.g. 60 or 90 days before auto-renewal).

---

## 4. Integration Architecture with CAS Python Backend
The Python backend connects to Fastn using `backend/integrations/fastn_client.py` and `backend/integrations/adapters.py`:

```text
┌─────────────────────────────────────────────────────────────┐
│                 CAS Python Backend Engine                   │
│                                                             │
│   [Director] ──► [Risk Intelligence] ──► [Event Bus]        │
└───────────────┬─────────────────────────────────────────────┘
                │ HTTP POST / Webhook Dispatch
                ▼
┌─────────────────────────────────────────────────────────────┐
│                 Fastn Enterprise Platform                   │
│         (org: personal_867cccac2ec39658a401)                │
│                                                             │
│   • cas-contract-intake      (Inbound Webhook)              │
│   • cas-risk-escalation      (Severity-gated alert)         │
│   • cas-approval-dispatch    (Human-in-the-loop dispatch)   │
│   • cas-obligation-sync      (Calendar / Task sync)         │
│   • cas-renewal-monitor      (Scheduled cron monitor)       │
└───────────────┬─────────────────────────────────────────────┘
                │ Integrations
                ▼
┌─────────────────────────────────────────────────────────────┐
│    External Systems: Slack, Google Calendar, Airtable       │
└─────────────────────────────────────────────────────────────┘
```

The Fastn integration allows CAS agents to operate with maximum autonomy while maintaining seamless bi-directional connectivity with real-world enterprise infrastructure.
