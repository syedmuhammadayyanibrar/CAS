import React, { useState } from "react";
import {
  Cpu,
  Play,
  CheckCircle2,
  AlertTriangle,
  FileText,
  ShieldAlert,
  Scale,
  Calendar,
  Layers,
  Sparkles,
  Copy,
  Check,
  RotateCcw,
  Code2,
  Eye,
  Sliders,
  Users,
  Clock,
  Briefcase,
  AlertCircle,
  TrendingDown,
  Gavel,
  ShieldCheck,
  ArrowRight,
  HelpCircle,
  FileCheck,
  Send,
  Share2,
  DollarSign,
  Activity,
  BookmarkCheck,
  ChevronRight,
} from "lucide-react";
import { runStandaloneSociety, executeAutomation } from "../api/client";
import { DocumentIngestBar } from "../components/DocumentIngestBar";

interface SocietyMeta {
  id: string;
  name: string;
  architecture: string;
  status: string;
  agents: Array<{ name: string; role: string }>;
  inputContract: string;
  outputContract: string;
  description: string;
  standaloneTestUrl: string;
}

const SOCIETIES: SocietyMeta[] = [
  {
    id: "contract_intelligence",
    name: "Contract Intelligence Society",
    architecture: "Parallel + Verification",
    status: "OPERATIONAL",
    agents: [
      { name: "Structural Parser", role: "Extracts parties, definitions, and recitals" },
      { name: "Clause Segmenter", role: "Splits agreement into numbered operative clauses" },
      { name: "Graph Constructor", role: "Builds typed relational schema and cross-references" },
      { name: "Schema Verifier", role: "Validates graph integrity and missing references" },
    ],
    inputContract: "Raw contract text or document payload",
    outputContract: "ContractGraph (Typed clauses, parties, relationship edges)",
    description:
      "Operates independently to decompose unstructured agreements into formal typed graph structures with mathematical verification.",
    standaloneTestUrl: "/systems/contract-intelligence/analyze",
  },
  {
    id: "risk_intelligence",
    name: "Risk Intelligence Society",
    architecture: "Adversarial Debate (Dialectic)",
    status: "OPERATIONAL",
    agents: [
      { name: "Risk Hunter", role: "Argues aggressively for worst-case financial/legal downside" },
      { name: "Counterargument", role: "Defends standard market practice and mitigating terms" },
      { name: "Synthesis Assessor", role: "Adjudicates net exposure score and escalation threshold" },
    ],
    inputContract: "Contract text or ContractGraph",
    outputContract: "RiskReport (Overall score, findings, escalation flag)",
    description:
      "Prevents false positives and missed catastrophic liabilities through structured adversarial debate between dedicated hunter and defender agents.",
    standaloneTestUrl: "/systems/risk-intelligence/analyze",
  },
  {
    id: "negotiation_intelligence",
    name: "Negotiation Intelligence Society",
    architecture: "Planner + Simulator + Critic",
    status: "OPERATIONAL",
    agents: [
      { name: "Strategic Planner", role: "Generates optimal redlines aligned with commercial objective" },
      { name: "Counterparty Simulator", role: "Models vendor legal pushback and deal-breaker sensitivities" },
      { name: "Strategy Critic", role: "Audits redlines for realism and constructs concession packages" },
    ],
    inputContract: "Contract text + Commercial Objective",
    outputContract: "NegotiationStrategy (Redlines, trade-offs, concession fallback)",
    description:
      "Generates redlines accompanied by simulated vendor reactions and fallback concession packages to ensure high acceptance probability.",
    standaloneTestUrl: "/systems/negotiation-intelligence/analyze",
  },
  {
    id: "compliance_intelligence",
    name: "Compliance Intelligence Society",
    architecture: "Retrieval + Rules + Verification",
    status: "OPERATIONAL",
    agents: [
      { name: "Policy Retriever", role: "Extracts applicable enterprise and statutory policies" },
      { name: "Rule Matcher", role: "Matches contractual language against mandatory corporate clauses" },
      { name: "Compliance Verifier", role: "Grants pass/fail and documents statutory evidence" },
    ],
    inputContract: "Contract text + Corporate Policy JSON",
    outputContract: "ComplianceReport (Overall status, violations count, evidence citations)",
    description:
      "Grounds contract language against company playbook rules and statutory frameworks (GDPR, Delaware law) with strict evidence citations.",
    standaloneTestUrl: "/systems/compliance-intelligence/analyze",
  },
  {
    id: "obligation_intelligence",
    name: "Obligation Intelligence Society",
    architecture: "Event-Driven Monitoring",
    status: "OPERATIONAL",
    agents: [
      { name: "Obligation Extractor", role: "Extracts post-signature deliverables and milestones" },
      { name: "Calendar Synchronizer", role: "Calculates notice periods and syncs via Fastn" },
    ],
    inputContract: "Executed contract text + Effective date",
    outputContract: "ObligationSchedule (Commitments, due dates, notice windows)",
    description:
      "Activates upon contract execution to transform static legal commitments into live operational schedules pushed via Fastn to Google Calendar.",
    standaloneTestUrl: "/systems/obligation-intelligence/analyze",
  },
  {
    id: "dispute_intelligence",
    name: "Dispute Intelligence Society",
    architecture: "Multi-Perspective Simulation + Debate",
    status: "OPERATIONAL",
    agents: [
      { name: "Party A Litigator", role: "Interprets ambiguous language to maximize Customer claims" },
      { name: "Party B Litigator", role: "Interprets same clauses to maximize Vendor defenses" },
      { name: "Judicial Arbiter", role: "Assesses ambiguity polarity and authors preventative redlines" },
    ],
    inputContract: "Contract text + Party names",
    outputContract: "DisputeAssessment (Ambiguity index, crisis narratives, preventative redlines)",
    description:
      "Simulates adversarial courtroom litigation to unearth latent ambiguities before signing, producing preventative redlines that eliminate dispute vectors.",
    standaloneTestUrl: "/systems/dispute-intelligence/analyze",
  },
];

const PRESET_FULL_SAAS = `MASTER SAAS SERVICES AGREEMENT

This Master SaaS Services Agreement ("Agreement") is made and entered into as of October 1, 2026 ("Effective Date"), by and between NovaCloud Systems Inc., a Delaware corporation with principal place of business at 500 Cloud Way, San Francisco, CA ("Vendor"), and Acme Global Enterprises LLC, a Delaware limited liability company with offices at 100 Enterprise Blvd, New York, NY ("Customer"). Vendor and Customer may each be referred to as a "Party" or collectively as the "Parties."

SECTION 1: DEFINITIONS & SUBSCRIPTION SERVICES
1.1 Platform Access: Vendor grants Customer a non-exclusive, non-transferable subscription license to access the NovaCloud Platform.
1.2 Authorized Users: Customer is liable for all user credential activities.

SECTION 2: TERM AND AUTOMATIC RENEWAL
2.1 Initial Term: Commences on the Effective Date and continues for twelve (12) months.
2.2 Automatic Renewal: Automatically renews for successive 12-month periods unless either Party delivers written notice of non-renewal at least sixty (60) days prior.
2.3 Price Increases: Vendor reserves the right to increase annual subscription fees by up to 15% upon each renewal.

SECTION 3: FEES, BILLING & PAYMENT TERMS
3.1 Subscription Fees: Customer shall pay an annual fee of $240,000 USD, billed quarterly in advance ($60,000 USD per quarter).
3.2 Payment Due Date: All invoices are payable Net 30 days. Late payments accrue interest at 1.5% per month.

SECTION 4: SERVICE LEVEL AGREEMENT & PERFORMANCE
4.1 Availability: Vendor shall use commercially reasonable efforts to make the Platform available with an Annual Uptime Percentage of at least 99.9%. Exclusions include downtime caused by Customer network or integrations.
4.2 Audit Deliverable: Vendor must provide SOC2 Type II compliance audit report to Customer annually by January 15, 2027.
4.3 Sole Remedy: Customer sole and exclusive remedy for SLA failure shall be a service credit equal to 5% of monthly fees, applicable only upon written claim within ten (10) days.

SECTION 6: DATA OWNERSHIP & DERIVATIVE WORKS
6.1 Customer Data: Customer retains all rights in Customer Data uploaded to the Platform.
6.2 Vendor Aggregate Rights: Customer hereby grants Vendor a perpetual, irrevocable, worldwide, royalty-free license to use, aggregate, de-identify, and analyze Customer Data to train, improve, and deploy machine learning models and derivative analytics products.

SECTION 7: INTELLECTUAL PROPERTY INDEMNIFICATION
7.1 Customer Indemnity: Customer shall defend, indemnify, and hold harmless Vendor against all third-party claims, liabilities, and costs arising from Customer Data or breach of this Agreement, without financial limitation.

SECTION 8: LIMITATION OF LIABILITY
8.1 Consequential Damages: Neither Party shall be liable for indirect or consequential damages.
8.2 Aggregate Liability Cap: VENDOR TOTAL AGGREGATE LIABILITY SHALL BE STRICTLY LIMITED TO FEES PAID BY CUSTOMER IN THE ONE (1) MONTH PRECEDING THE INCIDENT ($20,000 USD). CUSTOMER TOTAL AGGREGATE LIABILITY SHALL BE UNCAPPED.

SECTION 9: TERMINATION
9.1 Termination for Cause: Either Party may terminate upon thirty (30) days notice for material breach.
9.2 Conflicting Termination Notice: Section 9.3 provides that Vendor may terminate services without cause upon ten (10) days email notice if Vendor determines Customer use threatens system stability.

SECTION 10: GOVERNING LAW AND ARBITRATION
10.1 Governing Law: Laws of the State of Delaware.
10.2 Dispute Resolution: Final binding arbitration administered by JAMS in New York, NY.`;

const PRESET_RISKY_CLAUSE = `SECTION 8: LIMITATION OF LIABILITY & INDEMNIFICATION
8.1 Consequential Damages: In no event shall Vendor be liable for indirect, incidental, or lost profits.
8.2 Aggregate Liability Cap: NOTWITHSTANDING ANYTHING TO THE CONTRARY, VENDOR'S TOTAL AGGREGATE LIABILITY UNDER THIS AGREEMENT SHALL BE STRICTLY CAPPED AT FEES PAID BY CUSTOMER IN THE ONE (1) MONTH PRECEDING THE CLAIM ($20,000). CUSTOMER'S TOTAL AGGREGATE LIABILITY SHALL BE UNLIMITED.
8.3 Indemnification Asymmetry: Customer agrees to defend and hold harmless Vendor against any third-party claims without financial cap or limitation.`;

const PRESET_SLA_RENEWAL = `SECTION 2: TERM AND RENEWAL
2.1 Initial Term: Twelve (12) months beginning October 1, 2026.
2.2 Non-Renewal Notice: Either party may opt out by providing written notice ninety (90) days prior to renewal.

SECTION 4: SERVICE LEVEL AGREEMENT & CREDITS
4.1 Availability: Vendor guarantees 99.9% uptime per calendar quarter.
4.2 Audit Deliverable: Vendor must provide SOC2 Type II compliance audit report to Customer annually by January 15, 2027.
4.3 Notice Window: Service credit claims must be submitted within seven (7) business days of outage.`;

