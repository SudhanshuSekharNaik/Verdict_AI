"use client";

import Link from "next/link";
import { speakerColor, speakerIcon, formatDate } from "@/lib/utils";
import type { CourtroomEvent } from "@/types";

function EvidenceChip({ label, caseId }: { label: string; caseId?: string }) {
  const isP = label.startsWith("P-");
  const isD = label.startsWith("D-");
  const isA = label.startsWith("A-");
  const colorClass = isP
    ? "bg-red-50 text-red-700 border-red-200 hover:bg-red-100"
    : isD
    ? "bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100"
    : isA
    ? "bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100"
    : "bg-slate-50 text-slate-700 border-slate-200";

  if (caseId && (isP || isD)) {
    return (
      <Link
        href={`/cases/${caseId}/evidence`}
        className={`text-xs px-2 py-0.5 rounded border font-mono transition-colors ${colorClass}`}
        title={`Open Evidence Vault for ${label}`}
      >
        {label}
      </Link>
    );
  }

  return (
    <span className={`text-xs px-2 py-0.5 rounded border font-mono ${colorClass}`}>
      {label}
    </span>
  );
}

function ConfidenceDisplay({ confidence }: { confidence?: Record<string, number> }) {
  if (!confidence) return null;
  return (
    <div className="mt-3 pt-2 border-t border-current/10">
      <span className="text-xs font-medium opacity-70 block mb-1">Confidence Assessment:</span>
      <div className="flex flex-wrap gap-3 text-xs">
        {confidence.legal !== undefined && (
          <span className="font-mono">Legal: {(confidence.legal * 100).toFixed(0)}%</span>
        )}
        {confidence.evidence !== undefined && (
          <span className="font-mono">Evidence: {(confidence.evidence * 100).toFixed(0)}%</span>
        )}
        {confidence.citations !== undefined && (
          <span className="font-mono">Citations: {(confidence.citations * 100).toFixed(0)}%</span>
        )}
        {confidence.overall !== undefined && (
          <span className="font-mono font-semibold">Overall: {(confidence.overall * 100).toFixed(0)}%</span>
        )}
      </div>
    </div>
  );
}

export function TranscriptEntry({ event, caseId }: { event: CourtroomEvent; caseId?: string }) {
  const evidenceChips = (event as any).evidence_chips || [];
  const confidence = (event as any).confidence || (event as any).metadata_json?.confidence;
  const turnId = (event as any).metadata_json?.turn_id || (event as any).turn_id;

  return (
    <div className={`border rounded-lg p-4 mb-3 ${speakerColor(event.speaker)}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{speakerIcon(event.speaker)}</span>
        <span className="font-semibold text-sm">{event.speaker.replace(/_/g, " ")}</span>
        <span className="text-xs opacity-60 ml-auto font-mono">{event.event_type}</span>
      </div>
      <div className="text-sm whitespace-pre-wrap leading-relaxed">{event.content}</div>

      {evidenceChips.length > 0 && (
        <div className="mt-3 pt-2 border-t border-current/10">
          <span className="text-xs font-medium opacity-70 block mb-1">Evidence References:</span>
          <div className="flex flex-wrap gap-1.5">
            {evidenceChips.map((chip: string, i: number) => (
              <EvidenceChip key={i} label={chip} caseId={caseId} />
            ))}
          </div>
        </div>
      )}

      {evidenceChips.length === 0 && event.references && event.references.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {event.references.map((ref, i) => (
            <span key={i} className="text-xs bg-white/50 px-2 py-0.5 rounded border border-current/20 font-mono">
              {ref}
            </span>
          ))}
        </div>
      )}

      <ConfidenceDisplay confidence={confidence} />
    </div>
  );
}

export function Transcript({ events, caseId }: { events: CourtroomEvent[]; caseId?: string }) {
  if (!events.length) {
    return <p className="text-center text-slate-500 py-8">No events yet. Start the hearing.</p>;
  }

  const seenTurnIds = new Set<string>();
  const dedupedEvents = events.filter((event) => {
    const turnId = (event as any).metadata_json?.turn_id || (event as any).turn_id;
    if (turnId && seenTurnIds.has(turnId)) {
      return false;
    }
    if (turnId) {
      seenTurnIds.add(turnId);
    }
    return true;
  });

  return (
    <div className="space-y-2">
      {dedupedEvents.map((event) => (
        <TranscriptEntry key={event.id} event={event} caseId={caseId} />
      ))}
    </div>
  );
}
