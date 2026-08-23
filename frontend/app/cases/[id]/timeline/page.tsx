"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useCase } from "@/hooks/useCase";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageLoading } from "@/components/ui/loading";
import { formatDate } from "@/lib/utils";

export default function TimelinePage() {
  const params = useParams();
  const caseId = params.id as string;
  const { caseData, loading } = useCase(caseId);

  if (loading) return <PageLoading />;

  const events = caseData?.events || [];
  const sorted = [...events].sort((a: any, b: any) => new Date(a.event_date).getTime() - new Date(b.event_date).getTime());

  const eventColor = (type: string) => {
    const m: Record<string, string> = { FACT: "bg-blue-100 text-blue-800", DISPUTE: "bg-red-100 text-red-800", EVIDENCE: "bg-green-100 text-green-800" };
    return m[type] || "bg-slate-100 text-slate-700";
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <Link href={`/cases/${caseId}/courtroom`} className="text-sm text-blue-600 hover:underline">&larr; Courtroom</Link>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Timeline</h1>
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-6 py-8">
        {sorted.length === 0 ? (
          <p className="text-center text-slate-500 py-12">No events on timeline yet.</p>
        ) : (
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-200" />
            <div className="space-y-6">
              {sorted.map((ev: any) => (
                <div key={ev.id} className="relative pl-10">
                  <div className="absolute left-2.5 top-1 w-3 h-3 rounded-full bg-blue-500 border-2 border-white" />
                  <Card>
                    <CardContent className="py-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge className={eventColor(ev.event_type)}>{ev.event_type}</Badge>
                        <Badge variant="info">{ev.party_role}</Badge>
                        <span className="text-xs text-slate-400 ml-auto">{formatDate(ev.event_date)}</span>
                      </div>
                      <h4 className="font-medium text-sm text-slate-900">{ev.title}</h4>
                      <p className="text-sm text-slate-600 mt-1">{ev.description}</p>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