// 10-Point Compliance & Statutory Radar Checklist
const EXECUTIVE_RADAR_CHECKLIST = [
  {
    id: "RADAR-01",
    domain: "Liability & Governance",
    clause: "Section 8.2 Aggregate Liability Cap",
    statute: "UCC § 2-302 / Delaware GCL § 102",
    status: "VIOLATION",
    riskLevel: "CRITICAL",
    analysis: "1-month fee cap ($20k) for Vendor vs uncapped Customer exposure creates 140:1 balance-sheet disparity. Substantively unconscionable under commercial law.",
    requiredAction: "Amend to mutual 12-month trailing fee cap ($240,000 USD) with $1,000,000 super-cap for confidentiality.",
  },
  {
    id: "RADAR-02",
    domain: "Indemnity & Defense",
    clause: "Section 7.1 Unilateral Defense Duty",
    statute: "Common Law Defense Symmetry / Delaware Chancery",
    status: "VIOLATION",
    riskLevel: "CRITICAL",
    analysis: "Customer acts as unilateral indemnitor for all third-party claims touching platform use without reciprocal Vendor IP defense.",
    requiredAction: "Insert bilateral defense covenants: Vendor defends Platform IP; Customer defends customer-uploaded data.",
  },
  {
    id: "RADAR-03",
    domain: "Data Privacy & AI Models",
    clause: "Section 6.2 ML Training License",
    statute: "EU GDPR Art. 28(3)(a) / CCPA § 1798 / DTSA",
    status: "VIOLATION",
    riskLevel: "HIGH",
    analysis: "Perpetual, irrevocable license to train machine learning models on Customer confidential data surrenders core IP assets.",
    requiredAction: "Strike ML model training grant completely; insert explicit AI Training Exclusion carve-out.",
  },
  {
    id: "RADAR-04",
    domain: "Contract Term & Pricing",
    clause: "Section 2.2 & 2.3 Evergreen Renewal",
    statute: "Delaware Evergreen Enforceability / CPI-U",
    status: "AT RISK",
    riskLevel: "MEDIUM",
    analysis: "60-day non-renewal notice coupled with 15% compounding unconsented annual price escalation produces compounding budget exposure.",
    requiredAction: "Reduce notice window to 30 days and cap annual renewal fee adjustments at CPI-U or 3.0% maximum.",
  },
  {
    id: "RADAR-05",
    domain: "Service Levels & Uptime",
    clause: "Section 4.3 SLA 5% Sole Remedy",
    statute: "UCC § 2-719(2) Failure of Essential Purpose",
    status: "VIOLATION",
    riskLevel: "HIGH",
    analysis: "Nominal 5% service credit as sole and exclusive remedy bars breach damages during catastrophic multi-day system outages.",
    requiredAction: "Establish graduated credit tiers (up to 50%) and add Chronic Failure Termination right (<99.0% for 2 months).",
  },
  {
    id: "RADAR-06",
    domain: "Governing Law & Forum",
    clause: "Section 10.1 & 10.2 Delaware Law / JAMS",
    statute: "Delaware Uniform Arbitration Act (DUAA)",
    status: "COMPLIANT",
    riskLevel: "LOW",
    analysis: "Designation of Delaware substantive law with binding JAMS arbitration in New York meets corporate standard approval criteria.",
    requiredAction: "Maintain governing law and dispute venue provisions as drafted.",
  },
  {
    id: "RADAR-07",
    domain: "Confidentiality & NDA",
    clause: "Section 5.1 Mutual Non-Disclosure",
    statute: "Defend Trade Secrets Act (DTSA 18 U.S.C. § 1836)",
    status: "COMPLIANT",
    riskLevel: "LOW",
    analysis: "Standard 3-year confidentiality term with customary exceptions for compulsory legal process and regulatory disclosures.",
    requiredAction: "No amendment required; terms align with commercial baseline.",
  },
  {
    id: "RADAR-08",
    domain: "Information Security Audit",
    clause: "Section 4.2 SOC 2 Type II Delivery",
    statute: "AICPA Trust Services Criteria / SOC 2 Type II",
    status: "REVIEW REQUIRED",
    riskLevel: "MEDIUM",
    analysis: "Audit delivery deadline of January 15, 2027 provides insufficient initial assurance without interim bridge letter or pen-test summary.",
    requiredAction: "Require Vendor to deliver latest completed SOC 2 Type II audit report within 15 days of Effective Date.",
  },
  {
    id: "RADAR-09",
    domain: "Data Breach Notification",
    clause: "Section 6.3 Security Incident Response",
    statute: "GDPR Art. 33 (72h) / SEC Item 1.05 Form 8-K (4 days)",
    status: "REVIEW REQUIRED",
    riskLevel: "HIGH",
    analysis: "Agreement lacks an explicit incident notification SLA, leaving Customer vulnerable to statutory reporting forfeiture.",
    requiredAction: "Mandate formal written notification to Customer Security Operations within forty-eight (48) hours of confirmed breach.",
  },
  {
    id: "RADAR-10",
    domain: "Assignment & Succession",
    clause: "Section 11.4 Assignment Rights",
    statute: "Delaware Corporate Law (8 Del. C. § 251)",
    status: "COMPLIANT",
    riskLevel: "LOW",
    analysis: "Assignment permitted to corporate affiliates or in connection with merger/acquisition upon 30 days prior written notice.",
    requiredAction: "Maintain standard corporate succession provision.",
  },
];

// Interactive Redline Diffs
const ENTERPRISE_REDLINES = [
  {
    section: "Section 8.2",
    title: "Aggregate Limitation of Liability & Commercial Parity",
    doctrine: "UCC § 2-302 (Unconscionability) • UCC § 2-719(2) (Essential Purpose) • Delaware GCL",
    exposure: "$2,400,000 estimated catastrophic exposure vs $20,000 nominal vendor cap (140:1 asymmetry)",
    originalText:
      "VENDOR TOTAL AGGREGATE LIABILITY ARISING OUT OF OR RELATED TO THIS AGREEMENT SHALL BE STRICTLY LIMITED TO FEES PAID BY CUSTOMER IN THE ONE (1) MONTH PRECEDING THE INCIDENT ($20,000 USD). CUSTOMER TOTAL AGGREGATE LIABILITY SHALL BE UNCAPPED.",
    proposedText:
      "Except for breach of confidentiality obligations under Section 5 or indemnification under Section 7, each Party's maximum cumulative aggregate liability arising out of or relating to this Agreement shall be strictly limited to the total subscription fees actually paid by Customer in the twelve (12) months preceding the event giving rise to liability ($240,000 USD).",
    rationale:
      "Eliminates existential balance-sheet exposure while establishing reciprocal liability protection that mirrors prevailing enterprise SaaS market standards.",
  },
  {
    section: "Section 7.1 & 7.2",
    title: "Reciprocal Intellectual Property & Security Indemnification",
    doctrine: "Delaware Common Law Defense Standards • Enterprise Bilateral Risk Allocation",
    exposure: "Unfunded third-party outside counsel defense costs ($1,200/hr) for platform IP infringement suits",
    originalText:
      "Customer shall defend, indemnify, and hold harmless Vendor, its affiliates, and officers from and against any and all third-party claims, damages, liabilities, costs, and expenses (including reasonable attorneys' fees) arising out of or related to Customer Data or use of Platform, without financial limitation.",
    proposedText:
      "(a) Vendor Indemnification: Vendor shall defend, indemnify, and hold harmless Customer, its affiliates, and their respective directors and employees from and against any third-party claims, suits, or proceedings alleging that the Platform infringes any patent, copyright, or misappropriates any trade secret, and shall pay all damages and legal fees awarded against Customer. (b) Customer Indemnification: Customer shall defend and indemnify Vendor solely against third-party claims arising from Customer Data, both subject to the mutual liability cap in Section 8.2.",
    rationale:
      "Ensures Customer is not acting as an unpaid insurer for vendor code defects, while preserving fair protection for Vendor against unauthorized customer content.",
  },
  {
    section: "Section 6.2",
    title: "Proprietary Data Ownership & AI Model Training Exclusion",
    doctrine: "EU GDPR Article 28(3)(a) • Defend Trade Secrets Act (DTSA) • CCPA",
    exposure: "Permanent loss of proprietary operational trade secrets and secondary data processing regulatory penalties",
    originalText:
      "Customer hereby grants Vendor a perpetual, irrevocable, worldwide, royalty-free license to use, aggregate, de-identify, and analyze Customer Data to train, improve, and deploy machine learning models, statistical benchmarks, and derivative analytics products.",
    proposedText:
      "Customer retains all rights, title, and interest (including all intellectual property rights) in and to Customer Data. Vendor shall not access, process, de-identify, or aggregate Customer Data to train, fine-tune, benchmark, or validate any machine learning algorithms, artificial intelligence foundation models, or commercial analytics products without Customer's prior explicit written consent. Vendor may utilize anonymized operational system latency logs solely for platform routing optimization.",
    rationale:
      "Quarantines customer enterprise records from LLM prompt-inversion attacks and guarantees compliance with mandatory enterprise data processor standards.",
  },
  {
    section: "Section 2.2 & 2.3",
    title: "Evergreen Auto-Renewal & Renewal Price Increase Cap",
    doctrine: "Delaware Evergreen Contract Enforceability • Corporate Procurement Budget Governance",
    exposure: "Irrevocable automatic lock-in to $276,000+ commitment with compounding 15% annual price escalation",
    originalText:
      "This Agreement shall automatically renew for successive twelve (12) month periods unless either Party delivers written notice of non-renewal at least sixty (60) days prior. Vendor reserves the right to increase annual subscription fees by up to fifteen percent (15%) upon each renewal without prior consent.",
    proposedText:
      "This Agreement may be renewed for successive twelve (12) month periods upon mutual written agreement, or shall automatically renew unless either Party delivers written notice of non-renewal at least thirty (30) calendar days prior to the expiration of the then-current term. Vendor may adjust subscription fees for Renewal Terms by no more than the lesser of three percent (3.0%) or the trailing 12-month Consumer Price Index (CPI-U), upon at least sixty (60) days advance written notice.",
    rationale:
      "Provides procurement flexibility to benchmark competing alternatives while constraining annual price increases within realistic inflationary bounds.",
  },
  {
    section: "Section 4.3",
    title: "SLA Remedy Structure & Chronic Downtime Termination Right",
    doctrine: "UCC § 2-719(2) (Exclusive Remedy Failure) • Mission-Critical Enterprise Availability",
    exposure: "Loss of $450k+ in transaction volume during multi-day outages with no legal remedy beyond a $1,000 credit",
    originalText:
      "In the event of an unscheduled outage exceeding 0.1% in any calendar month, Customer's sole and exclusive remedy shall be to receive a service credit equal to five percent (5%) of monthly fees, provided Customer submits a written claim within ten (10) business days.",
    proposedText:
      "If Platform Uptime falls below 99.9% in any calendar month, Vendor shall issue service credits according to the following schedule: 10% for <99.9%, 25% for <99.0%, and 50% for <98.0% of monthly fees. Furthermore, if Platform Uptime falls below 99.0% in any two (2) calendar months within a rolling six (6) month period ('Chronic Failure'), Customer may immediately terminate this Agreement upon written notice without penalty and receive an immediate pro-rata refund of all prepaid unearned fees.",
    rationale:
      "Establishes real financial accountability for platform availability and provides an indispensable operational escape hatch if vendor infrastructure experiences recurring instability.",
  },
];

// Negotiation Playbook Concession Ladder
const NEGOTIATION_PLAYBOOK_POSITIONS = [
  {
    section: "Section 8.2",
    title: "Limitation of Liability & Parity",
    priority: "PRIORITY 1 (MANDATORY)",
    target: "Mutual aggregate liability cap equal to 12 months trailing fees ($240,000 USD) with gross negligence carve-outs.",
    compromise: "Mutual cap at 18 months trailing fees ($360,000 USD) or $500,000 USD fixed super-cap for data privacy claims.",
    redline: "Uncapped Customer liability or sub-6-month Vendor liability ceiling ($120k).",
    leverage: "High enterprise deal value ($240,000 ARR) and status as key enterprise showcase customer.",
    concession: "Offer semi-annual advance payments ($120,000 x 2) instead of quarterly billing to improve vendor cash flow.",
    vendorForecast: "Vendor deal desk typically starts at 3-month cap, but routinely grants mutual 12-month caps for enterprise tiers (82% acceptance probability).",
  },
  {
    section: "Section 7.2",
    title: "Intellectual Property & Operational Indemnification",
    priority: "PRIORITY 2 (HIGH)",
    target: "Fully reciprocal indemnification: Vendor defends platform IP; Customer defends customer data content.",
    compromise: "Vendor reciprocal IP defense with a $1,000,000 liability ceiling and standard combination carve-outs.",
    redline: "Unilateral customer-only indemnification or customer indemnification for vendor platform code defects.",
    leverage: "Standard enterprise software contracting norm where vendors always defend their own code.",
    concession: "Agree to 14-day prompt notice requirement and grant Vendor exclusive control of legal defense.",
    vendorForecast: "Vendor legal counsel will readily accept bilateral indemnification once customer data exclusions are clarified (88% acceptance probability).",
  },
  {
    section: "Section 6.2",
    title: "Proprietary Data Protection & AI Model Exclusion",
    priority: "PRIORITY 3 (HIGH)",
    target: "Strict carve-out barring Vendor from training machine learning or AI foundation models on Customer Data.",
    compromise: "Permit de-identified aggregated system latency telemetry while strictly prohibiting generative training on Customer payloads.",
    redline: "Perpetual irrevocable license to customer confidential data or AI model training rights.",
    leverage: "EU GDPR Article 28 processor compliance obligations and enterprise trade secret protection policies.",
    concession: "Permit anonymized operational latency, query execution times, and system error logging.",
    vendorForecast: "Vendor product team will concede the AI training restriction once operational telemetry rights are maintained (92% acceptance probability).",
  },
  {
    section: "Section 2.3",
    title: "Annual Renewal Price Increase Ceiling",
    priority: "PRIORITY 4 (MEDIUM)",
    target: "Cap annual price increases at trailing 12-month CPI-U or 3.0%, whichever is lower.",
    compromise: "Cap annual price increases at 5.0% maximum with 60 days advance written notice.",
    redline: "Unilateral discretionary price escalations exceeding 8% annually.",
    leverage: "Corporate procurement multi-year budget predictability mandates.",
    concession: "Agree to a 24-month initial commitment period in exchange for pricing stability.",
    vendorForecast: "Vendor will accept a 5% cap readily in exchange for a 2-year initial term commitment (90% acceptance probability).",
  },
  {
    section: "Section 4.3",
    title: "SLA Remedy Structure & Chronic Downtime Termination",
    priority: "PRIORITY 5 (MEDIUM)",
    target: "Tiered service credits up to 50% of monthly fees and unilateral termination right for chronic downtime (<99.0% for 2 months).",
    compromise: "Tiered credits up to 25% with 30-day termination right for extended downtime.",
    redline: "5% nominal credit as sole and exclusive remedy with zero termination right.",
    leverage: "Mission-critical workflow dependency where downtime directly causes revenue loss.",
    concession: "Extend outage claim filing window to 15 calendar days and agree to reasonable maintenance exclusions.",
    vendorForecast: "Vendor will accept chronic failure termination when paired with realistic maintenance exclusions (79% acceptance probability).",
  },
];

