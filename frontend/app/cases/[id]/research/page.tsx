"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageLoading } from "@/components/ui/loading";
import { api } from "@/lib/api";

export default function ResearchPage() {
  const params = useParams();
  const caseId = params.id as string;
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  const search = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const data = await api.searchResearch(caseId, query);
      setResults(data.authorities || data.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <Link href={`/cases/${caseId}/courtroom`} className="text-sm text-blue-600 hover:underline">&larr; Courtroom</Link>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Legal Research</h1>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-6 py-8">
        <Card className="mb-6">
          <CardContent>
            <div className="flex gap-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search legal authorities..."
                className="input flex-1"
                onKeyDown={(e) => e.key === "Enter" && search()}
              />
              <Button onClick={search} loading={searching}>Search</Button>
            </div>
          </CardContent>
        </Card>

        {results.length > 0 && (
          <div className="space-y-3">
            {results.map((r: any, i: number) => (
              <Card key={i}>
                <CardContent className="py-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-slate-900">{r.citation || r.title || `Authority ${i + 1}`}</h4>
                      <p className="text-sm text-slate-500 mt-1">{r.court} &middot; {r.year || ""}</p>
                      <p className="text-sm text-slate-700 mt-2 line-clamp-3">{r.chunk_text || r.summary || ""}</p>
                    </div>
                    <Badge variant="info">Score: {(r.hybrid_score || r.score || 0).toFixed(2)}</Badge>
                  </div>
                  {r.provenance_url && (
                    <a href={r.provenance_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline mt-2 inline-block">
                      View Source →
                    </a>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!searching && results.length === 0 && query && (
          <p className="text-center text-slate-500 py-12">No authorities found. Try a different query.</p>
        )}
      </main>
    </div>
  );
}
