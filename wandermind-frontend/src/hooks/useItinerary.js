import { useCallback } from "react";

import { useSSE } from "./useSSE";
import { useTripStore } from "../store/tripStore";

export function useItinerary() {
  const { streamItinerary } = useSSE();

  const form = useTripStore((state) => state.form);
  const loading = useTripStore((state) => state.loading);
  const progress = useTripStore((state) => state.progress);
  const result = useTripStore((state) => state.result);
  const error = useTripStore((state) => state.error);
  const history = useTripStore((state) => state.history);
  const activeHistoryToken = useTripStore((state) => state.activeHistoryToken);

  const setForm = useTripStore((state) => state.setForm);
  const setLoading = useTripStore((state) => state.setLoading);
  const setProgress = useTripStore((state) => state.setProgress);
  const setResult = useTripStore((state) => state.setResult);
  const setError = useTripStore((state) => state.setError);
  const setHistory = useTripStore((state) => state.setHistory);
  const addHistory = useTripStore((state) => state.addHistory);
  const loadHistoryEntry = useTripStore((state) => state.loadHistoryEntry);
  const deleteHistoryEntry = useTripStore((state) => state.deleteHistoryEntry);
  const clearHistory = useTripStore((state) => state.clearHistory);
  const reset = useTripStore((state) => state.reset);

  const submitTrip = useCallback(
    async (payload) => {
      setLoading(true);
      setError(null);
      setResult(null);
      setProgress({ stage: 0, label: "Preparing your travel graph...", progress: 2 });

      await streamItinerary({
        payload,
        onEvent: (event) => {
          if (event.type === "progress") {
            setProgress({ stage: event.stage, label: event.label, progress: event.progress });
            return;
          }
          if (event.type === "result") {
            setResult(event.data);
            addHistory(event.data);
            setLoading(false);
            return;
          }
          if (event.type === "error") {
            setError(event.message || "Unknown backend error");
            setLoading(false);
          }
        },
        onError: (message) => {
          setError(message);
          setLoading(false);
        },
      });
    },
    [addHistory, setError, setLoading, setProgress, setResult, streamItinerary]
  );

  return {
    form,
    loading,
    progress,
    result,
    error,
    history,
    activeHistoryToken,
    setForm,
    setError,
    setHistory,
    submitTrip,
    reset,
    loadHistoryEntry,
    deleteHistoryEntry,
    clearHistory,
  };
}
