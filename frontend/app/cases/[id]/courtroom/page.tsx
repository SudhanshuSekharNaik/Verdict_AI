"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useState, useEffect, useRef, useCallback } from "react";
import { useCase } from "@/hooks/useCase";
import { PageLoading } from "@/components/ui/loading";
import { api } from "@/lib/api";
import type { HearingMessage, HearingArgument, JudgeAnalysis } from "@/types";

const STAGE_LABELS: Record<string, string> = {
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

const STAGE_ORDER = [
  "CASE_OPENED", "CASE_PREPARATION", "EVIDENCE_SUBMISSION",
  "OPENING_ARGUMENTS", "PLAINTIFF_ARGUMENT", "DEFENCE_ARGUMENT",
  "CROSS_EXAMINATION", "PLAINTIFF_REBUTTAL", "DEFENCE_REBUTTAL",
  "FINAL_SUBMISSIONS", "JUDGE_QUESTIONS", "JUDGE_DELIBERATION",
  "VERDICT", "CASE_CLOSED",
];

function EvidenceChip({ label, caseId }: { label: string; caseId?: string }) {
  const isP = label.startsWith("P-");
  const isD = label.startsWith("D-");
  const base = isP ? "bg-red-950/50 text-red-300 border-red-800/50 hover:bg-red-900/50" : "bg-blue-950/50 text-blue-300 border-blue-800/50 hover:bg-blue-900/50";
  if (caseId && (isP || isD)) {
    return (
      <Link href={`/cases/${caseId}/evidence`} className={`text-xs px-2 py-0.5 rounded border font-mono transition-colors ${base}`} title={label}>
        {label}
      </Link>
    );
  }
  return <span className={`text-xs px-2 py-0.5 rounded border font-mono ${isP ? "bg-red-950/50 text-red-300 border-red-800/50" : "bg-blue-950/50 text-blue-300 border-blue-800/50"}`}>{label}</span>;
}

function ConfidenceBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-slate-400 w-16">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-slate-300 w-10 text-right">{pct}%</span>
    </div>
  );
}

