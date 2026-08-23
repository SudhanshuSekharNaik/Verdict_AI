import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Evidence } from "@/types";
import { formatDate } from "@/lib/utils";

interface Props {
  evidence: Evidence[];
  onAdmit?: (id: string) => void;
}

export function EvidenceList({ evidence, onAdmit }: Props) {
  if (!evidence.length) {
    return <p className="text-slate-500 text-center py-8">No evidence uploaded yet.</p>;
  }

  return (
    <div className="space-y-3">
      {evidence.map((ev) => (
        <Card key={ev.id} className={ev.admitted ? "border-green-300" : ""}>
          <CardContent className="py-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-slate-900">{ev.title}</h4>
                  <Badge variant={ev.admitted ? "success" : "default"}>
                    {ev.admitted ? "Admitted" : "Pending"}
                  </Badge>
                  <Badge variant="info">{ev.evidence_type}</Badge>
                </div>
                <p className="text-sm text-slate-600 mt-1">{ev.description}</p>
                {ev.extracted_text && (
                  <p className="text-xs text-slate-500 mt-2 line-clamp-2">{ev.extracted_text.slice(0, 200)}...</p>
                )}
                <p className="text-xs text-slate-400 mt-1">Uploaded: {formatDate(ev.created_at)}</p>
              </div>
              {onAdmit && !ev.admitted && (
                <button
                  onClick={() => onAdmit(ev.id)}
                  className="ml-4 text-sm text-green-600 hover:text-green-800 font-medium whitespace-nowrap"
                >
                  Admit
                </button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
