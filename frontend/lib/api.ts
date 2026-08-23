const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = `${API_BASE}/api/v1`;

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_V1}${path}`;
  const isFormData = options.body instanceof FormData;
  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      headers: isFormData
        ? options.headers
        : { "Content-Type": "application/json", ...options.headers },
    });
  } catch {
    throw new Error(`Cannot reach backend at ${API_BASE}. Is it running?`);
  }
  const text = await res.text();
  let body: any = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    throw new Error(
      `Backend returned non-JSON response (HTML) from ${url}. Is the FastAPI backend running on ${API_BASE}?`
    );
  }
  if (!res.ok) {
    throw new Error(body?.detail || body?.error?.message || `API error: ${res.status}`);
  }
  if (body?.success === false) throw new Error(body.error?.message || "Request failed");
  return body.data ?? body;
}

export const api = {
  health: () => request<{ status: string }>("/../../health"),
  version: () => request<{ version: string; capabilities: string[] }>("/../../api/version"),

  // Cases
  listCases: () => request<any[]>("/cases"),
  getCase: (id: string) => request<any>(`/cases/${id}`),
  createCase: (data: any) => request<any>("/cases", { method: "POST", body: JSON.stringify(data) }),
  deleteCase: (id: string) => request<void>(`/cases/${id}`, { method: "DELETE" }),

  // Evidence
  listEvidence: (caseId: string) => request<any[]>(`/cases/${caseId}/evidence`),
  uploadEvidence: (caseId: string, formData: FormData) =>
    request<any>(`/cases/${caseId}/evidence`, { method: "POST", body: formData }),
  admitEvidence: (caseId: string, evidenceId: string) =>
    request<any>(`/cases/${caseId}/evidence/${evidenceId}/admit`, { method: "POST" }),

  // Courtroom
  startCourtroom: (caseId: string) =>
    request<any>(`/courtroom/cases/${caseId}/session/start`, { method: "POST" }),
  getCourtroomState: (caseId: string) =>
    request<any>(`/courtroom/cases/${caseId}/state`),
  stepCourtroom: (caseId: string, targetStage?: string) =>
    request<any>(`/courtroom/cases/${caseId}/step`, {
      method: "POST",
      body: JSON.stringify({ target_stage: targetStage || null }),
    }),
  askJudgeQuestion: (caseId: string, targetAgent: string, question: string) =>
    request<any>(`/courtroom/cases/${caseId}/judge/question`, {
      method: "POST",
      body: JSON.stringify({ target_agent: targetAgent, question }),
    }),
  enterJudgment: (caseId: string, data: any) =>
    request<any>(`/courtroom/cases/${caseId}/judgment`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getReport: (caseId: string) =>
    request<any>(`/courtroom/cases/${caseId}/report`),

  // Adversarial Hearing
  getHearingMessages: (caseId: string) =>
    request<any>(`/hearing/cases/${caseId}/hearing/messages`, { method: "POST" }),
  generateHearingMessage: (caseId: string, data: { side: string; stage?: string; instruction?: string; opposing_turn_id?: string }) =>
    request<any>(`/hearing/cases/${caseId}/hearing/generate`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  judgeAnalysis: (caseId: string) =>
    request<any>(`/hearing/cases/${caseId}/hearing/judge-analysis`, {
      method: "POST",
      body: JSON.stringify({}),
    }),

  // ML
  runNER: (text: string) =>
    request<any[]>("/ml/ner", { method: "POST", body: JSON.stringify({ text }) }),
  classifyCase: (text: string) =>
    request<any>("/ml/classify/case", { method: "POST", body: JSON.stringify({ text }) }),
  classifyDocument: (text: string) =>
    request<any>("/ml/classify/document", { method: "POST", body: JSON.stringify({ text }) }),
  classifySentences: (sentences: string[]) =>
    request<any[]>("/ml/classify/sentences", { method: "POST", body: JSON.stringify({ sentences }) }),
  runNLI: (claim: string, evidence: string) =>
    request<any>("/ml/nli", { method: "POST", body: JSON.stringify({ claim, evidence }) }),
  runGrounding: (claim: string, evidencePassages: string[]) =>
    request<any>("/ml/grounding", { method: "POST", body: JSON.stringify({ claim, evidence_passages: evidencePassages }) }),

  // Research
  searchResearch: (caseId: string, query: string) =>
    request<any>(`/research/cases/${caseId}/search`, {
      method: "POST",
      body: JSON.stringify({ query }),
    }),

  // Court Intelligence
  searchCourt: (query: string, filters?: any) =>
    request<any>("/court/search", { method: "POST", body: JSON.stringify({ query, ...filters }) }),
  ingestCourtData: (url: string, documentType?: string) =>
    request<any>("/court/ingest", { method: "POST", body: JSON.stringify({ url, document_type: documentType }) }),

  // Evaluation
  getEvaluation: () => request<any>("/evaluation/metrics"),
  runEvaluation: () => request<any>("/evaluation/run", { method: "POST" }),

  // Agents
  getAgents: () => request<any[]>("/agents"),
};