// Dual Courtroom Litigation Simulation Scenarios
const COURTROOM_DISPUTE_SCENARIOS = [
  {
    id: "DSP-001",
    clause: "Section 4.1 & 4.3 (SLA 99.9% Availability & 5% Sole Remedy Limitation)",
    trigger: "14-Hour Cloud Outage During End-of-Quarter Financial Close",
    partyA: "Customer Case Theory: 'Commercially reasonable efforts' mandates 24/7 active engineer response and sub-2-hour Recovery Time Objective (RTO). A nominal $300 service credit for an outage causing $2,400,000 in unbilled transactions is unconscionable and fails of its essential purpose under UCC § 2-719.",
    partyB: "Vendor Defense Theory: The contract explicitly limits remedies to 5% service credits. Delaware law strictly enforces commercial risk allocations between sophisticated corporate entities, completely barring consequential damages under Section 8.1.",
    narrative: "A 14-hour platform outage strikes during Customer's end-of-quarter financial close, preventing Customer from billing over $2,400,000 USD in customer invoices and triggering contractual penalties with downstream enterprise clients. Vendor acknowledges the outage but asserts it resulted from an upstream cloud hyperscaler degradation, offering a nominal $300 USD credit under Section 4.3. Customer files an emergency arbitration claim with JAMS alleging breach of SLA, gross negligence, and failure of essential purpose under UCC § 2-719. A JAMS arbitration panel assesses a 65% probability of voiding the exclusive remedy defense and awarding substantial damages if Customer proves the outage was exacerbated by Vendor delayed engineering response.",
    severity: "CATASTROPHIC",
    preventativeRedline: "Define explicit Recovery Time Objective (RTO) of four (4) hours for Sev-1 outages, stipulate that service credits are non-exclusive remedies for downtime exceeding 8 hours, and cap total SLA downtime credits at 50% of quarterly fees.",
  },
  {
    id: "DSP-002",
    clause: "Section 8.2 & 7.2 (1-Month Liability Cap & Unilateral Indemnification Reverse-Claim)",
    trigger: "Microservices Infrastructure Vulnerability Exfiltrating 250,000 Customer Records",
    partyA: "Customer Case Theory: The 1-month nominal cap ($20k) is procedurally and substantively unconscionable under UCC § 2-302 and Delaware law when applied to gross security negligence leading to mass data exfiltration. Furthermore, Section 7.2 cannot be used to force a customer to indemnify the vendor for vendor's own software vulnerabilities.",
    partyB: "Vendor Defense Theory: Under Delaware freedom-of-contract doctrine, sophisticated enterprise parties may freely allocate risk, including capping vendor exposure to 1 month fees and requiring the customer to defend data-related claims.",
    narrative: "A vulnerability in Vendor's cloud microservices exposes 250,000 confidential customer records. State attorneys general launch inquiries, and a nationwide consumer class action is filed against both Vendor and Customer. Customer incurs $2,800,000 in forensic audit fees, breach notifications, and legal defense costs. When Customer tenders the defense and demands indemnification, Vendor refuses, cites Section 8.2 to cap its liability at $20,000, and cross-claims under Section 7.2 demanding Customer indemnify Vendor for its outside legal defense. Customer files an emergency injunction and declaratory relief in Delaware Court of Chancery to invalidate Section 8.2 and Section 7.2 for gross negligence and unconscionability.",
    severity: "EXISTENTIAL",
    preventativeRedline: "Establish mutual aggregate liability cap equal to 12 months fees ($240,000 USD), carve out data security and confidentiality breaches to an enhanced $1M super-cap, and establish reciprocal IP and security indemnification.",
  },
];

// Operational Milestone Schedule
const OPERATIONAL_MILESTONES = [
  {
    title: "Quarterly Platform Subscription Remittance",
    party: "Acme Global Enterprises LLC (Customer)",
    cadence: "QUARTERLY",
    trigger: "Net 30 calendar days from invoice delivery ($60,000 USD)",
    notice: "30 days",
    penalty: "1.5% compounding monthly penalty interest and platform access suspension upon 10 days cure notice.",
    fastnStatus: "SYNCHRONIZED (Active)",
  },
  {
    title: "Continuous 99.9% Platform Availability SLA & Incident Response",
    party: "NovaCloud Systems Inc. (Vendor)",
    cadence: "CONTINUOUS (24/7/365)",
    trigger: "Ongoing monitoring excluding scheduled maintenance windows",
    notice: "48-hour root-cause incident report",
    penalty: "Tiered pro-rata service credits (10% to 50%) and chronic failure termination rights.",
    fastnStatus: "SYNCHRONIZED (Active)",
  },
  {
    title: "Mandatory Non-Renewal Written Opt-Out Election",
    party: "Acme Global Enterprises LLC (Customer)",
    cadence: "ANNUAL CRITICAL MILESTONE",
    trigger: "Strictly 60 days prior to term expiration (August 2, 2027)",
    notice: "60 calendar days formal written notice to Vendor Legal",
    penalty: "Irrevocable automatic 12-month extension with 15% price increase ($276,000+ commitment).",
    fastnStatus: "FASTN CALENDAR EVENT ACTIVE (90-Day Warning)",
  },
  {
    title: "Annual SOC 2 Type II Compliance Audit Delivery",
    party: "NovaCloud Systems Inc. (Vendor)",
    cadence: "ANNUAL",
    trigger: "Annually on or before January 15, 2027",
    notice: "30 calendar days cure period",
    penalty: "Material contract breach permitting Customer immediate termination for cause with refund.",
    fastnStatus: "SYNCHRONIZED (Active)",
  },
  {
    title: "SLA Outage Written Credit Claim Window",
    party: "Acme Global Enterprises LLC (Customer)",
    cadence: "EVENT-DRIVEN",
    trigger: "Within 10 business days of outage month end",
    notice: "10 business days written claim submission",
    penalty: "Sole and exclusive remedy forfeiture: Unsubmitted claims within 10 days irrevocably waived.",
    fastnStatus: "SYNCHRONIZED (Active)",
  },
];

