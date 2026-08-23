export interface Case {
  id: string;
  case_number: string;
  title: string;
  description: string;
  case_type: string;
  status: string;
  jurisdiction: string;
  filing_date: string;
  parties: Party[];
  evidence_list: Evidence[];
  claims: Claim[];
  events: CaseEvent[];
  courtroom_rounds: CourtroomRound[];
  judgment: Judgment | null;
  created_at: string;
}

export interface Party {
  id: string;
  name: string;
  role: "PLAINTIFF" | "DEFENDANT";
  type: string;
}

export interface Evidence {
  id: string;
  case_id: string;
  title: string;
  evidence_type: string;
  description: string;
  extracted_text: string;
  source_url: string;
  uploaded_by: string;
  admitted: boolean;
  admitted_by_judge: boolean;
  party_owner: string;
  created_at: string;
}

export interface Claim {
  id: string;
  case_id: string;
  party_role: string;
  claim_text: string;
  legal_basis: string;
  amount_claimed: string;
}

export interface CaseEvent {
  id: string;
  case_id: string;
  event_type: string;
  title: string;
  description: string;
  event_date: string;
  party_role: string;
}

export interface Argument {
  id: string;
  case_id: string;
  round_id: string;
  agent: string;
  claim: string;
  reasoning: string;
  attack_type: string;
  confidence: number;
  evidence_ids: string[];
  citation_ids: string[];
}

export interface CourtroomRound {
  id: string;
  case_id: string;
  round_number: number;
  stage: string;
  active_speaker: string;
  summary: string;
  is_completed: boolean;
  events: CourtroomEvent[];
}

export interface CourtroomEvent {
  id: string;
  round_id: string;
  speaker: string;
  event_type: string;
  content: string;
  references: string[];
  evidence_chips?: string[];
}

export interface Judgment {
  id: string;
  case_id: string;
  verdict: string;
  relief_awarded: string;
  reasoning: string;
  evidence_relied_on: string[];
  authorities_relied_on: string[];
  judge_id: string;
  created_at: string;
}

export interface NEREntity {
  entity_group: string;
  word: string;
  score: number;
  start: number;
  end: number;
}

export interface ClassificationResult {
  label: string;
  confidence: number;
  model_version: string;
  all_scores?: Record<string, number>;
}

export interface NLIResult {
  status: string;
  confidence: number;
  all_scores: Record<string, number>;
  model_version: string;
}

export interface SearchResult {
  chunk_id: string;
  source_id: string;
  citation: string;
  title: string;
  court: string;
  year: number;
  section_type: string;
  chunk_text: string;
  vector_score: number;
  bm25_score: number;
  hybrid_score: number;
  provenance_url: string;
}

export interface LegalSource {
  id: string;
  citation: string;
  title: string;
  court: string;
  year: number;
  jurisdiction: string;
  source_type: string;
  statute_section: string;
  full_text: string;
  summary: string;
  provenance_url: string;
}

export interface AgentStep {
  round_id: string;
  round_number: number;
  stage: string;
  active_speaker: string;
  events: { speaker: string; content: string; references?: string[] }[];
}

export interface CourtIntelligenceResult {
  source: string;
  title: string;
  court: string;
  date: string;
  case_number: string;
  document_type: string;
  url: string;
}

export interface EvaluationMetrics {
  task: string;
  metrics: Record<string, number>;
  model_version: string;
  evaluated_at: string;
}

export interface MLModel {
  name: string;
  task: string;
  model_path: string;
  version: string;
  accuracy: number;
  f1_score: number;
  latency_ms: number;
}

