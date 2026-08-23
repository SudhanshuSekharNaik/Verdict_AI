"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { useCase } from "@/hooks/useCase";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageLoading } from "@/components/ui/loading";
import { EvidenceList } from "@/components/evidence/evidence-list";
import { api } from "@/lib/api";

export default function EvidencePage() {
  const params = useParams();
  const caseId = params.id as string;
  const { caseData, loading, refresh } = useCase(caseId);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", file.name);
      formData.append("description", "User uploaded evidence");
      await api.uploadEvidence(caseId, formData);
      refresh();
    } catch (e) {
      console.error(e);
    } finally {
      setUploading(false);
    }
  };

  const handleAdmit = async (evidenceId: string) => {
    try {
      await api.admitEvidence(caseId, evidenceId);
      refresh();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <PageLoading />;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <Link href={`/cases/${caseId}/courtroom`} className="text-sm text-blue-600 hover:underline">&larr; Courtroom</Link>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Evidence Vault</h1>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">Uploaded Evidence</h2>
          <div>
            <input ref={fileRef} type="file" className="hidden" onChange={handleUpload} accept=".pdf,.txt,.png,.jpg" />
            <Button onClick={() => fileRef.current?.click()} loading={uploading}>Upload Evidence</Button>
          </div>
        </div>
        <EvidenceList evidence={caseData?.evidence_list || []} onAdmit={handleAdmit} />
      </main>
    </div>
  );
}