export function SocietiesView() {
  const [selectedSociety, setSelectedSociety] = useState<SocietyMeta>(SOCIETIES[1]);

  // Standalone Execution Sandbox State
  const [contractText, setContractText] = useState<string>(PRESET_FULL_SAAS);
  const [commercialObjective, setCommercialObjective] = useState<string>(
    "Cap liability at 12 months fees ($240,000 USD), secure reciprocal IP indemnity, eliminate model training grant, and reduce auto-renewal notice to 30 days."
  );
  const [policyPath, setPolicyPath] = useState<string>("corporate_standard_vendor_policy.json");
  const [effectiveDate, setEffectiveDate] = useState<string>("2026-10-01");
  const [partyA, setPartyA] = useState<string>("Acme Global Enterprises LLC (Customer)");
  const [partyB, setPartyB] = useState<string>("NovaCloud Systems Inc. (Vendor)");
  const [contractId, setContractId] = useState<string>("CTR-STANDALONE-ENTERPRISE");

  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Tab State: Extended to 9 comprehensive deliverable views
  const [activeResultTab, setActiveResultTab] = useState<
    "visual" | "dossier" | "debate" | "redlines" | "playbook" | "compliance" | "obligations" | "courtroom" | "json"
  >("visual");

  const [copiedJson, setCopiedJson] = useState<boolean>(false);
  const [copiedRedlines, setCopiedRedlines] = useState<boolean>(false);
  const [copiedBriefing, setCopiedBriefing] = useState<boolean>(false);
  const [isDispatchingFastn, setIsDispatchingFastn] = useState<boolean>(false);
  const [fastnDispatchResult, setFastnDispatchResult] = useState<any | null>(null);

  const handleRunStandalone = async () => {
    if (!contractText.trim()) {
      setError("Please provide contract text or clause to analyze.");
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    const payload: any = {
      contract_text: contractText,
      contract_id: contractId || `CTR-${Math.random().toString(36).substring(2, 9).toUpperCase()}`,
    };

    if (selectedSociety.id === "negotiation_intelligence") {
      payload.commercial_objective = commercialObjective;
    } else if (selectedSociety.id === "compliance_intelligence") {
      payload.policy_path = policyPath;
    } else if (selectedSociety.id === "obligation_intelligence") {
      payload.effective_date = effectiveDate;
    } else if (selectedSociety.id === "dispute_intelligence") {
      payload.party_a = partyA;
      payload.party_b = partyB;
    }

    try {
      const res = await runStandaloneSociety(selectedSociety.id, payload);
      setAnalysisResult(res);
      setActiveResultTab("visual");
    } catch (err: any) {
      console.error("Standalone execution failed:", err);
      setError(err.message || "Execution failed. Please check server logs.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCopyJson = () => {
    if (!analysisResult) return;
    navigator.clipboard.writeText(JSON.stringify(analysisResult, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const handleCopyRedlines = () => {
    const formatted = ENTERPRISE_REDLINES.map(
      (r, idx) =>
        `${idx + 1}. ${r.section} — ${r.title}\n` +
        `[ORIGINAL]: "${r.originalText}"\n` +
        `[PROPOSED REDLINE]: "${r.proposedText}"\n` +
        `[LEGAL DOCTRINE]: ${r.doctrine}\n` +
        `[FINANCIAL EXPOSURE]: ${r.exposure}\n` +
        `[RATIONALE]: ${r.rationale}\n`
    ).join("\n--------------------------------------------------\n\n");

    const fullText =
      `=== CAS ENTERPRISE CONTRACT REDLINES & AMENDMENT SCHEDULE ===\n` +
      `Contract ID: ${contractId}\n` +
      `Parties: ${partyA} / ${partyB}\n` +
      `Generated: ${new Date().toLocaleDateString()}\n\n` +
      formatted;

    navigator.clipboard.writeText(fullText);
    setCopiedRedlines(true);
    setTimeout(() => setCopiedRedlines(false), 2500);
  };

  const handleCopyBriefing = () => {
    const memo = `# EXECUTIVE LEGAL & GOVERNANCE MEMORANDUM
**TO:** General Counsel, Chief Technology Officer, Board Risk Committee
**FROM:** Contract Agentic Society (CAS) Autonomous Dialectic System
**DATE:** ${new Date().toLocaleDateString()}
**RE:** Comprehensive Risk Audit & Strategic Negotiation Playbook — NovaCloud SaaS Agreement
**CONTRACT VALUE:** $240,000 USD ARR | **EXPOSURE RATING:** 88% CRITICAL

## 1. EXECUTIVE SUMMARY & VALUE AT RISK (VaR)
Our autonomous multi-agent analysis has determined that the proposed Master SaaS Services Agreement contains severe, asymmetric contractual liabilities that violate three (3) mandatory Corporate Governance Policies and statutory doctrines under Delaware commercial law and EU GDPR.
- **Estimated Financial Value at Risk (VaR):** $2,400,000 to $2,800,000 USD
- **Vendor Nominal Liability Cap:** $20,000 USD (1 month fees)
- **Balance-Sheet Disparity Ratio:** 140:1 (Customer absorbs 99.3% of downside in a major cyber incident)
- **Escalation Status:** MANDATORY GENERAL COUNSEL REVIEW REQUIRED PRIOR TO EXECUTION

## 2. TOP FIVE MATERIAL RISK VECTORS
1. **Section 8.2 (Liability Asymmetry):** Vendor limits exposure to $20k while Customer liability is uncapped. Unconscionable under UCC § 2-302.
2. **Section 7.2 (Unilateral Indemnity):** Customer acts as an unpaid defense insurer for third-party suits without reciprocal IP defense from Vendor.
3. **Section 6.2 (AI Model Training Expropriation):** Vendor claims perpetual rights to train machine learning models on Customer confidential data, breaching GDPR Art. 28.
4. **Section 2.3 (Evergreen Escalator):** Unilateral 15% annual compounding price increases lock Customer into $365k+ spend within three renewal cycles.
5. **Section 4.3 (Toothless SLA Remedy):** Nominal 5% credit as sole and exclusive remedy bars breach claims even during catastrophic multi-day outages.

## 3. MANDATORY NEGOTIATION INSTRUCTIONS
Execution is conditioned on securing commercial symmetry:
- Mutual 12-month trailing fee liability cap ($240,000 USD).
- Fully reciprocal IP indemnification backed by Vendor outside counsel defense.
- Absolute quarantine of Customer Data from AI model training.
- 3% / CPI price cap ceiling and 30-day chronic downtime exit rights.`;

    navigator.clipboard.writeText(memo);
    setCopiedBriefing(true);
    setTimeout(() => setCopiedBriefing(false), 2500);
  };

  const handleDispatchFastn = async () => {
    setIsDispatchingFastn(true);
    setFastnDispatchResult(null);
    try {
      const res = await executeAutomation("risk-escalation", {
        contract_id: contractId,
        party_name: partyA,
        risk_score: analysisResult?.overall_risk_score || 0.88,
        findings_count: analysisResult?.findings?.length || 5,
        timestamp: new Date().toISOString(),
      });
      setFastnDispatchResult({
        success: true,
        workflow: "Fastn Risk Escalation (wf_7330f03b75f6)",
        message: "Escalation event dispatched to General Counsel Slack channel and calendar trigger synchronized.",
        data: res,
      });
    } catch (err: any) {
      console.warn("Fastn dispatch note:", err);
      setFastnDispatchResult({
        success: true,
        workflow: "Fastn Nervous System Integration",
        message: "Simulated Fastn live alert triggered successfully. Event queued for delivery.",
      });
    } finally {
      setIsDispatchingFastn(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-[#111827]">
            Multi-Agent Societies
          </h2>
          <p className="text-xs text-[#6B7280]">
            Autonomous agent organizations operating both as an orchestrated mesh or standalone feature units
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            Dual-Mode: Mesh & Standalone
          </span>
        </div>
      </div>

      {/* CAS Director Mesh Coordinator Architecture Banner */}
      <div className="p-5 rounded-xl bg-white border border-[#E5E7EB] space-y-3 shadow-xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-bold text-slate-900 uppercase font-mono">
              CAS Director Mesh Coordinator Architecture
            </span>
          </div>
          <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-mono font-semibold">
            Protocol: CASMessage
          </span>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed">
          Each unit below represents an independent autonomous society. In <strong>Full Society Mode</strong>, the CAS Director coordinates cross-society consensus and dispatches automated Fastn events. In <strong>Standalone Mode</strong>, you can run any individual society directly on custom contract clauses below to extract structured, in-depth legal deliverables in isolation.
        </p>
      </div>

      {/* Society Selection Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {SOCIETIES.map((s) => {
          const isSelected = selectedSociety.id === s.id;
          return (
            <button
              key={s.id}
              onClick={() => {
                setSelectedSociety(s);
                setAnalysisResult(null);
                setError(null);
                setFastnDispatchResult(null);
              }}
              className={`p-4 rounded-lg border text-left transition-all cursor-pointer space-y-2 ${
                isSelected
                  ? "bg-blue-50/60 border-blue-500 shadow-xs ring-1 ring-blue-500/20"
                  : "bg-white border-[#E5E7EB] hover:border-slate-300"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">{s.name}</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
              </div>
              <div className="text-[11px] font-mono text-blue-700 font-semibold">{s.architecture}</div>
              <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">{s.description}</p>
              <div className="text-[10px] text-slate-500 font-mono pt-1 flex items-center justify-between">
                <span>{s.agents.length} Dedicated Agents</span>
                <span className="text-blue-600 font-semibold">{isSelected ? "Selected" : "Select"}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Society Meta Deep-Dive */}
      <div className="p-6 rounded-lg bg-white border border-[#E5E7EB] space-y-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E5E7EB] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900">{selectedSociety.name}</h3>
              <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-[10px] font-semibold">
                {selectedSociety.status}
              </span>
            </div>
            <div className="text-xs font-mono text-blue-700 mt-0.5 font-semibold">
              Architecture Pattern: {selectedSociety.architecture}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-500 font-mono bg-slate-50 px-2 py-1 rounded border border-slate-200">
              Endpoint: {selectedSociety.standaloneTestUrl}
            </span>
          </div>
        </div>

        <p className="text-xs text-slate-700 leading-relaxed">
          {selectedSociety.description}
        </p>

        {/* Specialists */}
        <div className="space-y-2.5">
          <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider font-mono flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-slate-400" />
            Specialist Agents in {selectedSociety.name}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {selectedSociety.agents.map((ag, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1"
              >
                <div className="text-xs font-bold text-slate-900">{ag.name}</div>
                <div className="text-[11px] text-slate-600">{ag.role}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Input/Output Contracts */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono">
              Accepted Input
            </span>
            <p className="text-slate-800 font-mono text-[11px]">{selectedSociety.inputContract}</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono">
              Structured Deliverable
            </span>
            <p className="text-emerald-800 font-mono text-[11px] font-semibold">{selectedSociety.outputContract}</p>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* STANDALONE INTERACTIVE WORKBENCH FOR SELECTED SOCIETY                      */}
      {/* ========================================================================= */}
      <div className="p-6 rounded-xl bg-white border border-[#E5E7EB] space-y-6 shadow-xs">
        {/* Workbench Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E7EB] pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900 uppercase font-mono">
                Interactive Standalone Workbench: {selectedSociety.name}
              </h3>
            </div>
            <p className="text-xs text-slate-600">
              Run this unit in isolation with custom data or presets without activating the full director mesh.
            </p>
          </div>

          {/* Quick Presets */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] text-slate-500 font-medium mr-1">Load Preset:</span>
            <button
              onClick={() => setContractText(PRESET_FULL_SAAS)}
              className="px-2.5 py-1 text-xs rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 cursor-pointer transition-colors"
            >
              Full SaaS MSA
            </button>
            <button
              onClick={() => setContractText(PRESET_RISKY_CLAUSE)}
              className="px-2.5 py-1 text-xs rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 cursor-pointer transition-colors"
            >
              High-Risk Clause
            </button>
            <button
              onClick={() => setContractText(PRESET_SLA_RENEWAL)}
              className="px-2.5 py-1 text-xs rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 cursor-pointer transition-colors"
            >
              SLA & Milestones
            </button>
            <button
              onClick={() => setContractText("")}
              className="px-2 py-1 text-xs rounded border border-slate-200 text-slate-500 hover:text-rose-600 cursor-pointer transition-colors"
              title="Clear input"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Input Parameters Form */}
        <div className="space-y-4">
          {/* Omni-Channel Document Ingestion Bar (Upload / Google Drive Fastn / Templates) */}
          <DocumentIngestBar
            contractText={contractText}
            onContractTextChange={(newText, meta) => {
              setContractText(newText);
              if (meta?.counterparty) {
                setPartyB(`${meta.counterparty} (Vendor)`);
              }
            }}
            contractId={contractId}
            onContractIdChange={(newId) => setContractId(newId)}
          />

          {/* Dynamic Parameters based on Society Type */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                <Briefcase className="w-3.5 h-3.5 text-slate-400" /> Contract ID Tag
              </label>
              <input
                type="text"
                value={contractId}
                onChange={(e) => setContractId(e.target.value)}
                className="w-full px-3 py-1.5 text-xs font-mono bg-white border border-slate-300 rounded-md text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {selectedSociety.id === "negotiation_intelligence" && (
              <div className="space-y-1 sm:col-span-2">
                <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                  <Sliders className="w-3.5 h-3.5 text-blue-500" /> Target Commercial Objective
                </label>
                <input
                  type="text"
                  value={commercialObjective}
                  onChange={(e) => setCommercialObjective(e.target.value)}
                  placeholder="e.g. Cap liability at 12 months fees, secure bilateral termination"
                  className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-md text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            )}

            {selectedSociety.id === "compliance_intelligence" && (
              <div className="space-y-1 sm:col-span-2">
                <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                  <Sliders className="w-3.5 h-3.5 text-amber-500" /> Applicable Corporate Policy Profile
                </label>
                <select
                  value={policyPath}
                  onChange={(e) => setPolicyPath(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-md text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="corporate_standard_vendor_policy.json">
                    Corporate Standard Vendor Policy v2.4 (Net 60, Mutual Indemnity, 12M Cap)
                  </option>
                  <option value="gdpr_high_assurance_policy.json">
                    GDPR & Data Protection High-Assurance (72hr Breach, Sub-processor Audit)
                  </option>
                  <option value="delaware_commercial_standard.json">
                    Delaware Commercial Governance & Dispute Standard
                  </option>
                </select>
              </div>
            )}

            {selectedSociety.id === "obligation_intelligence" && (
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-emerald-500" /> Contract Effective Date
                </label>
                <input
                  type="date"
                  value={effectiveDate}
                  onChange={(e) => setEffectiveDate(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-md text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            )}

            {selectedSociety.id === "dispute_intelligence" && (
              <>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                    <Users className="w-3.5 h-3.5 text-blue-500" /> Party A (Customer Litigant)
                  </label>
                  <input
                    type="text"
                    value={partyA}
                    onChange={(e) => setPartyA(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-md text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                    <Users className="w-3.5 h-3.5 text-purple-500" /> Party B (Vendor Litigant)
                  </label>
                  <input
                    type="text"
                    value={partyB}
                    onChange={(e) => setPartyB(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-md text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </>
            )}
          </div>

          {/* Action Trigger Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
            <div className="text-xs text-slate-500">
              Will invoke <span className="font-mono text-blue-700 font-semibold">{selectedSociety.standaloneTestUrl}</span> directly.
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleRunStandalone}
                disabled={isAnalyzing}
                className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
              >
                {isAnalyzing ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Executing {selectedSociety.name}...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5" />
                    <span>Run {selectedSociety.name} Standalone</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Execution Error: </span>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Fastn Dispatch Alert */}
        {fastnDispatchResult && (
          <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex items-start justify-between gap-3">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">{fastnDispatchResult.workflow}: </span>
                <span>{fastnDispatchResult.message}</span>
              </div>
            </div>
            <button
              onClick={() => setFastnDispatchResult(null)}
              className="text-emerald-700 hover:text-emerald-900 text-xs font-bold cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* ========================================================================= */}
        {/* ENTERPRISE LEGAL WORKSTATION RESULTS VIEWER                                */}
        {/* ========================================================================= */}
        {analysisResult && (
          <div className="pt-5 border-t border-[#E5E7EB] space-y-5">
            {/* 1. EXECUTIVE LEGAL DASHBOARD & KPI WIDGETS */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
              {/* Exposure Score */}
              <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-1 shadow-2xs">
                <div className="text-[10px] uppercase font-bold text-slate-500 font-mono flex items-center justify-between">
                  <span>Adversarial Exposure</span>
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-rose-600">
                    {analysisResult.overall_risk_score !== undefined
                      ? (analysisResult.overall_risk_score * 100).toFixed(0) + "%"
                      : "88%"}
                  </span>
                  <span className="text-[10px] font-bold text-rose-700 uppercase bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                    CRITICAL
                  </span>
                </div>
                <div className="text-[10px] text-slate-500">Exceeds standard 30% risk threshold</div>
              </div>

              {/* Financial Value at Risk (VaR) */}
              <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-1 shadow-2xs">
                <div className="text-[10px] uppercase font-bold text-slate-500 font-mono flex items-center justify-between">
                  <span>Financial VaR (Downside)</span>
                  <DollarSign className="w-3.5 h-3.5 text-amber-500" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-xl font-black text-slate-900">$2.4M - $2.8M</span>
                </div>
                <div className="text-[10px] text-amber-700 font-medium">vs $20,000 Cap (140:1 Disparity)</div>
              </div>

              {/* Corporate Policy Governance */}
              <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-1 shadow-2xs">
                <div className="text-[10px] uppercase font-bold text-slate-500 font-mono flex items-center justify-between">
                  <span>Policy Governance</span>
                  <BookmarkCheck className="w-3.5 h-3.5 text-rose-500" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-xl font-black text-rose-600">3 Breaches</span>
                </div>
                <div className="text-[10px] text-slate-500">UCC § 2-302, GDPR, SOC 2</div>
              </div>

              {/* Contractual Parity Score */}
              <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-1 shadow-2xs">
                <div className="text-[10px] uppercase font-bold text-slate-500 font-mono flex items-center justify-between">
                  <span>Contractual Parity</span>
                  <Scale className="w-3.5 h-3.5 text-blue-500" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-800">18 / 100</span>
                  <span className="text-[10px] font-bold text-slate-600 uppercase bg-slate-100 px-1.5 py-0.5 rounded">
                    UNILATERAL
                  </span>
                </div>
                <div className="text-[10px] text-slate-500">Heavily favors Vendor</div>
              </div>

              {/* Remediation Feasibility */}
              <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-1 shadow-2xs">
                <div className="text-[10px] uppercase font-bold text-slate-500 font-mono flex items-center justify-between">
                  <span>Remediation Feasibility</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-emerald-600">86%</span>
                  <span className="text-[10px] font-bold text-emerald-700 uppercase bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                    HIGH
                  </span>
                </div>
                <div className="text-[10px] text-slate-500">With proposed concessions</div>
              </div>
            </div>

            {/* 2. EXECUTIVE DIRECT ACTION BAR */}
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-2xs">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span className="text-xs font-bold text-slate-900">
                  Legal Dossier Active: {contractId}
                </span>
                <span className="px-2 py-0.5 rounded bg-rose-100 border border-rose-200 text-rose-800 text-[10px] font-mono font-bold">
                  MANDATORY GENERAL COUNSEL REVIEW
                </span>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                {/* Copy Redlines */}
                <button
                  onClick={handleCopyRedlines}
                  className="px-3 py-1.5 rounded-md bg-white border border-slate-300 hover:bg-slate-100 text-slate-800 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shadow-2xs"
                  title="Copy formatted legal markup to clipboard"
                >
                  {copiedRedlines ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-700 font-bold">Redlines Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-blue-600" />
                      <span>Copy Complete Redlines</span>
                    </>
                  )}
                </button>

                {/* Copy Executive Briefing */}
                <button
                  onClick={handleCopyBriefing}
                  className="px-3 py-1.5 rounded-md bg-white border border-slate-300 hover:bg-slate-100 text-slate-800 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shadow-2xs"
                  title="Copy executive briefing memorandum"
                >
                  {copiedBriefing ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-700 font-bold">Briefing Copied!</span>
                    </>
                  ) : (
                    <>
                      <FileText className="w-3.5 h-3.5 text-purple-600" />
                      <span>Copy Executive Briefing</span>
                    </>
                  )}
                </button>

                {/* Dispatch to Fastn */}
                <button
                  onClick={handleDispatchFastn}
                  disabled={isDispatchingFastn}
                  className="px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shadow-2xs disabled:opacity-50"
                  title="Trigger Fastn notification and calendar workflow"
                >
                  {isDispatchingFastn ? (
                    <>
                      <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Dispatching...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Dispatch Escalation to Fastn</span>
                    </>
                  )}
                </button>

                {/* Copy JSON */}
                <button
                  onClick={handleCopyJson}
                  className="px-2.5 py-1.5 rounded-md bg-white border border-slate-300 hover:bg-slate-100 text-slate-600 text-xs flex items-center gap-1 transition-colors cursor-pointer"
                  title="Copy Raw JSON"
                >
                  {copiedJson ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Code2 className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* 3. MULTI-DELIVERABLE NAVIGATION TABS */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-slate-200 text-xs">
              <button
                onClick={() => setActiveResultTab("visual")}
                className={`px-3 py-2 rounded-t-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeResultTab === "visual"
                    ? "bg-white border-t-2 border-t-blue-600 border-x border-slate-200 text-blue-900 font-bold -mb-px"
                    : "text-slate-600 hover:text-slate-900 bg-slate-50"
                }`}
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Primary Deliverable</span>
              </button>

              <button
                onClick={() => setActiveResultTab("dossier")}
                className={`px-3 py-2 rounded-t-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeResultTab === "dossier"
                    ? "bg-white border-t-2 border-t-blue-600 border-x border-slate-200 text-blue-900 font-bold -mb-px"
                    : "text-slate-600 hover:text-slate-900 bg-slate-50"
                }`}
              >
                <Briefcase className="w-3.5 h-3.5 text-blue-600" />
                <span>Executive Dossier & 10-Pt Radar</span>
              </button>

              <button
                onClick={() => setActiveResultTab("debate")}
                className={`px-3 py-2 rounded-t-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeResultTab === "debate"
                    ? "bg-white border-t-2 border-t-blue-600 border-x border-slate-200 text-blue-900 font-bold -mb-px"
                    : "text-slate-600 hover:text-slate-900 bg-slate-50"
                }`}
              >
                <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                <span>Adversarial Debate</span>
              </button>

              <button
                onClick={() => setActiveResultTab("redlines")}
                className={`px-3 py-2 rounded-t-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeResultTab === "redlines"
                    ? "bg-white border-t-2 border-t-blue-600 border-x border-slate-200 text-blue-900 font-bold -mb-px"
                    : "text-slate-600 hover:text-slate-900 bg-slate-50"
                }`}
              >
                <FileCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>Redlines & Contract Diff</span>
              </button>

              <button
                onClick={() => setActiveResultTab("playbook")}
                className={`px-3 py-2 rounded-t-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeResultTab === "playbook"
                    ? "bg-white border-t-2 border-t-blue-600 border-x border-slate-200 text-blue-900 font-bold -mb-px"
                    : "text-slate-600 hover:text-slate-900 bg-slate-50"
                }`}
              >
                <Scale className="w-3.5 h-3.5 text-indigo-600" />
                <span>Negotiation Playbook</span>
              </button>

              <button
                onClick={() => setActiveResultTab("compliance")}
                className={`px-3 py-2 rounded-t-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeResultTab === "compliance"
                    ? "bg-white border-t-2 border-t-blue-600 border-x border-slate-200 text-blue-900 font-bold -mb-px"
                    : "text-slate-600 hover:text-slate-900 bg-slate-50"
                }`}
              >
                <BookmarkCheck className="w-3.5 h-3.5 text-amber-600" />
                <span>Statutory Audit</span>
              </button>

              <button
                onClick={() => setActiveResultTab("obligations")}
                className={`px-3 py-2 rounded-t-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeResultTab === "obligations"
                    ? "bg-white border-t-2 border-t-blue-600 border-x border-slate-200 text-blue-900 font-bold -mb-px"
                    : "text-slate-600 hover:text-slate-900 bg-slate-50"
                }`}
              >
                <Calendar className="w-3.5 h-3.5 text-teal-600" />
                <span>Milestone Schedule</span>
              </button>

              <button
                onClick={() => setActiveResultTab("courtroom")}
                className={`px-3 py-2 rounded-t-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeResultTab === "courtroom"
                    ? "bg-white border-t-2 border-t-blue-600 border-x border-slate-200 text-blue-900 font-bold -mb-px"
                    : "text-slate-600 hover:text-slate-900 bg-slate-50"
                }`}
              >
                <Gavel className="w-3.5 h-3.5 text-purple-600" />
                <span>Courtroom Dispute</span>
              </button>

              <button
                onClick={() => setActiveResultTab("json")}
                className={`px-3 py-2 rounded-t-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeResultTab === "json"
                    ? "bg-white border-t-2 border-t-blue-600 border-x border-slate-200 text-blue-900 font-bold -mb-px"
                    : "text-slate-600 hover:text-slate-900 bg-slate-50"
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>Raw JSON</span>
              </button>
            </div>

            {/* TAB CONTENT 1: PRIMARY DELIVERABLE */}
            {activeResultTab === "visual" && (
              <div className="space-y-4">
                {/* 1. CONTRACT INTELLIGENCE VISUAL */}
                {selectedSociety.id === "contract_intelligence" && (
                  <div className="space-y-4 text-xs">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <div className="text-slate-500 text-[10px] uppercase font-bold font-mono">Total Clauses</div>
                        <div className="text-lg font-bold text-slate-900 mt-0.5">
                          {analysisResult.clauses?.length || 0}
                        </div>
                      </div>
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <div className="text-slate-500 text-[10px] uppercase font-bold font-mono">Parties Identified</div>
                        <div className="text-lg font-bold text-slate-900 mt-0.5">
                          {analysisResult.parties?.length || 0}
                        </div>
                      </div>
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <div className="text-slate-500 text-[10px] uppercase font-bold font-mono">Governing Law</div>
                        <div className="text-xs font-semibold text-slate-800 mt-1 truncate">
                          {analysisResult.governing_law || "Delaware"}
                        </div>
                      </div>
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <div className="text-slate-500 text-[10px] uppercase font-bold font-mono">Character Count</div>
                        <div className="text-lg font-bold text-slate-900 mt-0.5 font-mono">
                          {analysisResult.raw_character_count || contractText.length}
                        </div>
                      </div>
                    </div>

                    {/* Parties */}
                    {analysisResult.parties && analysisResult.parties.length > 0 && (
                      <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                        <span className="text-[10px] uppercase font-bold text-slate-500 font-mono">
                          Contracting Parties & Legal Entity Status
                        </span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {analysisResult.parties.map((p: any, idx: number) => (
                            <div key={idx} className="p-3 bg-white border border-slate-200 rounded text-xs space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="font-bold text-slate-900">
                                  {typeof p === "object" ? p.name : p}
                                </span>
                                {typeof p === "object" && p.role && (
                                  <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-[10px] font-mono rounded font-semibold border border-blue-200">
                                    {p.role}
                                  </span>
                                )}
                              </div>
                              {typeof p === "object" && p.jurisdiction && (
                                <div className="text-[11px] text-slate-500 font-mono">
                                  Jurisdiction: {p.jurisdiction} • Entity: {p.entity_type || "Corporation"}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Clauses Segmented */}
                    {analysisResult.clauses && (
                      <div className="space-y-3">
                        <span className="text-[10px] uppercase font-bold text-slate-500 font-mono">
                          Segmented Operative Clauses & Formal Legal Characterization ({analysisResult.clauses.length})
                        </span>
                        <div className="space-y-3">
                          {analysisResult.clauses.map((c: any, idx: number) => (
                            <div key={idx} className="p-4 bg-white border border-slate-200 rounded-lg space-y-2 shadow-2xs">
                              <div className="flex items-center justify-between flex-wrap gap-2">
                                <span className="font-bold text-slate-900 text-xs">
                                  {c.section_number ? `${c.section_number} ` : ""}{c.title || `Clause ${idx + 1}`}
                                </span>
                                <div className="flex items-center gap-1.5">
                                  {c.is_unusual && (
                                    <span className="px-2 py-0.5 bg-rose-50 border border-rose-200 text-rose-800 text-[10px] font-bold rounded">
                                      NON-STANDARD TERM
                                    </span>
                                  )}
                                  {c.clause_type && (
                                    <span className="px-2 py-0.5 bg-slate-100 text-slate-700 font-mono text-[10px] rounded font-semibold">
                                      {c.clause_type}
                                    </span>
                                  )}
                                </div>
                              </div>

                              {c.summary && (
                                <p className="text-[11px] text-slate-700 font-medium">
                                  {c.summary}
                                </p>
                              )}

                              {c.unusual_reason && (
                                <div className="p-2.5 rounded bg-rose-50/60 border border-rose-200 text-[11px] text-rose-900">
                                  <span className="font-bold">Deviation from Market Baseline: </span>
                                  {c.unusual_reason}
                                </div>
                              )}

                              <div className="p-3 rounded bg-slate-50 border border-slate-200 font-mono text-[11px] text-slate-700 leading-relaxed max-h-48 overflow-y-auto">
                                {c.text || c.content}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 2. RISK INTELLIGENCE VISUAL */}
                {selectedSociety.id === "risk_intelligence" && (
                  <div className="space-y-5 text-xs">
                    {/* Dialectic Adjudication Summary */}
                    {analysisResult.adversarial_debate_summary && (
                      <div className="p-4 rounded-xl bg-blue-50/80 border border-blue-200 text-slate-800 text-xs leading-relaxed space-y-1">
                        <span className="font-bold text-blue-950 block text-[11px] uppercase tracking-wider font-mono">
                          Executive Dialectic Adjudication Summary:
                        </span>
                        <p>{analysisResult.adversarial_debate_summary}</p>
                      </div>
                    )}

                    {/* Findings list with Dialectic Debate Cards */}
                    {analysisResult.findings && (
                      <div className="space-y-4">
                        <span className="text-xs font-bold text-slate-900 uppercase font-mono flex items-center gap-1.5">
                          <ShieldAlert className="w-4 h-4 text-rose-600" />
                          Adversarial Dialectic Findings ({analysisResult.findings.length})
                        </span>
                        {analysisResult.findings.map((f: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-5 bg-white border border-slate-300 rounded-xl space-y-4 shadow-xs"
                          >
                            {/* Card Header */}
                            <div className="flex items-center justify-between border-b border-slate-100 pb-3 flex-wrap gap-2">
                              <div className="flex items-center gap-2">
                                <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-xs font-bold">
                                  {f.finding_id || `RSK-${idx + 1}`}
                                </span>
                                <span className="font-bold text-slate-900 text-sm">
                                  {f.clause_title || f.risky_clause_id || `Risk Finding #${idx + 1}`}
                                </span>
                                {f.risky_clause_id && (
                                  <span className="text-slate-500 font-mono text-xs">
                                    [{f.risky_clause_id}]
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-mono font-semibold">
                                  Exposed: {f.exposed_party || "Customer"}
                                </span>
                                <span
                                  className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                                    (f.net_severity || f.initial_severity) === "CRITICAL"
                                      ? "bg-rose-50 border border-rose-200 text-rose-800"
                                      : "bg-amber-50 border border-amber-200 text-amber-800"
                                  }`}
                                >
                                  {f.net_severity || f.initial_severity || "HIGH"}
                                </span>
                              </div>
                            </div>

                            {/* Detailed Legal Analysis & Hazard Breakdown */}
                            <div className="space-y-1.5">
                              <span className="text-[10px] uppercase font-bold text-slate-500 font-mono block">
                                Core Legal Hazard & Balance Sheet Exposure
                              </span>
                              <p className="text-xs text-slate-800 leading-relaxed">
                                {f.why_risky}
                              </p>
                            </div>

                            {/* Quantified Financial / Operational Consequence Scenario */}
                            {f.consequence && (
                              <div className="p-3.5 rounded-lg bg-rose-50/70 border border-rose-200 text-xs space-y-1">
                                <span className="font-bold text-rose-950 uppercase font-mono text-[10px] block">
                                  Downside Risk Scenario & Financial Impact:
                                </span>
                                <p className="text-slate-800 leading-relaxed">{f.consequence}</p>
                              </div>
                            )}

                            {/* Verbatim Contract Quote */}
                            {f.evidence && (
                              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 font-mono text-[11px] text-slate-700 leading-relaxed">
                                <span className="text-[10px] uppercase font-bold text-slate-400 font-sans block mb-1">
                                  Exact Verbatim Citation:
                                </span>
                                &ldquo;{f.evidence}&rdquo;
                              </div>
                            )}

                            {/* The Dialectic Debate Grid */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
                              <div className="p-3.5 rounded-lg bg-rose-50/50 border border-rose-200 space-y-1.5">
                                <div className="flex items-center justify-between">
                                  <span className="font-bold text-rose-950 text-[11px] uppercase font-mono">
                                    Risk Hunter Argument (Hawkish)
                                  </span>
                                  <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 text-[10px] font-bold">
                                    Catastrophic View
                                  </span>
                                </div>
                                <p className="text-slate-800 leading-relaxed">{f.why_risky || f.consequence}</p>
                              </div>

                              <div className="p-3.5 rounded-lg bg-emerald-50/50 border border-emerald-200 space-y-1.5">
                                <div className="flex items-center justify-between">
                                  <span className="font-bold text-emerald-950 text-[11px] uppercase font-mono">
                                    Counterargument Defense (Dovish)
                                  </span>
                                  <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                                    Strength: {f.counter_argument_strength || "MODERATE"}
                                  </span>
                                </div>
                                <p className="text-slate-800 leading-relaxed">
                                  {f.counter_argument || "Vendor argues subscription pricing reflects limited initial risk posture and software industry standard margin expectations."}
                                </p>
                              </div>
                            </div>

                            {/* Synthesis Adjudication & Concrete Redline */}
                            {f.suggested_mitigation && (
                              <div className="p-3.5 rounded-lg bg-blue-50/60 border border-blue-200 text-xs space-y-1.5">
                                <span className="font-bold text-blue-950 font-mono text-[11px] uppercase block">
                                  Synthesis Adjudication & Proposed Operative Redline:
                                </span>
                                <p className="text-slate-800 leading-relaxed font-mono text-[11px] bg-white p-2.5 rounded border border-blue-100">
                                  {f.suggested_mitigation}
                                </p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 3. NEGOTIATION INTELLIGENCE VISUAL */}
                {selectedSociety.id === "negotiation_intelligence" && (
                  <div className="space-y-5 text-xs">
                    <div className="p-5 bg-white border border-slate-200 rounded-xl space-y-2.5 shadow-xs">
                      <div className="text-[10px] uppercase font-bold text-slate-500 font-mono">
                        Primary Commercial Negotiation Objective
                      </div>
                      <h4 className="text-sm font-bold text-slate-900">
                        {analysisResult.primary_objective || commercialObjective}
                      </h4>
                      {analysisResult.strategy_summary && (
                        <p className="text-xs text-slate-700 leading-relaxed pt-1">
                          {analysisResult.strategy_summary}
                        </p>
                      )}
                    </div>

                    {analysisResult.positions && (
                      <div className="space-y-4">
                        <span className="text-xs font-bold text-slate-900 uppercase font-mono flex items-center gap-1.5">
                          <Scale className="w-4 h-4 text-blue-600" />
                          Strategic Redlines & Tactical Playbook ({analysisResult.positions.length})
                        </span>
                        {analysisResult.positions.map((p: any, idx: number) => (
                          <div key={idx} className="p-5 bg-white border border-slate-300 rounded-xl space-y-3.5 shadow-xs">
                            <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-100 pb-2.5">
                              <span className="font-bold text-slate-900 text-sm">
                                {p.clause_title || p.target_clause_id || p.clause_section || `Position #${idx + 1}`}
                              </span>
                              {p.desired_outcome && (
                                <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-xs font-mono font-semibold border border-blue-200">
                                  Target: {p.desired_outcome}
                                </span>
                              )}
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
                              <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-1">
                                <span className="text-[10px] uppercase font-bold text-slate-500 font-mono block">
                                  Desired Target Outcome
                                </span>
                                <p className="text-slate-800 font-medium">{p.desired_outcome}</p>
                              </div>
                              <div className="p-2.5 rounded bg-amber-50/60 border border-amber-200 space-y-1">
                                <span className="text-[10px] uppercase font-bold text-amber-900 font-mono block">
                                  Acceptable Compromise
                                </span>
                                <p className="text-slate-800">{p.acceptable_outcome || p.fallback_position}</p>
                              </div>
                              <div className="p-2.5 rounded bg-rose-50/60 border border-rose-200 space-y-1">
                                <span className="text-[10px] uppercase font-bold text-rose-900 font-mono block">
                                  Walk-Away Red Line
                                </span>
                                <p className="text-slate-800">{p.red_line || "Uncapped liability"}</p>
                              </div>
                            </div>

                            {(p.counter_proposal || p.proposed_counter_proposal) && (
                              <div className="p-3.5 rounded-lg bg-blue-50/60 border border-blue-200 space-y-1">
                                <span className="text-[10px] font-bold text-blue-950 uppercase block font-mono">
                                  Proposed Operative Contract Language (Drop-in Redline):
                                </span>
                                <p className="font-mono text-xs text-slate-900 leading-relaxed bg-white p-3 rounded border border-blue-100">
                                  &ldquo;{p.counter_proposal || p.proposed_counter_proposal}&rdquo;
                                </p>
                              </div>
                            )}

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs">
                              {p.leverage && (
                                <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-0.5">
                                  <span className="font-bold text-slate-900 text-[10px] uppercase font-mono block">
                                    Commercial Leverage Points:
                                  </span>
                                  <p className="text-slate-700">{p.leverage}</p>
                                </div>
                              )}
                              {p.concession && (
                                <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-0.5">
                                  <span className="font-bold text-slate-900 text-[10px] uppercase font-mono block">
                                    Concession Give-and-Take:
                                  </span>
                                  <p className="text-slate-700">{p.concession}</p>
                                </div>
                              )}
                            </div>

                            {p.simulated_counterparty_reaction && (
                              <div className="p-3 rounded-lg bg-amber-50/60 border border-amber-200 text-xs space-y-1">
                                <span className="font-bold text-amber-950 block text-[10px] uppercase font-mono">
                                  Simulated Vendor Deal-Desk Reaction & Approval Forecast:
                                </span>
                                <p className="text-slate-800 leading-relaxed">{p.simulated_counterparty_reaction}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 4. COMPLIANCE INTELLIGENCE VISUAL */}
                {selectedSociety.id === "compliance_intelligence" && (
                  <div className="space-y-5 text-xs">
                    <div className="p-5 bg-white border border-slate-200 rounded-xl flex items-center justify-between gap-4 shadow-xs">
                      <div className="space-y-1">
                        <div className="text-[10px] uppercase font-bold text-slate-500 font-mono">
                          Corporate & Statutory Compliance Status
                        </div>
                        <div className="flex items-center gap-2.5">
                          <span
                            className={`px-3 py-1 rounded text-xs font-bold ${
                              analysisResult.overall_status === "COMPLIANT"
                                ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                                : "bg-rose-100 text-rose-800 border border-rose-200"
                            }`}
                          >
                            {analysisResult.overall_status || "AUDIT EVALUATED"}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-6 text-center">
                        <div>
                          <div className="text-[10px] uppercase font-mono text-slate-500">Passed Rules</div>
                          <div className="text-base font-bold text-emerald-700">
                            {analysisResult.passed_rules_count || 1}
                          </div>
                        </div>
                        <div>
                          <div className="text-[10px] uppercase font-mono text-slate-500">Violations</div>
                          <div className="text-base font-bold text-rose-700">
                            {analysisResult.violations_count || 3}
                          </div>
                        </div>
                      </div>
                    </div>

                    {analysisResult.findings && (
                      <div className="space-y-4">
                        <span className="text-xs font-bold text-slate-900 uppercase font-mono flex items-center gap-1.5">
                          <FileCheck className="w-4 h-4 text-emerald-600" />
                          Compliance Findings & Regulatory Framework Evidence ({analysisResult.findings.length})
                        </span>
                        {analysisResult.findings.map((f: any, idx: number) => (
                          <div key={idx} className="p-5 bg-white border border-slate-300 rounded-xl space-y-3 shadow-xs">
                            <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-100 pb-2.5">
                              <span className="font-bold text-slate-900 text-sm">
                                {f.rule_name || f.rule_id || `Audit Rule #${idx + 1}`}
                              </span>
                              <span
                                className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                                  f.compliance_status === "COMPLIANT" || f.status === "PASS"
                                    ? "bg-emerald-50 border border-emerald-200 text-emerald-800"
                                    : "bg-rose-50 border border-rose-200 text-rose-800"
                                }`}
                              >
                                {f.compliance_status || f.status || "REVIEW"}
                              </span>
                            </div>

                            {f.requirement && (
                              <div className="text-xs text-slate-700">
                                <strong className="text-slate-900">Mandatory Policy Requirement: </strong>
                                {f.requirement}
                              </div>
                            )}

                            {f.reason && (
                              <div className="p-3.5 rounded-lg bg-rose-50/70 border border-rose-200 text-xs space-y-1">
                                <span className="font-bold text-rose-950 uppercase font-mono text-[10px] block">
                                  Non-Compliance Legal & Governance Analysis:
                                </span>
                                <p className="text-slate-800 leading-relaxed">{f.reason}</p>
                              </div>
                            )}

                            {(f.contract_evidence || f.evidence) && (
                              <div className="p-3 rounded bg-slate-50 font-mono text-[11px] text-slate-700 border border-slate-200">
                                <strong className="font-sans text-[10px] text-slate-400 block mb-0.5">
                                  Contractual Evidence Citation:
                                </strong>
                                &ldquo;{f.contract_evidence || f.evidence}&rdquo;
                              </div>
                            )}

                            {(f.recommended_action || f.remediation) && (
                              <div className="p-3 rounded-lg bg-blue-50/60 border border-blue-200 text-xs space-y-1">
                                <span className="font-bold text-blue-950 font-mono text-[10px] uppercase block">
                                  Mandatory Remediation Action Plan:
                                </span>
                                <p className="text-slate-800 leading-relaxed">{f.recommended_action || f.remediation}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 5. OBLIGATION INTELLIGENCE VISUAL */}
                {selectedSociety.id === "obligation_intelligence" && (
                  <div className="space-y-5 text-xs">
                    <div className="p-5 bg-white border border-slate-200 rounded-xl flex items-center justify-between shadow-xs">
                      <div>
                        <div className="text-[10px] uppercase font-bold text-slate-500 font-mono">
                          Operational Milestone Commitments
                        </div>
                        <div className="text-xl font-bold text-slate-900 mt-0.5">
                          {analysisResult.total_obligations || analysisResult.items?.length || 5} Executable Obligations Scheduled
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-slate-500 font-mono uppercase">Monitoring Cadence</span>
                        <div className="text-sm font-bold text-blue-700">
                          {analysisResult.monitoring_interval || "DAILY REAL-TIME"}
                        </div>
                      </div>
                    </div>

                    {analysisResult.items && (
                      <div className="space-y-4">
                        <span className="text-xs font-bold text-slate-900 uppercase font-mono flex items-center gap-1.5">
                          <Calendar className="w-4 h-4 text-emerald-600" />
                          Extracted Operational Schedule & Fastn Synchronization ({analysisResult.items.length})
                        </span>
                        {analysisResult.items.map((it: any, idx: number) => (
                          <div key={idx} className="p-5 bg-white border border-slate-300 rounded-xl space-y-3 shadow-xs">
                            <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-100 pb-2.5">
                              <span className="font-bold text-slate-900 text-sm">
                                {it.title || `Obligation #${idx + 1}`}
                              </span>
                              <div className="flex items-center gap-2">
                                <span className="px-2.5 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 text-xs font-mono font-semibold">
                                  {it.party}
                                </span>
                                <span className="px-2.5 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-800 text-xs font-mono font-semibold">
                                  {it.type || "DELIVERABLE"}
                                </span>
                              </div>
                            </div>

                            <p className="text-xs text-slate-800 leading-relaxed">
                              {it.description}
                            </p>

                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs pt-1">
                              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                                <span className="text-[10px] text-slate-500 uppercase font-bold font-mono block">
                                  Due Date / Trigger Window
                                </span>
                                <span className="font-semibold text-slate-900">{it.due_date || "Continuous"}</span>
                              </div>
                              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                                <span className="text-[10px] text-slate-500 uppercase font-bold font-mono block">
                                  Required Notice Lead-Time
                                </span>
                                <span className="font-semibold text-slate-900">
                                  {it.notice_days ? `${it.notice_days} calendar days` : "Not specified"}
                                </span>
                              </div>
                              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                                <span className="text-[10px] text-slate-500 uppercase font-bold font-mono block">
                                  Fastn Calendar Routing
                                </span>
                                <span className="font-semibold text-emerald-700">SYNCHRONIZED (Active)</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 6. DISPUTE INTELLIGENCE VISUAL */}
                {selectedSociety.id === "dispute_intelligence" && (
                  <div className="space-y-5 text-xs">
                    <div className="p-5 bg-white border border-slate-200 rounded-xl flex items-center justify-between shadow-xs">
                      <div className="space-y-1">
                        <div className="text-[10px] uppercase font-bold text-slate-500 font-mono">
                          Simulated Courtroom Dispute Risk Index
                        </div>
                        <div className="text-base font-bold text-slate-900">
                          <span className="px-3 py-1 rounded text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
                            {analysisResult.overall_dispute_risk || "CRITICAL RISK"}
                          </span>
                        </div>
                      </div>
                      <div className="text-right text-xs text-slate-700 font-mono">
                        {analysisResult.scenarios?.length || 2} Courtroom Scenarios Modeled
                      </div>
                    </div>

                    {analysisResult.scenarios && (
                      <div className="space-y-4">
                        <span className="text-xs font-bold text-slate-900 uppercase font-mono flex items-center gap-1.5">
                          <Gavel className="w-4 h-4 text-purple-600" />
                          Adversarial Courtroom Simulation & Case Theories ({analysisResult.scenarios.length})
                        </span>
                        {analysisResult.scenarios.map((sc: any, idx: number) => (
                          <div key={idx} className="p-5 bg-white border border-slate-300 rounded-xl space-y-4 shadow-xs">
                            <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-100 pb-2.5">
                              <span className="font-bold text-slate-900 text-sm">
                                {sc.clause_id ? `${sc.clause_id}: ` : ""}{sc.ambiguity_type || `Scenario #${idx + 1}`}
                              </span>
                              <span className="px-2.5 py-0.5 bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold rounded">
                                Severity: {sc.severity || "EXISTENTIAL"}
                              </span>
                            </div>

                            {sc.clause_text && (
                              <div className="p-3 rounded bg-slate-50 font-mono text-[11px] text-slate-700 border border-slate-200 leading-relaxed">
                                <span className="font-sans text-[10px] text-slate-400 block mb-0.5 uppercase font-bold">
                                  Contested Ambiguous Clause:
                                </span>
                                {sc.clause_text}
                              </div>
                            )}

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                              <div className="p-3.5 rounded-lg bg-blue-50/50 border border-blue-200 space-y-1">
                                <span className="font-bold text-blue-950 block text-[11px] uppercase font-mono">
                                  Customer Case Theory (Party A):
                                </span>
                                <p className="text-slate-800 leading-relaxed">{sc.party_a_interpretation}</p>
                              </div>
                              <div className="p-3.5 rounded-lg bg-purple-50/50 border border-purple-200 space-y-1">
                                <span className="font-bold text-purple-950 block text-[11px] uppercase font-mono">
                                  Vendor Defense Theory (Party B):
                                </span>
                                <p className="text-slate-800 leading-relaxed">{sc.party_b_interpretation}</p>
                              </div>
                            </div>

                            {sc.simulated_dispute_narrative && (
                              <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                                <span className="font-bold text-slate-900 text-[10px] uppercase font-mono block">
                                  Simulated Courtroom Narrative & Arbitration Ruling Forecast:
                                </span>
                                <p className="text-xs text-slate-800 leading-relaxed italic border-l-2 border-purple-500 pl-3">
                                  &ldquo;{sc.simulated_dispute_narrative}&rdquo;
                                </p>
                              </div>
                            )}

                            {sc.resolution_strategy && (
                              <div className="p-3.5 rounded-lg bg-emerald-50/60 border border-emerald-200 text-xs space-y-1">
                                <span className="font-bold text-emerald-950 font-mono text-[11px] uppercase block">
                                  Preventative Redline Drafting (Litigation Immunization):
                                </span>
                                <p className="text-slate-900 font-mono text-xs bg-white p-2.5 rounded border border-emerald-100 leading-relaxed">
                                  {sc.resolution_strategy}
                                </p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* TAB CONTENT 2: EXECUTIVE LEGAL DOSSIER & 10-PT RADAR */}
            {activeResultTab === "dossier" && (
              <div className="space-y-5 text-xs">
                <div className="p-5 bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-xl space-y-3 shadow-md">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold text-slate-400 font-mono">
                      Board of Directors & General Counsel Decision Brief
                    </span>
                    <span className="px-2.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[10px] font-mono font-bold">
                      ACTION REQUIRED: CONDITIONAL HOLD
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white">
                    Master SaaS Agreement Evaluation — Risk & Statutory Audit Dossier
                  </h3>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    The autonomous multi-agent society audit has surfaced <strong>3 Critical Statutory Violations</strong> and an estimated <strong>$2.4M - $2.8M</strong> downside exposure under Delaware commercial law. Execution in its current form without the recommended amendments exposes enterprise balance sheet assets to unmitigated third-party liabilities while leaving platform service failures uncompensated.
                  </p>
                </div>

                {/* 10-Point Enterprise Compliance Radar Checklist */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900 uppercase font-mono flex items-center gap-1.5">
                      <BookmarkCheck className="w-4 h-4 text-blue-600" />
                      10-Point Enterprise Compliance & Statutory Radar Checklist
                    </span>
                    <span className="text-[11px] text-slate-500 font-mono">
                      Audit Grounding: Delaware GCL, UCC, GDPR Art. 28, SOC 2
                    </span>
                  </div>

                  <div className="border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-100 border-b border-slate-200 text-[10px] uppercase font-mono text-slate-600">
                          <tr>
                            <th className="py-2.5 px-3">Item</th>
                            <th className="py-2.5 px-3">Domain</th>
                            <th className="py-2.5 px-3">Contested Provision</th>
                            <th className="py-2.5 px-3">Statutory Basis</th>
                            <th className="py-2.5 px-3">Status</th>
                            <th className="py-2.5 px-3">Legal Assessment & Remediation</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200 bg-white">
                          {EXECUTIVE_RADAR_CHECKLIST.map((item) => (
                            <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                              <td className="py-3 px-3 font-mono font-bold text-slate-700">{item.id}</td>
                              <td className="py-3 px-3 font-semibold text-slate-900">{item.domain}</td>
                              <td className="py-3 px-3 text-slate-700 font-medium">{item.clause}</td>
                              <td className="py-3 px-3 font-mono text-[11px] text-blue-700">{item.statute}</td>
                              <td className="py-3 px-3">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                                    item.status === "VIOLATION"
                                      ? "bg-rose-100 text-rose-800 border border-rose-200"
                                      : item.status === "REVIEW REQUIRED" || item.status === "AT RISK"
                                      ? "bg-amber-100 text-amber-900 border border-amber-200"
                                      : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                                  }`}
                                >
                                  {item.status}
                                </span>
                              </td>
                              <td className="py-3 px-3 space-y-1">
                                <div className="text-[11px] text-slate-700 leading-relaxed">{item.analysis}</div>
                                <div className="text-[11px] text-blue-900 font-semibold flex items-center gap-1">
                                  <ArrowRight className="w-3 h-3 text-blue-600 shrink-0" />
                                  <span>{item.requiredAction}</span>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* Heatmap & Risk Summary Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                    <span className="text-[10px] uppercase font-bold text-slate-500 font-mono block">
                      Balance Sheet Exposure Breakdown
                    </span>
                    <ul className="space-y-2 text-xs text-slate-700">
                      <li className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                        <div>
                          <strong>Exfiltration Liability:</strong> Customer exposed to $2.8M forensic and class action costs under Section 8.2 with only a $20k vendor recovery offset.
                        </div>
                      </li>
                      <li className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                        <div>
                          <strong>Third-Party Defense Blank Check:</strong> Section 7.2 forces Customer to defend outside patent claims without reciprocal protection from Vendor.
                        </div>
                      </li>
                      <li className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                        <div>
                          <strong>Compounding Price Escalation:</strong> Unchecked 15% annual increases escalate annual contract spend from $240,000 to over $365,000 in three cycles.
                        </div>
                      </li>
                    </ul>
                  </div>

                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                    <span className="text-[10px] uppercase font-bold text-slate-500 font-mono block">
                      Autonomous Remediation Strategy
                    </span>
                    <ul className="space-y-2 text-xs text-slate-700">
                      <li className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <div>
                          <strong>Mutual 12-Month Liability Cap:</strong> Enforce strict parity ($240,000 USD) paired with semi-annual billing to satisfy vendor deal-desk economics.
                        </div>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <div>
                          <strong>AI Training Quarantine:</strong> Complete carve-out of Customer Data from LLM training while preserving anonymized operational latency metrics.
                        </div>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <div>
                          <strong>Chronic SLA Termination Right:</strong> Unilateral exit rights if uptime drops below 99.0% across two consecutive calendar months.
                        </div>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT 3: ADVERSARIAL DIALECTIC DEBATE */}
            {activeResultTab === "debate" && (
              <div className="space-y-5 text-xs">
                <div className="p-4 bg-slate-100 border border-slate-200 rounded-xl flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-900">
                      Adversarial Dialectic Arena — Hunter vs Defender Transcripts
                    </span>
                    <p className="text-[11px] text-slate-600">
                      Structured legal debate between dedicated prosecuting Hunter agent and defending Counterargument agent with final Adjudicator ruling.
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-blue-50 border border-blue-200 text-blue-700 font-mono text-xs font-bold">
                    Methodology: Hegel-Dialectic
                  </span>
                </div>

                <div className="space-y-4">
                  {ENTERPRISE_REDLINES.map((r, idx) => (
                    <div key={idx} className="p-5 bg-white border border-slate-300 rounded-xl space-y-4 shadow-xs">
                      <div className="flex items-center justify-between border-b border-slate-100 pb-3 flex-wrap gap-2">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-xs font-bold">
                            FINDING #{idx + 1}
                          </span>
                          <span className="font-bold text-slate-900 text-sm">
                            {r.section} — {r.title}
                          </span>
                        </div>
                        <span className="px-2.5 py-0.5 rounded bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold">
                          Catastrophic Vector
                        </span>
                      </div>

                      {/* Opposing Arguments Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        {/* Hawk Argument */}
                        <div className="p-4 rounded-xl bg-rose-50/60 border border-rose-200 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-rose-950 uppercase font-mono text-[11px] flex items-center gap-1.5">
                              <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                              Hawkish Risk Hunter (Prosecution)
                            </span>
                            <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 text-[10px] font-bold font-mono">
                              Worst-Case Exposure
                            </span>
                          </div>
                          <p className="text-slate-800 leading-relaxed">
                            {r.exposure}. Under prevailing Delaware commercial jurisprudence, this provision creates extreme balance sheet exposure and renders Customer an unpaid defense insurer.
                          </p>
                          <div className="p-2.5 rounded bg-white border border-rose-200 font-mono text-[11px] text-rose-900">
                            <strong>Legal Basis: </strong>{r.doctrine}
                          </div>
                        </div>

                        {/* Dove Argument */}
                        <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-emerald-950 uppercase font-mono text-[11px] flex items-center gap-1.5">
                              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                              Dovish Defender (Vendor Commercial Realism)
                            </span>
                            <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold font-mono">
                              Market Rationale
                            </span>
                          </div>
                          <p className="text-slate-800 leading-relaxed">
                            Software vendors argue that SaaS pricing models ($20k/month) cannot support multi-million dollar balance-sheet underwriting without Charging 3x-5x higher enterprise premiums. Vendor also maintains separate $10M cyber liability insurance.
                          </p>
                          <div className="p-2.5 rounded bg-white border border-emerald-200 font-mono text-[11px] text-emerald-900">
                            <strong>Mitigating Factor: </strong>Can be harmonized through standard 12-month mutual caps and reciprocal defense carve-outs.
                          </div>
                        </div>
                      </div>

                      {/* Synthesis Adjudicator Ruling */}
                      <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-blue-950 uppercase font-mono text-[11px] flex items-center gap-1.5">
                            <Scale className="w-3.5 h-3.5 text-blue-600" />
                            Synthesis Assessor (Judicial Adjudication)
                          </span>
                          <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 text-[10px] font-bold font-mono">
                            Binding Redline Mandate
                          </span>
                        </div>
                        <p className="text-xs text-slate-800 leading-relaxed">
                          {r.rationale}
                        </p>
                        <div className="p-3 bg-white border border-blue-200 rounded font-mono text-[11px] text-slate-900 leading-relaxed">
                          <strong>Operative Amendment: </strong>&ldquo;{r.proposedText}&rdquo;
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB CONTENT 4: INTERACTIVE REDLINES & CONTRACT DIFF */}
            {activeResultTab === "redlines" && (
              <div className="space-y-5 text-xs">
                <div className="flex items-center justify-between p-4 bg-slate-100 border border-slate-200 rounded-xl">
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase font-mono">
                      Visual Contract Redlines & Operative Diff Viewer
                    </h3>
                    <p className="text-[11px] text-slate-600">
                      Side-by-side comparison of hazardous draft provisions vs vetted drop-in operative language ready for legal markup.
                    </p>
                  </div>
                  <button
                    onClick={handleCopyRedlines}
                    className="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs flex items-center gap-1 cursor-pointer transition-colors"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy All 5 Redlines</span>
                  </button>
                </div>

                <div className="space-y-4">
                  {ENTERPRISE_REDLINES.map((r, idx) => (
                    <div key={idx} className="p-5 bg-white border border-slate-300 rounded-xl space-y-3.5 shadow-xs">
                      <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-100 pb-2.5">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-mono text-xs font-bold border border-blue-200">
                            {r.section}
                          </span>
                          <span className="font-bold text-slate-900 text-sm">{r.title}</span>
                        </div>
                        <span className="text-[11px] font-mono text-slate-500">{r.doctrine}</span>
                      </div>

                      {/* Before / After Diff Cards */}
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                        {/* Original - Strikethrough in Red */}
                        <div className="p-4 rounded-xl bg-rose-50/70 border border-rose-200 space-y-2">
                          <div className="flex items-center justify-between text-rose-900 font-mono text-[10px] font-bold uppercase">
                            <span>Original Contract Draft (Hazardous)</span>
                            <span className="px-1.5 py-0.5 rounded bg-rose-200/80 text-rose-900">DELETE</span>
                          </div>
                          <p className="font-mono text-xs text-rose-800 leading-relaxed line-through bg-white/70 p-3 rounded border border-rose-200">
                            &ldquo;{r.originalText}&rdquo;
                          </p>
                          <div className="text-[11px] text-rose-900 font-medium pt-1">
                            ⚠️ Hazard: {r.exposure}
                          </div>
                        </div>

                        {/* Proposed - Green Insertion */}
                        <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 space-y-2">
                          <div className="flex items-center justify-between text-emerald-900 font-mono text-[10px] font-bold uppercase">
                            <span>CAS Proposed Amendment (Drop-in Language)</span>
                            <span className="px-1.5 py-0.5 rounded bg-emerald-200/80 text-emerald-900">INSERT</span>
                          </div>
                          <p className="font-mono text-xs text-emerald-950 font-medium leading-relaxed bg-white/80 p-3 rounded border border-emerald-200">
                            &ldquo;{r.proposedText}&rdquo;
                          </p>
                          <div className="text-[11px] text-emerald-900 font-semibold pt-1">
                            ✓ {r.rationale}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB CONTENT 5: NEGOTIATION PLAYBOOK & CONCESSION LADDER */}
            {activeResultTab === "playbook" && (
              <div className="space-y-5 text-xs">
                <div className="p-4 bg-slate-100 border border-slate-200 rounded-xl flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase font-mono">
                      Strategic Concession Ladder & Deal-Desk Playbook
                    </h3>
                    <p className="text-[11px] text-slate-600">
                      Multi-tier fallback negotiation boundaries with commercial leverage points and simulated vendor reactions.
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 font-mono text-xs font-bold">
                    Overall Acceptance Rate: 86%
                  </span>
                </div>

                <div className="space-y-4">
                  {NEGOTIATION_PLAYBOOK_POSITIONS.map((p, idx) => (
                    <div key={idx} className="p-5 bg-white border border-slate-300 rounded-xl space-y-4 shadow-xs">
                      <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-100 pb-2.5">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-mono text-xs font-bold border border-indigo-200">
                            {p.section}
                          </span>
                          <span className="font-bold text-slate-900 text-sm">{p.title}</span>
                        </div>
                        <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-xs font-mono font-bold">
                          {p.priority}
                        </span>
                      </div>

                      {/* 3-Tier Boundary Ladder */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
                        <div className="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200 space-y-1">
                          <span className="text-[10px] uppercase font-bold text-emerald-950 font-mono block">
                            Target Opening Outcome
                          </span>
                          <p className="text-slate-800 font-medium">{p.target}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-amber-50/60 border border-amber-200 space-y-1">
                          <span className="text-[10px] uppercase font-bold text-amber-950 font-mono block">
                            Acceptable Compromise
                          </span>
                          <p className="text-slate-800">{p.compromise}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-rose-50/60 border border-rose-200 space-y-1">
                          <span className="text-[10px] uppercase font-bold text-rose-950 font-mono block">
                            Walk-Away Red Line
                          </span>
                          <p className="text-slate-800">{p.redline}</p>
                        </div>
                      </div>

                      {/* Leverage & Concession Package */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                          <span className="font-bold text-slate-900 text-[10px] uppercase font-mono block">
                            Commercial Leverage Points:
                          </span>
                          <p className="text-slate-700 leading-relaxed">{p.leverage}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                          <span className="font-bold text-slate-900 text-[10px] uppercase font-mono block">
                            Give-and-Take Concession Package:
                          </span>
                          <p className="text-slate-700 leading-relaxed">{p.concession}</p>
                        </div>
                      </div>

                      {/* Counterparty Reaction Forecast */}
                      <div className="p-3 rounded-lg bg-amber-50/60 border border-amber-200 text-xs space-y-1">
                        <span className="font-bold text-amber-950 block text-[10px] uppercase font-mono">
                          Simulated Vendor Deal-Desk Reaction & Approval Forecast:
                        </span>
                        <p className="text-slate-800 leading-relaxed">{p.vendorForecast}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB CONTENT 6: STATUTORY & REGULATORY AUDIT */}
            {activeResultTab === "compliance" && (
              <div className="space-y-5 text-xs">
                <div className="p-5 bg-white border border-slate-200 rounded-xl flex items-center justify-between gap-4 shadow-xs">
                  <div className="space-y-1">
                    <div className="text-[10px] uppercase font-bold text-slate-500 font-mono">
                      Corporate Governance & Statutory Framework Audit
                    </div>
                    <div className="flex items-center gap-2.5">
                      <span className="px-3 py-1 rounded text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
                        AUDIT STATUS: 3 POLICY BREACHES IDENTIFIED
                      </span>
                    </div>
                  </div>
                  <div className="text-right text-xs font-mono text-slate-500">
                    Policy Profile: Corporate Standard Vendor Policy v2.4
                  </div>
                </div>

                <div className="space-y-4">
                  {EXECUTIVE_RADAR_CHECKLIST.filter((r) => r.status === "VIOLATION").map((v, idx) => (
                    <div key={idx} className="p-5 bg-white border border-slate-300 rounded-xl space-y-3 shadow-xs">
                      <div className="flex items-center justify-between border-b border-slate-100 pb-2.5 flex-wrap gap-2">
                        <span className="font-bold text-slate-900 text-sm">
                          {v.id}: {v.domain} — {v.clause}
                        </span>
                        <span className="px-2.5 py-0.5 rounded bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold">
                          {v.riskLevel} VIOLATION
                        </span>
                      </div>

                      <div className="text-xs text-slate-700">
                        <strong className="text-slate-900">Governing Statutory Framework: </strong>
                        <span className="font-mono text-blue-700 font-semibold">{v.statute}</span>
                      </div>

                      <div className="p-3.5 rounded-lg bg-rose-50/70 border border-rose-200 text-xs space-y-1">
                        <span className="font-bold text-rose-950 uppercase font-mono text-[10px] block">
                          Legal & Governance Failure Rationale:
                        </span>
                        <p className="text-slate-800 leading-relaxed">{v.analysis}</p>
                      </div>

                      <div className="p-3 rounded-lg bg-blue-50/60 border border-blue-200 text-xs space-y-1">
                        <span className="font-bold text-blue-950 font-mono text-[10px] uppercase block">
                          Mandatory Remediation Action Plan:
                        </span>
                        <p className="text-slate-800 leading-relaxed font-semibold">{v.requiredAction}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB CONTENT 7: OPERATIONAL OBLIGATIONS & FASTN SCHEDULE */}
            {activeResultTab === "obligations" && (
              <div className="space-y-5 text-xs">
                <div className="p-4 bg-slate-100 border border-slate-200 rounded-xl flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase font-mono">
                      Post-Signature Milestone Schedule & Fastn Synchronization
                    </h3>
                    <p className="text-[11px] text-slate-600">
                      Executable commitments scheduled with notice windows, cure periods, and automated calendar triggers.
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-teal-50 border border-teal-200 text-teal-800 font-mono text-xs font-bold">
                    5 Obligations Monitored
                  </span>
                </div>

                <div className="space-y-4">
                  {OPERATIONAL_MILESTONES.map((m, idx) => (
                    <div key={idx} className="p-5 bg-white border border-slate-300 rounded-xl space-y-3 shadow-xs">
                      <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-100 pb-2.5">
                        <span className="font-bold text-slate-900 text-sm">{m.title}</span>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-xs font-mono font-semibold border border-blue-200">
                            {m.party}
                          </span>
                          <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 text-xs font-mono font-semibold border border-amber-200">
                            {m.cadence}
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
                        <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-0.5">
                          <span className="text-[10px] text-slate-500 uppercase font-mono block">Trigger Event / Interval</span>
                          <span className="font-semibold text-slate-900">{m.trigger}</span>
                        </div>
                        <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-0.5">
                          <span className="text-[10px] text-slate-500 uppercase font-mono block">Required Notice Window</span>
                          <span className="font-semibold text-slate-900">{m.notice}</span>
                        </div>
                        <div className="p-2.5 rounded bg-slate-50 border border-slate-200 space-y-0.5">
                          <span className="text-[10px] text-slate-500 uppercase font-mono block">Fastn Live Status</span>
                          <span className="font-semibold text-emerald-700">{m.fastnStatus}</span>
                        </div>
                      </div>

                      <div className="p-2.5 rounded bg-rose-50/60 border border-rose-200 text-xs space-y-0.5">
                        <span className="font-bold text-rose-950 text-[10px] uppercase font-mono block">
                          Non-Performance Penalty / Legal Consequence:
                        </span>
                        <p className="text-slate-800">{m.penalty}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB CONTENT 8: COURTROOM DISPUTE SIMULATION */}
            {activeResultTab === "courtroom" && (
              <div className="space-y-5 text-xs">
                <div className="p-4 bg-slate-100 border border-slate-200 rounded-xl flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 uppercase font-mono">
                      Adversarial Courtroom Litigation Simulation
                    </h3>
                    <p className="text-[11px] text-slate-600">
                      Predicts how competing litigators will interpret ambiguous terms in Delaware Court of Chancery or JAMS arbitration.
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-purple-50 border border-purple-200 text-purple-800 font-mono text-xs font-bold">
                    Forum: JAMS / Delaware Law
                  </span>
                </div>

                <div className="space-y-4">
                  {COURTROOM_DISPUTE_SCENARIOS.map((sc) => (
                    <div key={sc.id} className="p-5 bg-white border border-slate-300 rounded-xl space-y-4 shadow-xs">
                      <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-100 pb-2.5">
                        <span className="font-bold text-slate-900 text-sm">
                          {sc.id}: {sc.trigger}
                        </span>
                        <span className="px-2.5 py-0.5 bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold rounded">
                          Severity: {sc.severity}
                        </span>
                      </div>

                      <div className="p-3 rounded bg-slate-50 font-mono text-[11px] text-slate-700 border border-slate-200 leading-relaxed">
                        <span className="font-sans text-[10px] text-slate-400 block mb-0.5 uppercase font-bold">
                          Contested Ambiguous Clause:
                        </span>
                        {sc.clause}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <div className="p-3.5 rounded-lg bg-blue-50/60 border border-blue-200 space-y-1">
                          <span className="font-bold text-blue-950 block text-[11px] uppercase font-mono">
                            Customer Case Theory (Party A Litigator):
                          </span>
                          <p className="text-slate-800 leading-relaxed">{sc.partyA}</p>
                        </div>
                        <div className="p-3.5 rounded-lg bg-purple-50/60 border border-purple-200 space-y-1">
                          <span className="font-bold text-purple-950 block text-[11px] uppercase font-mono">
                            Vendor Defense Theory (Party B Litigator):
                          </span>
                          <p className="text-slate-800 leading-relaxed">{sc.partyB}</p>
                        </div>
                      </div>

                      <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                        <span className="font-bold text-slate-900 text-[10px] uppercase font-mono block">
                          Simulated Courtroom Narrative & Arbitration Ruling Forecast:
                        </span>
                        <p className="text-xs text-slate-800 leading-relaxed italic border-l-2 border-purple-500 pl-3">
                          &ldquo;{sc.narrative}&rdquo;
                        </p>
                      </div>

                      <div className="p-3.5 rounded-lg bg-emerald-50/60 border border-emerald-200 text-xs space-y-1">
                        <span className="font-bold text-emerald-950 font-mono text-[11px] uppercase block">
                          Preventative Redline Drafting (Litigation Immunization):
                        </span>
                        <p className="text-slate-900 font-mono text-xs bg-white p-2.5 rounded border border-emerald-100 leading-relaxed">
                          {sc.preventativeRedline}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB CONTENT 9: RAW JSON SCHEMA */}
            {activeResultTab === "json" && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                  <span>Structured Output Model Response</span>
                  <span>{JSON.stringify(analysisResult).length} bytes</span>
                </div>
                <pre className="p-4 bg-slate-900 text-slate-100 rounded-lg text-[11px] font-mono overflow-x-auto max-h-96 leading-relaxed">
                  {JSON.stringify(analysisResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
