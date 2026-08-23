import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + "...";
}

export function speakerColor(speaker: string): string {
  if (speaker.includes("PLAINTIFF")) return "text-red-600 bg-red-50 border-red-200";
  if (speaker.includes("DEFENCE")) return "text-blue-600 bg-blue-50 border-blue-200";
  if (speaker.includes("MY_LORD") || speaker.includes("JUDGE")) return "text-amber-600 bg-amber-50 border-amber-200";
  return "text-slate-600 bg-slate-50 border-slate-200";
}

export function speakerIcon(speaker: string): string {
  if (speaker.includes("PLAINTIFF")) return "🔴";
  if (speaker.includes("DEFENCE")) return "🔵";
  if (speaker.includes("MY_LORD") || speaker.includes("JUDGE")) return "⚖️";
  if (speaker.includes("ASSISTANT")) return "📋";
  return "📝";
}

export function verdictColor(verdict: string): string {
  if (verdict === "PLAINTIFF_SUCCEEDS") return "bg-green-100 text-green-800";
  if (verdict === "DEFENDANT_SUCCEEDS") return "bg-blue-100 text-blue-800";
  if (verdict === "PARTIAL") return "bg-yellow-100 text-yellow-800";
  return "bg-slate-100 text-slate-800";
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    INTAKE: "bg-slate-100 text-slate-700",
    PREPARATION: "bg-blue-100 text-blue-700",
    HEARING: "bg-amber-100 text-amber-700",
    DELIBERATION: "bg-purple-100 text-purple-700",
    RESOLVED: "bg-green-100 text-green-700",
  };
  return map[status] || "bg-slate-100 text-slate-700";
}
