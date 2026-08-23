"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

interface Props {
  caseId: string;
  onComplete: () => void;
}

export function JudgePanel({ caseId, onComplete }: Props) {
  const [question, setQuestion] = useState("");
  const [targetAgent, setTargetAgent] = useState("PLAINTIFF_AI");
  const [responses, setResponses] = useState<{ q: string; a: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const [verdict, setVerdict] = useState("PLAINTIFF_SUCCEEDS");
  const [issues, setIssues] = useState("");
  const [findingsFact, setFindingsFact] = useState("");
  const [findingsLaw, setFindingsLaw] = useState("");
  const [evidenceRelied, setEvidenceRelied] = useState("");
  const [authoritiesRelied, setAuthoritiesRelied] = useState("");
  const [reasoning, setReasoning] = useState("");
  const [relief, setRelief] = useState("");
  const [costs, setCosts] = useState("");
  const [finalOrder, setFinalOrder] = useState("");
  const [legalConfidence, setLegalConfidence] = useState("85");
  const [evidenceConfidence, setEvidenceConfidence] = useState("80");
  const [unresolved, setUnresolved] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const askQuestion = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const result = await api.askJudgeQuestion(caseId, targetAgent, question);
      setResponses((prev) => [...prev, { q: question, a: result.answer || "" }]);
      setQuestion("");
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const submitJudgment = async () => {
    if (!reasoning.trim()) return;
    setSubmitting(true);
    try {
      const evidenceItems = evidenceRelied.split("\n").filter((l) => l.trim());
      const authorityItems = authoritiesRelied.split("\n").filter((l) => l.trim());

      const fullReasoning = [
        "ISSUES FOR DETERMINATION:",
        issues || "Not specified.",
        "",
        "FINDINGS OF FACT:",
        findingsFact || "Not specified.",
        "",
        "FINDINGS OF LAW:",
        findingsLaw || "Not specified.",
        "",
        "REASONING:",
        reasoning,
        "",
        "UNRESOLVED ISSUES:",
        unresolved || "None.",
      ].join("\n");

      const fullRelief = [
        relief ? `RELIEF: ${relief}` : "",
        costs ? `COSTS: ${costs}` : "",
        finalOrder ? `FINAL ORDER: ${finalOrder}` : "",
      ]
        .filter(Boolean)
        .join("\n");

      await api.enterJudgment(caseId, {
        verdict,
        relief_awarded: fullRelief,
        reasoning: fullReasoning,
        evidence_relied_on: evidenceItems,
        authorities_relied_on: authorityItems,
      });
      onComplete();
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Judge Questioning</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-3">
            <select value={targetAgent} onChange={(e) => setTargetAgent(e.target.value)} className="input w-48">
              <option value="PLAINTIFF_AI">Plaintiff Agent</option>
              <option value="DEFENCE_AI">Defence Agent</option>
            </select>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question to the agent..."
              className="input flex-1"
              onKeyDown={(e) => e.key === "Enter" && askQuestion()}
            />
            <Button onClick={askQuestion} loading={loading}>Ask</Button>
          </div>
          {responses.length > 0 && (
            <div className="space-y-3 mt-4">
              {responses.map((r, i) => (
                <div key={i} className="border rounded-lg p-3 bg-slate-50">
                  <p className="text-sm font-medium text-amber-700">Q: {r.q}</p>
                  <p className="text-sm mt-1 text-slate-700">{r.a}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-amber-300">
        <CardHeader className="bg-amber-50">
          <CardTitle>Enter Judgment</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Verdict</label>
            <select value={verdict} onChange={(e) => setVerdict(e.target.value)} className="input">
              <option value="PLAINTIFF_SUCCEEDS">Plaintiff Succeeds</option>
              <option value="DEFENDANT_SUCCEEDS">Defendant Succeeds</option>
              <option value="PARTIALLY_SUCCEEDS">Partial Relief</option>
              <option value="INSUFFICIENT_EVIDENCE">Dismissed</option>
            </select>
          </div>

          <div className="border rounded-lg p-4 bg-slate-50 space-y-3">
            <h4 className="font-semibold text-sm text-slate-700">Issues for Determination</h4>
            <textarea
              value={issues}
              onChange={(e) => setIssues(e.target.value)}
              className="input"
              rows={3}
              placeholder={"1. Whether the defendant breached the agreement?\n2. Whether damages are recoverable?\n3. What relief should be granted?"}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="border rounded-lg p-4 bg-slate-50 space-y-3">
              <h4 className="font-semibold text-sm text-slate-700">Findings of Fact</h4>
              <textarea
                value={findingsFact}
                onChange={(e) => setFindingsFact(e.target.value)}
                className="input"
                rows={4}
                placeholder="State findings of fact..."
              />
            </div>
            <div className="border rounded-lg p-4 bg-slate-50 space-y-3">
              <h4 className="font-semibold text-sm text-slate-700">Findings of Law</h4>
              <textarea
                value={findingsLaw}
                onChange={(e) => setFindingsLaw(e.target.value)}
                className="input"
                rows={4}
                placeholder="State findings of law..."
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Evidence Relied Upon</label>
              <textarea
                value={evidenceRelied}
                onChange={(e) => setEvidenceRelied(e.target.value)}
                className="input"
                rows={3}
                placeholder={"P-001\nP-002\nD-001"}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Authorities Relied Upon</label>
              <textarea
                value={authoritiesRelied}
                onChange={(e) => setAuthoritiesRelied(e.target.value)}
                className="input"
                rows={3}
                placeholder={"(2021) 8 SCC 342\nSection 73, Indian Contract Act"}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Reasoning</label>
            <textarea
              value={reasoning}
              onChange={(e) => setReasoning(e.target.value)}
              className="input"
              rows={5}
              placeholder="State your detailed reasoning..."
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Relief / Remedy</label>
              <textarea
                value={relief}
                onChange={(e) => setRelief(e.target.value)}
                className="input"
                rows={2}
                placeholder="Describe relief awarded..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Costs</label>
              <textarea
                value={costs}
                onChange={(e) => setCosts(e.target.value)}
                className="input"
                rows={2}
                placeholder="Costs awarded..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Final Order</label>
              <textarea
                value={finalOrder}
                onChange={(e) => setFinalOrder(e.target.value)}
                className="input"
                rows={2}
                placeholder="Final directive..."
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Legal Confidence (%)</label>
              <input
                type="number"
                value={legalConfidence}
                onChange={(e) => setLegalConfidence(e.target.value)}
                className="input"
                min={0}
                max={100}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Evidence Confidence (%)</label>
              <input
                type="number"
                value={evidenceConfidence}
                onChange={(e) => setEvidenceConfidence(e.target.value)}
                className="input"
                min={0}
                max={100}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Unresolved Issues</label>
            <textarea
              value={unresolved}
              onChange={(e) => setUnresolved(e.target.value)}
              className="input"
              rows={2}
              placeholder="Any remaining unresolved issues..."
            />
          </div>

          <div className="p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-700">
            AI ASSISTS IN PREPARING THIS DRAFT. THE FINAL JUDICIAL DECISION IS MADE EXCLUSIVELY BY THE HUMAN JUDGE.
          </div>

          <Button onClick={submitJudgment} loading={submitting} variant="primary" className="w-full">
            Submit Judgment
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
