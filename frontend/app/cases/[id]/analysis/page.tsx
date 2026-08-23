"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { useCase } from "@/hooks/useCase";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageLoading } from "@/components/ui/loading";
import { api } from "@/lib/api";

export default function AnalysisPage() {
  const params = useParams();
  const caseId = params.id as string;
  const { caseData, loading } = useCase(caseId);
  const [nerResult, setNerResult] = useState<any[]>([]);
  const [clfResult, setClfResult] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const analyze = async () => {
    if (!caseData?.description) return;
    setAnalyzing(true);
    try {
      const [ner, clf] = await Promise.all([
        api.runNER(caseData.description),
        api.classifyCase(caseData.description),
      ]);
      setNerResult(ner);
      setClfResult(clf);
    } catch (e) {
      console.error(e);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <PageLoading />;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <Link href={`/cases/${caseId}/courtroom`} className="text-sm text-blue-600 hover:underline">&larr; Courtroom</Link>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Case Analysis</h1>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-6 py-8">
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Case Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-700">{caseData?.description}</p>
            <button
              onClick={analyze}
              disabled={analyzing}
              className="mt-4 btn-primary text-sm"
            >
              {analyzing ? "Analyzing..." : "Run NLP Analysis"}
            </button>
          </CardContent>
        </Card>

        {clfResult && (
          <Card className="mb-6">
            <CardHeader><CardTitle>Classification</CardTitle></CardHeader>
            <CardContent>
              <div className="flex items-center gap-3">
                <Badge variant="info">{clfResult.label}</Badge>
                <span className="text-sm text-slate-600">
                  Confidence: {(clfResult.confidence * 100).toFixed(1)}%
                </span>
              </div>
              {clfResult.all_scores && (
                <div className="mt-3 space-y-1">
                  {Object.entries(clfResult.all_scores).map(([label, score]) => (
                    <div key={label} className="flex items-center gap-2 text-sm">
                      <span className="w-24 text-slate-600">{label}</span>
                      <div className="flex-1 bg-slate-100 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${(score as number) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-500">{((score as number) * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {nerResult.length > 0 && (
          <Card>
            <CardHeader><CardTitle>Named Entities</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {nerResult.map((ent: any, i: number) => (
                  <div key={i} className="flex items-center gap-3 text-sm">
                    <Badge variant={ent.entity_group === "PERSON" ? "danger" : ent.entity_group === "COURT" ? "warning" : "info"}>
                      {ent.entity_group}
                    </Badge>
                    <span className="font-medium text-slate-900">{ent.word}</span>
                    <span className="text-xs text-slate-400 ml-auto">{(ent.score * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
