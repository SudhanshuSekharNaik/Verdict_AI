"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useCase } from "@/hooks/useCase";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageLoading } from "@/components/ui/loading";
import { formatDate, verdictColor } from "@/lib/utils";

function StructuredSection({ title, content }: { title: string; content: string }) {
  if (!content) return null;
  const sections = content.split("\n\n").filter(Boolean);
  return (
    <div className="mb-4">
      <h4 className="font-semibold text-sm text-slate-700 mb-2">{title}</h4>
      <div className="space-y-1">
        {sections.map((section, i) => (
          <p key={i} className="text-sm text-slate-600 whitespace-pre-wrap leading-relaxed">{section}</p>
        ))}
      </div>
    </div>
  );
}

export default function JudgmentPage() {
  const params = useParams();
  const caseId = params.id as string;
  const { caseData, loading } = useCase(caseId);

  if (loading) return <PageLoading />;

  const judgment = caseData?.judgment;

  const parseStructured = (text: string) => {
    const sections: Record<string, string> = {};
    const lines = text.split("\n");
    let currentKey = "";
    let currentLines: string[] = [];

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.match(/^[A-Z][A-Z\s/]+:$/) || trimmed.match(/^(ISSUE|FINDINGS|REASONING|UNRESOLVED|RELIEF|COSTS|FINAL ORDER)/i)) {
        if (currentKey) {
          sections[currentKey] = currentLines.join("\n").trim();
        }
        currentKey = trimmed.replace(/:$/, "").trim();
        currentLines = [];
      } else {
        currentLines.push(line);
      }
    }
    if (currentKey) {
      sections[currentKey] = currentLines.join("\n").trim();
    }
    return sections;
  };

  const reasoningSections = judgment?.reasoning ? parseStructured(judgment.reasoning) : {};

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <Link href={`/cases/${caseId}/courtroom`} className="text-sm text-blue-600 hover:underline">&larr; Courtroom</Link>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Judgment</h1>
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-6 py-8">
        {!judgment ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-slate-500">No judgment entered yet.</p>
              <Link href={`/cases/${caseId}/courtroom`} className="text-sm text-blue-600 hover:underline mt-2 inline-block">
                Go to Courtroom
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            <Card className="border-amber-300">
              <CardHeader className="bg-amber-50">
                <CardTitle>Verdict</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge className={verdictColor(judgment.verdict)}>{judgment.verdict.replace(/_/g, " ")}</Badge>
                <p className="text-xs text-slate-400 mt-2">{formatDate(judgment.created_at)}</p>
              </CardContent>
            </Card>

            {Object.keys(reasoningSections).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Reasoning</CardTitle>
                </CardHeader>
                <CardContent>
                  {Object.entries(reasoningSections).map(([key, value]) => (
                    <StructuredSection key={key} title={key} content={value} />
                  ))}
                </CardContent>
              </Card>
            )}

            {judgment.evidence_relied_on && judgment.evidence_relied_on.length > 0 && (
              <Card>
                <CardHeader><CardTitle>Evidence Relied Upon</CardTitle></CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {judgment.evidence_relied_on.map((ev: string, i: number) => (
                      <Badge key={i} className="bg-slate-100 text-slate-700 font-mono text-xs">{ev}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {judgment.authorities_relied_on && judgment.authorities_relied_on.length > 0 && (
              <Card>
                <CardHeader><CardTitle>Authorities Relied Upon</CardTitle></CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {judgment.authorities_relied_on.map((auth: string, i: number) => (
                      <Badge key={i} className="bg-purple-50 text-purple-700 font-mono text-xs">{auth}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {judgment.relief_awarded && !Object.keys(reasoningSections).length && (
              <Card>
                <CardHeader><CardTitle>Relief Awarded</CardTitle></CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-700 whitespace-pre-wrap">{judgment.relief_awarded}</p>
                </CardContent>
              </Card>
            )}

            {judgment.relief_awarded && Object.keys(reasoningSections).length > 0 && (
              <Card>
                <CardHeader><CardTitle>Relief / Final Order</CardTitle></CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-700 whitespace-pre-wrap">{judgment.relief_awarded}</p>
                </CardContent>
              </Card>
            )}

            <Card className="bg-amber-50 border-amber-200">
              <CardContent className="py-4">
                <p className="text-xs text-amber-700 font-medium">
                  AI ASSISTS IN PREPARING THIS DRAFT. THE FINAL JUDICIAL DECISION IS MADE EXCLUSIVELY BY THE HUMAN JUDGE.
                </p>
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