function ArgumentMessage({ msg, caseId, side }: { msg: HearingMessage; caseId: string; side: "PLAINTIFF" | "DEFENCE" }) {
  const arg = msg.content_json as HearingArgument;
  const isPlaintiff = side === "PLAINTIFF";
  const borderColor = isPlaintiff ? "border-red-800/40" : "border-blue-800/40";
  const bgColor = isPlaintiff ? "bg-red-950/20" : "bg-blue-950/20";
  const accentColor = isPlaintiff ? "text-red-400" : "text-blue-400";
  const dotColor = isPlaintiff ? "bg-red-500" : "bg-blue-500";

  return (
    <div className={`border ${borderColor} ${bgColor} rounded-xl p-4 mb-3 animate-fade-in-up`}>
      <div className="flex items-center gap-2 mb-3">
        <span className={`w-2 h-2 rounded-full ${dotColor}`} />
        <span className={`text-xs font-semibold uppercase tracking-wider ${accentColor}`}>
          {arg.stage?.replace(/_/g, " ")}
        </span>
      </div>

      {arg.position && (
        <p className="text-sm text-slate-200 font-medium mb-3 leading-relaxed">{arg.position}</p>
      )}

      {arg.argument?.claim && (
        <div className="mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Claim</span>
          <p className="text-sm text-slate-300 mt-1 leading-relaxed">{arg.argument.claim}</p>
        </div>
      )}

      {arg.argument?.legal_rule && (
        <div className="mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Legal Rule</span>
          <p className="text-sm text-slate-300 mt-1 leading-relaxed">{arg.argument.legal_rule}</p>
        </div>
      )}

      {arg.argument?.material_facts?.length > 0 && (
        <div className="mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Material Facts</span>
          <ul className="mt-1 space-y-1">
            {arg.argument.material_facts.map((fact, i) => (
              <li key={i} className="text-sm text-slate-300 pl-3 relative before:content-[''] before:absolute before:left-0 before:top-2 before:w-1 before:h-1 before:rounded-full before:bg-slate-600">
                {fact}
              </li>
            ))}
          </ul>
        </div>
      )}

      {arg.argument?.application && (
        <div className="mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Application</span>
          <p className="text-sm text-slate-300 mt-1 leading-relaxed">{arg.argument.application}</p>
        </div>
      )}

      {arg.evidence_references?.length > 0 && (
        <div className="mb-3 pt-3 border-t border-slate-700/30">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">Evidence</span>
          <div className="flex flex-wrap gap-1.5">
            {arg.evidence_references.map((ref, i) => (
              <div key={i} className="flex items-center gap-1">
                <EvidenceChip label={ref.id} caseId={caseId} />
                <span className="text-xs text-slate-500 hidden sm:inline">: {ref.reason?.slice(0, 60)}...</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {arg.authority_references?.length > 0 && (
        <div className="mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
            Verified Authorities ({arg.authority_references.length})
          </span>
          <div className="space-y-2">
            {arg.authority_references.map((ref, i) => (
              <div key={i} className="bg-slate-800/30 rounded-lg p-2 border border-slate-700/30">
                <div className="flex items-center gap-2">
                  {ref.verification_status === "VERIFIED" && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-900/50 text-emerald-400 border border-emerald-800/30">✓ VERIFIED</span>
                  )}
                  {ref.verification_status === "PARTIALLY_SUPPORTED" && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-yellow-900/50 text-yellow-400 border border-yellow-800/30">Partial</span>
                  )}
                  {ref.verification_status === "REJECTED" && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-900/50 text-red-400 border border-red-800/30">✗ REJECTED</span>
                  )}
                  {ref.verification_status === "UNVERIFIED" && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800/50 text-slate-400 border border-slate-700/30">Unverified</span>
                  )}
                </div>
                <p className="text-xs font-mono text-amber-300 mt-1">{ref.citation}</p>
                {ref.case_name && (
                  <p className="text-[10px] text-slate-400 mt-0.5">{ref.case_name}</p>
                )}
                {ref.court && ref.year && (
                  <p className="text-[10px] text-slate-500">{ref.court} · {ref.year}</p>
                )}
                {ref.reason && (
                  <p className="text-[10px] text-slate-400 mt-1 italic">{ref.reason?.slice(0, 200)}</p>
                )}
                {ref.verification_steps && ref.verification_steps.length > 0 && (
                  <div className="mt-1.5 space-y-0.5">
                    {ref.verification_steps.map((step, j) => (
                      <div key={j} className="flex items-center gap-1.5 text-[9px]">
                        <span className={step.status === "PASS" ? "text-emerald-500" : step.status === "FAIL" ? "text-red-500" : "text-yellow-500"}>
                          {step.status === "PASS" ? "✓" : step.status === "FAIL" ? "✗" : "◐"}
                        </span>
                        <span className="text-slate-500">{step.detail?.slice(0, 100)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {arg.authority_verification && (arg.authority_verification.rejected_count > 0 || arg.authority_verification.total_candidate > 0) && (
        <div className="mb-3 bg-slate-800/20 border border-slate-700/20 rounded-lg p-2">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Verification Report
          </span>
          <div className="flex gap-3 mt-1 text-[10px]">
            <span className="text-slate-500">Candidates: {arg.authority_verification.total_candidate}</span>
            <span className="text-emerald-400">Verified: {arg.authority_verification.verified_count}</span>
            {arg.authority_verification.rejected_count > 0 && (
              <span className="text-red-400">Rejected: {arg.authority_verification.rejected_count}</span>
            )}
            {arg.authority_verification.partially_count > 0 && (
              <span className="text-yellow-400">Partial: {arg.authority_verification.partially_count}</span>
            )}
          </div>
          {arg.authority_verification.rejected?.map((rej, i) => (
            <div key={i} className="mt-1.5 bg-red-950/20 border border-red-800/15 rounded p-1.5">
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] px-1 py-0.5 rounded bg-red-900/30 text-red-400">✗ REJECTED</span>
                <span className="text-[10px] font-mono text-red-300">{rej.citation}</span>
              </div>
              <p className="text-[9px] text-red-400/70 mt-0.5">{rej.reason?.slice(0, 150)}</p>
              {rej.steps && (
                <div className="mt-1 space-y-0.5">
                  {rej.steps.map((step, j) => (
                    <div key={j} className="flex items-center gap-1.5 text-[9px]">
                      <span className={step.status === "PASS" ? "text-emerald-500" : step.status === "FAIL" ? "text-red-500" : "text-yellow-500"}>
                        {step.status === "PASS" ? "✓" : step.status === "FAIL" ? "✗" : "◐"}
                      </span>
                      <span className="text-slate-500">{step.detail?.slice(0, 100)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {arg.authority_references?.length === 0 && (
        <div className="mb-3 bg-slate-800/30 border border-slate-700/20 rounded-lg p-2">
          <span className="text-[10px] text-slate-500 italic">No verified authorities — all candidates rejected by verification pipeline</span>
        </div>
      )}

      {arg.confidence && (
        <div className="pt-3 border-t border-slate-700/30 space-y-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Backend-Computed Confidence</span>
          <ConfidenceBar label="Evidence" value={arg.confidence.evidence_support} color={isPlaintiff ? "bg-red-500" : "bg-blue-500"} />
          <ConfidenceBar label="Legal Auth" value={arg.confidence.legal_authority_support} color={isPlaintiff ? "bg-red-400" : "bg-blue-400"} />
          <ConfidenceBar label="Consistency" value={arg.confidence.argument_consistency} color={isPlaintiff ? "bg-red-300" : "bg-blue-300"} />
          <div className="pt-1 border-t border-slate-700/20">
            <ConfidenceBar label="Overall" value={arg.confidence.overall} color="bg-amber-500" />
          </div>
        </div>
      )}
    </div>
  );
}

function JudgeAnalysisMessage({ msg }: { msg: HearingMessage }) {
  const analysis = msg.content_json as JudgeAnalysis;
  return (
    <div className="border border-amber-800/40 bg-amber-950/20 rounded-xl p-4 animate-fade-in-up">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-amber-500">⚖</span>
        <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Judge Analysis</span>
      </div>

      {analysis.issues?.length > 0 && (
        <div className="mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Issues</span>
          <div className="space-y-2 mt-1">
            {analysis.issues.map((item, i) => (
              <div key={i} className="text-sm">
                <span className="text-amber-300 font-medium">{i + 1}. {item.issue}</span>
                <p className="text-slate-400 mt-0.5 pl-4">{item.analysis}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {analysis.plaintiff_strengths?.length > 0 && (
        <div className="mb-3">
          <span className="text-xs font-semibold text-red-400 uppercase tracking-wider">Plaintiff Strengths</span>
          <ul className="mt-1 space-y-1">
            {analysis.plaintiff_strengths.map((s, i) => (
              <li key={i} className="text-sm text-slate-300 pl-3 relative before:content-[''] before:absolute before:left-0 before:top-2 before:w-1 before:h-1 before:rounded-full before:bg-red-500">{s}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis.defence_strengths?.length > 0 && (
        <div className="mb-3">
          <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">Defence Strengths</span>
          <ul className="mt-1 space-y-1">
            {analysis.defence_strengths.map((s, i) => (
              <li key={i} className="text-sm text-slate-300 pl-3 relative before:content-[''] before:absolute before:left-0 before:top-2 before:w-1 before:h-1 before:rounded-full before:bg-blue-500">{s}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis.evidence_conflicts?.length > 0 && (
        <div className="mb-3 pt-3 border-t border-amber-800/30">
          <span className="text-xs font-semibold text-orange-400 uppercase tracking-wider">Evidence Conflicts</span>
          <div className="mt-1 space-y-2">
            {analysis.evidence_conflicts.map((c, i) => {
              if (typeof c === 'string') {
                return <li key={i} className="text-sm text-orange-300 pl-3">{c}</li>;
              }
              return (
                <div key={i} className="bg-orange-950/20 border border-orange-800/20 rounded-lg p-2">
                  <p className="text-sm text-orange-300">{c.description}</p>
                  {c.court_question && (
                    <div className="mt-1.5 pl-3 border-l-2 border-amber-600/40">
                      <span className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider">Court Question</span>
                      <p className="text-xs text-amber-300 mt-0.5">{c.court_question}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {analysis.unresolved_questions?.length > 0 && (
        <div className="mb-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Unresolved</span>
          <ul className="mt-1 space-y-1">
            {analysis.unresolved_questions.map((q, i) => (
              <li key={i} className="text-sm text-slate-400 pl-3">{q}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis.provisional_findings?.length > 0 && (
        <div className="mb-3 pt-3 border-t border-amber-800/30">
          <span className="text-xs font-semibold text-amber-300 uppercase tracking-wider">Provisional Findings</span>
          <ul className="mt-1 space-y-1">
            {analysis.provisional_findings.map((f, i) => (
              <li key={i} className="text-sm text-slate-300 pl-3">{f}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ThinkingIndicator({ side }: { side: "PLAINTIFF" | "DEFENCE" | "JUDGE" }) {
  const color = side === "PLAINTIFF" ? "text-red-400" : side === "DEFENCE" ? "text-blue-400" : "text-amber-400";
  const dotColor = side === "PLAINTIFF" ? "bg-red-400" : side === "DEFENCE" ? "bg-blue-400" : "bg-amber-400";
  const label = side === "PLAINTIFF" ? "Plaintiff AI" : side === "DEFENCE" ? "Defence AI" : "Judge AI";

  return (
    <div className={`border border-slate-700/30 rounded-xl p-4 mb-3 ${side === "PLAINTIFF" ? "bg-red-950/10" : side === "DEFENCE" ? "bg-blue-950/10" : "bg-amber-950/10"}`}>
      <div className="flex items-center gap-3">
        <div className="flex gap-1">
          <span className={`w-2 h-2 rounded-full ${dotColor} thinking-dot`} />
          <span className={`w-2 h-2 rounded-full ${dotColor} thinking-dot`} />
          <span className={`w-2 h-2 rounded-full ${dotColor} thinking-dot`} />
        </div>
        <span className={`text-sm font-medium ${color}`}>{label} is analyzing...</span>
      </div>
    </div>
  );
}

function HearingProgress({ currentStage, messages }: { currentStage: string; messages: HearingMessage[] }) {
  const currentIdx = STAGE_ORDER.indexOf(currentStage);

  const completedStages = new Set(messages.map(m => m.stage));

  return (
    <div className="space-y-1">
      {STAGE_ORDER.filter(s => !["CASE_OPENED", "CASE_PREPARATION", "EVIDENCE_SUBMISSION", "CASE_CLOSED"].includes(s)).map((stage, idx) => {
        const isCompleted = completedStages.has(stage);
        const isActive = stage === currentStage;
        const label = STAGE_LABELS[stage] || stage;

        return (
          <div
            key={stage}
            className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
              isActive ? "bg-slate-800 text-white font-medium" :
              isCompleted ? "text-emerald-400/80" : "text-slate-600"
            }`}
          >
            <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
              isCompleted ? "bg-emerald-600 text-white" :
              isActive ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-500"
            }`}>
              {isCompleted ? "✓" : ""}
            </span>
            <span className="truncate">{label}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function CourtroomPage() {
  const params = useParams();
  const caseId = params.id as string;
  const { caseData, loading: caseLoading } = useCase(caseId);

  const [messages, setMessages] = useState<HearingMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(true);
  const [generatingSide, setGeneratingSide] = useState<"PLAINTIFF" | "DEFENCE" | "JUDGE" | null>(null);
  const [instruction, setInstruction] = useState("");
  const [currentStage, setCurrentStage] = useState("OPENING_ARGUMENTS");
  const [error, setError] = useState<string | null>(null);

  const plaintiffScrollRef = useRef<HTMLDivElement>(null);
  const defenceScrollRef = useRef<HTMLDivElement>(null);

  const loadMessages = useCallback(async () => {
    try {
      setLoadingMessages(true);
      const data = await api.getHearingMessages(caseId);
      const msgs = data?.messages || [];
      setMessages(msgs);

      if (msgs.length > 0) {
        const stages = msgs.map((m: HearingMessage) => m.stage);
        const lastStage = stages[stages.length - 1];
        const lastIdx = STAGE_ORDER.indexOf(lastStage);
        if (lastIdx < STAGE_ORDER.length - 1) {
          setCurrentStage(STAGE_ORDER[lastIdx + 1]);
        }
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoadingMessages(false);
    }
  }, [caseId]);

  useEffect(() => { loadMessages(); }, [loadMessages]);

  useEffect(() => {
    if (plaintiffScrollRef.current) {
      plaintiffScrollRef.current.scrollTop = plaintiffScrollRef.current.scrollHeight;
    }
    if (defenceScrollRef.current) {
      defenceScrollRef.current.scrollTop = defenceScrollRef.current.scrollHeight;
    }
  }, [messages, generatingSide]);

  const plaintiffMessages = messages.filter(m => m.side === "PLAINTIFF");
  const defenceMessages = messages.filter(m => m.side === "DEFENCE");
  const judgeMessages = messages.filter(m => m.side === "JUDGE");

  const generate = async (side: "PLAINTIFF" | "DEFENCE") => {
    try {
      setGeneratingSide(side);
      setError(null);

      const result = await api.generateHearingMessage(caseId, {
        side,
        stage: currentStage,
        instruction: instruction || undefined,
      });

      setMessages(prev => [...prev, {
        id: result.id,
        turn_id: result.turn_id,
        stage: result.stage,
        side: result.side,
        message_type: result.message_type,
        content_json: result.content_json,
        evidence_refs: result.evidence_refs || [],
        authority_refs: result.authority_refs || [],
        parent_turn_id: null,
        created_at: new Date().toISOString(),
      }]);

      setInstruction("");
    } catch (e: any) {
      setError(`${side} AI generation failed: ${e.message}`);
    } finally {
      setGeneratingSide(null);
    }
  };

  const runJudgeAnalysis = async () => {
    try {
      setGeneratingSide("JUDGE");
      setError(null);

      const result = await api.judgeAnalysis(caseId);

      setMessages(prev => [...prev, {
        id: result.id,
        turn_id: result.turn_id,
        stage: result.stage,
        side: "JUDGE",
        message_type: "RULING",
        content_json: result.content_json,
        evidence_refs: [],
        authority_refs: [],
        parent_turn_id: null,
        created_at: new Date().toISOString(),
      }]);
    } catch (e: any) {
      setError(`Judge analysis failed: ${e.message}`);
    } finally {
      setGeneratingSide(null);
    }
  };

  if (caseLoading) return <PageLoading />;
  if (!caseData) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">Case not found</div>;

  return (
    <div className="h-screen flex flex-col bg-slate-950 text-slate-200">
      <header className="bg-slate-900 border-b border-slate-800 px-4 py-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-sm text-slate-400 hover:text-white transition-colors">
              ← Dashboard
            </Link>
            <div>
              <h1 className="text-lg font-bold text-white">{caseData.title}</h1>
              <p className="text-xs text-slate-500">{caseData.case_number}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href={`/cases/${caseId}/evidence`} className="text-xs text-slate-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-slate-800">Evidence</Link>
            <Link href={`/cases/${caseId}/timeline`} className="text-xs text-slate-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-slate-800">Timeline</Link>
            <Link href={`/cases/${caseId}/research`} className="text-xs text-slate-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-slate-800">Research</Link>
            <Link href={`/cases/${caseId}/judgment`} className="text-xs text-slate-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-slate-800">Judgment</Link>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-amber-950/50 text-amber-400 border border-amber-800/30">
              {STAGE_LABELS[currentStage as keyof typeof STAGE_LABELS] || currentStage}
            </span>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-52 flex-shrink-0 bg-slate-900/50 border-r border-slate-800 p-3 overflow-y-auto scrollbar-thin hidden lg:block">
          <h2 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-3">Hearing Progress</h2>
          <HearingProgress currentStage={currentStage} messages={messages} />
        </aside>

        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
          <div className="flex-1 flex flex-col min-w-0 border-r border-slate-800/50">
            <div className="px-4 py-3 border-b border-slate-800/50 bg-red-950/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
                <span className="text-sm font-bold text-red-400">PLAINTIFF AI</span>
              </div>
              <span className="text-[10px] text-slate-500">{plaintiffMessages.length} argument{plaintiffMessages.length !== 1 ? "s" : ""}</span>
            </div>
            <div ref={plaintiffScrollRef} className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-thin">
              {plaintiffMessages.length === 0 && !generatingSide && (
                <div className="flex items-center justify-center h-full text-slate-600 text-sm">
                  Click "Generate Plaintiff Argument" to begin
                </div>
              )}
              {plaintiffMessages.map(msg => (
                <ArgumentMessage key={msg.id} msg={msg} caseId={caseId} side="PLAINTIFF" />
              ))}
              {generatingSide === "PLAINTIFF" && <ThinkingIndicator side="PLAINTIFF" />}
            </div>
          </div>

          <div className="w-full lg:w-72 flex-shrink-0 flex flex-col bg-slate-900/30 border-r border-slate-800/50">
            <div className="px-4 py-3 border-b border-slate-800/50 flex items-center justify-center gap-2">
              <span className="text-amber-500">⚖</span>
              <span className="text-sm font-bold text-amber-400">COURT</span>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin">
              <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/30">
                <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Current Stage</span>
                <p className="text-sm text-white mt-1">{STAGE_LABELS[currentStage as keyof typeof STAGE_LABELS] || currentStage}</p>
              </div>

              <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/30">
                <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Status</span>
                <div className="mt-1 space-y-1">
                  <div className="flex items-center gap-2 text-xs">
                    <span className={`w-1.5 h-1.5 rounded-full ${plaintiffMessages.length > 0 ? "bg-emerald-500" : "bg-slate-600"}`} />
                    <span className={plaintiffMessages.length > 0 ? "text-emerald-400" : "text-slate-500"}>Plaintiff submitted</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className={`w-1.5 h-1.5 rounded-full ${defenceMessages.length > 0 ? "bg-emerald-500" : "bg-slate-600"}`} />
                    <span className={defenceMessages.length > 0 ? "text-emerald-400" : "text-slate-500"}>Defence submitted</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className={`w-1.5 h-1.5 rounded-full ${judgeMessages.length > 0 ? "bg-emerald-500" : "bg-slate-600"}`} />
                    <span className={judgeMessages.length > 0 ? "text-emerald-400" : "text-slate-500"}>Judge analyzed</span>
                  </div>
                </div>
              </div>

              {judgeMessages.length > 0 && (
                <div className="bg-amber-950/20 rounded-lg p-3 border border-amber-800/30">
                  <span className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider">Judge Analysis</span>
                  <div className="mt-2 space-y-1">
                    {(judgeMessages[judgeMessages.length - 1].content_json as JudgeAnalysis)?.plaintiff_strengths?.length > 0 && (
                      <p className="text-[10px] text-slate-400">Plaintiff strengths identified</p>
                    )}
                    {(judgeMessages[judgeMessages.length - 1].content_json as JudgeAnalysis)?.defence_strengths?.length > 0 && (
                      <p className="text-[10px] text-slate-400">Defence strengths identified</p>
                    )}
                  </div>
                </div>
              )}

              <button
                onClick={runJudgeAnalysis}
                disabled={generatingSide !== null || messages.length < 2}
                className="w-full text-xs px-3 py-2 rounded-lg bg-amber-900/50 text-amber-300 border border-amber-800/30 hover:bg-amber-800/50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Run Judge Analysis
              </button>
            </div>

            {error && (
              <div className="px-4 py-3 border-t border-slate-800/50 bg-red-950/20">
                <p className="text-xs text-red-400">{error}</p>
              </div>
            )}

            <div className="px-3 py-3 border-t border-slate-800/50 bg-slate-800/30">
              <textarea
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                placeholder="Court instruction / issue to address..."
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-600 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                rows={2}
              />
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => generate("PLAINTIFF")}
                  disabled={generatingSide !== null}
                  className="flex-1 text-xs px-3 py-2 rounded-lg bg-red-900/50 text-red-300 border border-red-800/30 hover:bg-red-800/50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Generate Plaintiff
                </button>
                <button
                  onClick={() => generate("DEFENCE")}
                  disabled={generatingSide !== null}
                  className="flex-1 text-xs px-3 py-2 rounded-lg bg-blue-900/50 text-blue-300 border border-blue-800/30 hover:bg-blue-800/50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Generate Defence
                </button>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col min-w-0">
            <div className="px-4 py-3 border-b border-slate-800/50 bg-blue-950/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                <span className="text-sm font-bold text-blue-400">DEFENCE AI</span>
              </div>
              <span className="text-[10px] text-slate-500">{defenceMessages.length} argument{defenceMessages.length !== 1 ? "s" : ""}</span>
            </div>
            <div ref={defenceScrollRef} className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-thin">
              {defenceMessages.length === 0 && !generatingSide && (
                <div className="flex items-center justify-center h-full text-slate-600 text-sm">
                  Click "Generate Defence Argument" to respond
                </div>
              )}
              {defenceMessages.map(msg => (
                <ArgumentMessage key={msg.id} msg={msg} caseId={caseId} side="DEFENCE" />
              ))}
              {generatingSide === "DEFENCE" && <ThinkingIndicator side="DEFENCE" />}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
