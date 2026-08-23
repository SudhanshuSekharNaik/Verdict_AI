"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

export default function CourtIntelligencePage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [ingestUrl, setIngestUrl] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<any>(null);

  const search = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const data = await api.searchCourt(query);
      setResults(data.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setSearching(false);
    }
  };

  const ingest = async () => {
    if (!ingestUrl.trim()) return;
    setIngesting(true);
    try {
      const data = await api.ingestCourtData(ingestUrl);
      setIngestResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">&larr; Dashboard</Link>
            <h1 className="text-xl font-bold text-slate-900 mt-1">Court Intelligence</h1>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        <Card>
          <CardHeader><CardTitle>Search Court Records</CardTitle></CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by case number, party, keyword..."
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
                      <h4 className="font-medium text-slate-900">{r.title || r.citation || `Result ${i + 1}`}</h4>
                      <p className="text-sm text-slate-500">{r.court} &middot; {r.date || r.year || ""}</p>
                      <p className="text-sm text-slate-700 mt-2 line-clamp-2">{r.text || r.summary || ""}</p>
                    </div>
                    <Badge variant="info">{r.document_type || "Document"}</Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <Card>
          <CardHeader><CardTitle>Import Court Data</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600 mb-3">
              Import from permitted public sources. CAPTCHA-protected sources will require manual upload.
            </p>
            <div className="flex gap-2">
              <input
                type="url"
                value={ingestUrl}
                onChange={(e) => setIngestUrl(e.target.value)}
                placeholder="https://..."
                className="input flex-1"
              />
              <Button onClick={ingest} loading={ingesting}>Import</Button>
            </div>
            {ingestResult && (
              <div className="mt-4 p-3 rounded-lg bg-slate-50 text-sm">
                <p><strong>Status:</strong> {ingestResult.status}</p>
                {ingestResult.error && <p className="text-red-600 mt-1">{ingestResult.error}</p>}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
