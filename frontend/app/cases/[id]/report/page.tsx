"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageLoading } from "@/components/ui/loading";
import { api } from "@/lib/api";

export default function ReportPage() {
  const params = useParams();
  const caseId = params.id as string;
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getReport(caseId).then(setReport).finally(() => setLoading(false));
  }, [caseId]);

  if (loading) return <PageLoading />;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <Link href={`/cases/${caseId}/courtroom`} className="text-sm text-blue-600 hover:underline">&larr; Courtroom</Link>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Post-Judgment Report</h1>
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-6 py-8">
        {!report ? (
          <Card><CardContent className="py-12 text-center text-slate-500">No report available yet.</CardContent></Card>
        ) : (
          <div className="space-y-6">
            <Card>
              <CardHeader><CardTitle>Case Summary</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p><strong>Case:</strong> {report.case_title || "N/A"}</p>
                <p><strong>Verdict:</strong> <Badge>{report.verdict || "N/A"}</Badge></p>
                <p><strong>Total Rounds:</strong> {report.total_rounds || 0}</p>
                <p><strong>Plaintiff Arguments:</strong> {report.plaintiff_arguments || 0}</p>
                <p><strong>Defence Arguments:</strong> {report.defence_arguments || 0}</p>
              </CardContent>
            </Card>
            {report.evaluation && (
              <Card>
                <CardHeader><CardTitle>AI Evaluation</CardTitle></CardHeader>
                <CardContent className="space-y-2 text-sm">
                  {Object.entries(report.evaluation).map(([key, val]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-slate-600">{key.replace(/_/g, " ")}</span>
                      <span className="font-medium">{typeof val === "number" ? (val * 100).toFixed(1) + "%" : String(val)}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
