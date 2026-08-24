"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageLoading } from "@/components/ui/loading";
import { api } from "@/lib/api";
import { statusColor, formatDate } from "@/lib/utils";

export default function DashboardPage() {
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, hearing: 0, resolved: 0 });

  useEffect(() => {
    api.listCases().then((data) => {
      setCases(data);
      setStats({
        total: data.length,
        hearing: data.filter((c: any) => c.status === "HEARING").length,
        resolved: data.filter((c: any) => c.status === "RESOLVED").length,
      });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading />;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">⚖️ VerdictAI</h1>
            <p className="text-sm text-slate-500">Nyay Manch · न्याय मंच — AI Courtroom Simulation</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardContent className="py-6 text-center">
              <p className="text-3xl font-bold text-slate-900">{stats.total}</p>
              <p className="text-sm text-slate-500 mt-1">Total Cases</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-6 text-center">
              <p className="text-3xl font-bold text-amber-600">{stats.hearing}</p>
              <p className="text-sm text-slate-500 mt-1">In Hearing</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-6 text-center">
              <p className="text-3xl font-bold text-green-600">{stats.resolved}</p>
              <p className="text-sm text-slate-500 mt-1">Resolved</p>
            </CardContent>
          </Card>
        </div>

        <h2 className="text-lg font-semibold text-slate-900 mb-4">Cases</h2>
        {cases.length === 0 ? (
          <Card><CardContent><p className="text-center text-slate-500 py-8">No cases yet. Run the seed script to add demo cases.</p></CardContent></Card>
        ) : (
          <div className="space-y-3">
            {cases.map((c: any) => (
              <Link key={c.id} href={`/cases/${c.id}/courtroom`}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="py-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold text-slate-900">{c.title}</h3>
                        <p className="text-sm text-slate-500 mt-1">{c.case_number} &middot; {c.case_type} &middot; {c.jurisdiction}</p>
                      </div>
                      <Badge className={statusColor(c.status)}>{c.status}</Badge>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
