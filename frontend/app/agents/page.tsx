"use client";

import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const agents = [
  { name: "Plaintiff Agent", icon: "🔴", role: "PLAINTIFF_AGENT", description: "Constructs evidence-grounded arguments for the plaintiff. Links claims to admitted evidence and cites legal authorities." },
  { name: "Defence Agent", icon: "🔵", role: "DEFENCE_AGENT", description: "Challenges the plaintiff's case. Searches for unsupported claims, contradictory evidence, and missing proof." },
  { name: "Research Agent", icon: "📚", role: "RESEARCH", description: "Hybrid retrieval of legal authorities using BM25 + dense vector search with cross-encoder reranking." },
  { name: "Evidence Agent", icon: "📂", role: "EVIDENCE", description: "Processes uploaded evidence. Segregates by party, verifies admissibility, extracts text and metadata." },
  { name: "Validation Agent", icon: "✅", role: "VALIDATION", description: "Grounds every claim against evidence using NLI. Verifies citations against the legal corpus." },
  { name: "Judge Assistant", icon: "📋", role: "JUDGE_ASSISTANT", description: "Prepares bench briefs. Identifies contradictions, timeline conflicts, and suggests questions for the bench." },
  { name: "Case Intake Agent", icon: "📝", role: "INTAKE", description: "Extracts parties, claims, amounts, dates from case narratives using NER and regex patterns." },
];

export default function AgentsPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">&larr; Dashboard</Link>
          <h1 className="text-xl font-bold text-slate-900 mt-1">AI Agents</h1>
          <p className="text-sm text-slate-500">7 specialized agents powering the courtroom simulation</p>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {agents.map((a) => (
            <Card key={a.role} className="hover:shadow-md transition-shadow">
              <CardContent className="py-5">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{a.icon}</span>
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-900">{a.name}</h3>
                    <Badge variant="info" className="mt-1">{a.role}</Badge>
                    <p className="text-sm text-slate-600 mt-2">{a.description}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="mt-8">
          <CardHeader><CardTitle>Courtroom Flow</CardTitle></CardHeader>
          <CardContent>
            <div className="text-sm text-slate-700 space-y-2">
              <p><strong>1.</strong> Case Intake → Extract parties, claims, evidence</p>
              <p><strong>2.</strong> Evidence Submission → Upload and admit evidence</p>
              <p><strong>3.</strong> Opening Arguments → Plaintiff and Defence</p>
              <p><strong>4.</strong> Attack Rounds → Adversarial argumentation</p>
              <p><strong>5.</strong> Cross Examination → Challenge credibility</p>
              <p><strong>6.</strong> Rebuttal → Final responses</p>
              <p><strong>7.</strong> Judge Questions → Human judge queries agents</p>
              <p><strong>8.</strong> Final Submissions → Closing arguments</p>
              <p><strong>9.</strong> Deliberation → Judge enters judgment</p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
