"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageLoading } from "@/components/ui/loading";
import { api } from "@/lib/api";

export default function EvaluationPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.getEvaluation().then(setMetrics).finally(() => setLoading(false));
  }, []);

  const runEval = async () => {
    setRunning(true);
    try {
      const result = await api.runEvaluation();
      setMetrics(result);
    } catch (e) {
      console.error(e);
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <PageLoading />;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">&larr; Dashboard</Link>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Evaluation</h1>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        <div className="flex justify-end">
          <Button onClick={runEval} loading={running}>Run Evaluation</Button>
        </div>

        {!metrics ? (
          <Card><CardContent className="py-12 text-center text-slate-500">No evaluation data. Run an evaluation to see results.</CardContent></Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(metrics).map(([task, data]: [string, any]) => (
              <Card key={task}>
                <CardHeader>
                  <CardTitle className="capitalize">{task.replace(/_/g, " ")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {typeof data === "object" && data !== null ? (
                      Object.entries(data).map(([metric, value]) => (
                        <div key={metric} className="flex justify-between text-sm">
                          <span className="text-slate-600 capitalize">{metric.replace(/_/g, " ")}</span>
                          <span className="font-medium">
                            {typeof value === "number" ? (value * 100).toFixed(1) + "%" : String(value)}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-slate-600">{String(data)}</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