export type CourtroomStage =
  | "CASE_OPENED"
  | "CASE_PREPARATION"
  | "EVIDENCE_SUBMISSION"
  | "OPENING_ARGUMENTS"
  | "PLAINTIFF_ARGUMENT"
  | "DEFENCE_ARGUMENT"
  | "CROSS_EXAMINATION"
  | "PLAINTIFF_REBUTTAL"
  | "DEFENCE_REBUTTAL"
  | "FINAL_SUBMISSIONS"
  | "JUDGE_QUESTIONS"
  | "JUDGE_DELIBERATION"
  | "VERDICT"
  | "CASE_CLOSED";

export const STAGE_LABELS: Record<CourtroomStage, string> = {
  CASE_OPENED: "Case Opened",
  CASE_PREPARATION: "Case Preparation",
  EVIDENCE_SUBMISSION: "Evidence Submission",
  OPENING_ARGUMENTS: "Opening Arguments",
  PLAINTIFF_ARGUMENT: "Plaintiff Argument",
  DEFENCE_ARGUMENT: "Defence Argument",
  CROSS_EXAMINATION: "Cross Examination",
  PLAINTIFF_REBUTTAL: "Plaintiff Rebuttal",
  DEFENCE_REBUTTAL: "Defence Rebuttal",
  FINAL_SUBMISSIONS: "Final Submissions",
  JUDGE_QUESTIONS: "Judge Questions",
  JUDGE_DELIBERATION: "Judge Deliberation",
  VERDICT: "Verdict",
  CASE_CLOSED: "Case Closed",
};

export const STAGE_ORDER: CourtroomStage[] = [
  "CASE_OPENED",
  "CASE_PREPARATION",
  "EVIDENCE_SUBMISSION",
  "OPENING_ARGUMENTS",
  "PLAINTIFF_ARGUMENT",
  "DEFENCE_ARGUMENT",
  "CROSS_EXAMINATION",
  "PLAINTIFF_REBUTTAL",
  "DEFENCE_REBUTTAL",
  "FINAL_SUBMISSIONS",
  "JUDGE_QUESTIONS",
  "JUDGE_DELIBERATION",
  "VERDICT",
  "CASE_CLOSED",
];

export interface HearingMessage {
  id: string;
  turn_id: string;
  stage: string;
  side: "PLAINTIFF" | "DEFENCE" | "JUDGE" | "SYSTEM";
  message_type: string;
  content_json: HearingArgument | JudgeAnalysis;
  evidence_refs: string[];
  authority_refs: string[];
  authority_verification?: AuthorityVerificationReport;
  parent_turn_id: string | null;
  created_at: string | null;
}

export interface AuthorityVerificationReport {
  total_candidate: number;
  verified_count: number;
  rejected_count: number;
  partially_count: number;
  rejected: Array<{
    citation: string;
    reason: string;
    steps?: Array<{ step: string; status: string; detail: string }>;
  }>;
}

export interface HearingArgument {
  side: string;
  stage: string;
  position: string;
  issues: Array<{ issue: string; position: string }>;
  argument: {
    claim: string;
    legal_rule: string;
    material_facts: string[];
    application: string;
    counterargument: string;
    rebuttal: string;
    requested_relief: string;
  };
  evidence_references: Array<{ id: string; reason: string }>;
  authority_references: Array<{
    id?: string;
    citation: string;
    case_name?: string;
    court?: string;
    year?: number;
    reason: string;
    verification_status?: string;
    verification_steps?: Array<{ step: string; status: string; detail: string }>;
  }>;
  evidence_count: number;
  authority_count: number;
  confidence: {
    evidence_support: number;
    legal_authority_support: number;
    argument_consistency: number;
    overall: number;
  };
  authority_verification?: AuthorityVerificationReport;
}

export interface JudgeAnalysis {
  issues: Array<{ issue: string; analysis: string }>;
  facts_found: string[];
  facts_disputed: string[];
  law: string[];
  plaintiff_strengths: string[];
  defence_strengths: string[];
  evidence_conflicts: Array<string | { description: string; court_question: string }>;
  unresolved_questions: string[];
  analysis: string[];
  provisional_findings: string[];
  recommended_next_questions: string[];
}
