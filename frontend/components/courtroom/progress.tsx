"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { STAGE_LABELS, STAGE_ORDER, type CourtroomStage } from "@/types";

interface Props {
  currentStage: string;
  rounds: any[];
}

export function CourtroomProgress({ currentStage, rounds }: Props) {
  const currentIdx = STAGE_ORDER.indexOf(currentStage as CourtroomStage);
  return (
    <Card>
      <CardHeader>
        <CardTitle>Hearing Progress</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {STAGE_ORDER.map((stage, idx) => {
            const isCompleted = idx < currentIdx;
            const isCurrent = idx === currentIdx;
            const label = STAGE_LABELS[stage];
            return (
              <div
                key={stage}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isCurrent ? "bg-blue-50 border border-blue-200 font-semibold text-blue-800" :
                  isCompleted ? "text-green-700 bg-green-50" : "text-slate-400"
                }`}
              >
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  isCompleted ? "bg-green-500 text-white" :
                  isCurrent ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-500"
                }`}>
                  {isCompleted ? "✓" : idx + 1}
                </span>
                <span>{label}</span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
