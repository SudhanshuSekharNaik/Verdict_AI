"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { Case } from "@/types";

export function useCases() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listCases();
      setCases(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);
  return { cases, loading, error, refresh };
}

export function useCase(caseId: string | null) {
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!caseId) return;
    setLoading(true);
    try {
      const data = await api.getCase(caseId);
      setCaseData(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => { refresh(); }, [refresh]);
  return { caseData, loading, error, refresh };
}

export function useCourtroom(caseId: string | null) {
  const [state, setState] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [stepping, setStepping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!caseId) return;
    setLoading(true);
    try {
      const data = await api.getCourtroomState(caseId);
      setState(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  const step = useCallback(async (targetStage?: string) => {
    if (!caseId) return;
    setStepping(true);
    try {
      const result = await api.stepCourtroom(caseId, targetStage);
      await load();
      return result;
    } catch (e: any) {
      setError(e.message);
    } finally {
      setStepping(false);
    }
  }, [caseId, load]);

  const start = useCallback(async () => {
    if (!caseId) return;
    setStepping(true);
    try {
      await api.startCourtroom(caseId);
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setStepping(false);
    }
  }, [caseId, load]);

  useEffect(() => { load(); }, [load]);
  return { state, loading, stepping, error, step, start, refresh: load };
}
