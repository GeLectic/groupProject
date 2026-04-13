import { create } from "zustand";

const defaultForm = {
  destination: "",
  days: 7,
  month: "October",
  budget_level: "mid-range",
  travel_style: "culture",
};

const HISTORY_STORAGE_KEY = "wandermind-itinerary-history-v1";
const ACTIVE_HISTORY_STORAGE_KEY = "wandermind-active-history-token-v1";

function parseDatabaseId(value) {
  if (value === null || value === undefined) {
    return null;
  }

  const text = String(value).trim();
  if (!text) {
    return null;
  }

  const prefixed = text.match(/^db-(\d+)$/i);
  if (prefixed) {
    const fromPrefix = Number(prefixed[1]);
    return Number.isInteger(fromPrefix) && fromPrefix > 0 ? fromPrefix : null;
  }

  const numeric = Number(text);
  return Number.isInteger(numeric) && numeric > 0 ? numeric : null;
}

function normalizeResultPayload(result, fallback = {}) {
  const source = result && typeof result === "object" ? result : {};
  const inferredItineraryId =
    source.itinerary_id
    ?? fallback.itinerary_id
    ?? parseDatabaseId(source.id)
    ?? parseDatabaseId(fallback.id)
    ?? null;

  const normalized = {
    ...source,
    destination: source.destination || fallback.destination || "Untitled itinerary",
    days: source.days ?? fallback.days ?? defaultForm.days,
    month: source.month || fallback.month || defaultForm.month,
    budget_level: source.budget_level || fallback.budget_level || defaultForm.budget_level,
    travel_style: source.travel_style || fallback.travel_style || defaultForm.travel_style,
    itinerary: Array.isArray(source.itinerary) ? source.itinerary : [],
    hotels: source.hotels && typeof source.hotels === "object" ? source.hotels : {},
    hidden_gems: Array.isArray(source.hidden_gems) ? source.hidden_gems : [],
    notices: Array.isArray(source.notices) ? source.notices : [],
    warnings: Array.isArray(source.warnings) ? source.warnings : [],
    must_eat: Array.isArray(source.must_eat) ? source.must_eat : [],
    cultural_tips: Array.isArray(source.cultural_tips) ? source.cultural_tips : [],
    packing: Array.isArray(source.packing) ? source.packing : [],
    budget_breakdown:
      source.budget_breakdown && typeof source.budget_breakdown === "object" ? source.budget_breakdown : {},
    data_sources: source.data_sources && typeof source.data_sources === "object" ? source.data_sources : {},
    generated_at: source.generated_at || fallback.generated_at || new Date().toISOString(),
    itinerary_id: parseDatabaseId(inferredItineraryId),
  };

  const hotels = normalized.hotels || {};
  normalized.hotels = {
    budget: Array.isArray(hotels.budget) ? hotels.budget : [],
    mid_range: Array.isArray(hotels.mid_range) ? hotels.mid_range : [],
    luxury: Array.isArray(hotels.luxury) ? hotels.luxury : [],
  };

  normalized.data_sources = {
    youtube_videos_used: Array.isArray(normalized.data_sources.youtube_videos_used)
      ? normalized.data_sources.youtube_videos_used
      : [],
    reddit_posts_used: Number(normalized.data_sources.reddit_posts_used || 0),
    quora_pages_used: Number(normalized.data_sources.quora_pages_used || 0),
  };

  return normalized;
}

function toFormFromHistory(entry, currentForm = defaultForm) {
  return {
    destination: entry?.destination || currentForm.destination || defaultForm.destination,
    days: entry?.days ?? currentForm.days ?? defaultForm.days,
    month: entry?.month || currentForm.month || defaultForm.month,
    budget_level: entry?.budget_level || currentForm.budget_level || defaultForm.budget_level,
    travel_style: entry?.travel_style || currentForm.travel_style || defaultForm.travel_style,
  };
}

function loadActiveHistoryToken() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const value = window.localStorage.getItem(ACTIVE_HISTORY_STORAGE_KEY);
    return value || null;
  } catch {
    return null;
  }
}

function persistActiveHistoryToken(token) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    if (!token) {
      window.localStorage.removeItem(ACTIVE_HISTORY_STORAGE_KEY);
      return;
    }
    window.localStorage.setItem(ACTIVE_HISTORY_STORAGE_KEY, String(token));
  } catch {
    // Ignore storage errors and keep app usable.
  }
}

function normalizeHistoryEntry(entry, index) {
  if (!entry || typeof entry !== "object") {
    return null;
  }

  const dataSource = entry.data && typeof entry.data === "object" ? entry.data : entry;
  if (!dataSource || typeof dataSource !== "object") {
    return null;
  }

  const data = normalizeResultPayload(dataSource, entry);
  const dbId = parseDatabaseId(entry.db_id ?? data.itinerary_id ?? entry.id);
  if (dbId && !data.itinerary_id) {
    data.itinerary_id = dbId;
  }

  const generatedAt = String(data.generated_at || "");
  const createdAt = entry.createdAt || generatedAt || new Date().toISOString();
  const fallbackId = dbId ? `db-${dbId}` : generatedAt || `legacy-${createdAt}-${index}`;
  const normalizedId = dbId ? `db-${dbId}` : String(entry.id || fallbackId);

  return {
    id: normalizedId,
    db_id: dbId,
    createdAt,
    destination: entry.destination || data.destination || "Untitled itinerary",
    days: entry.days ?? data.days ?? null,
    month: entry.month || data.month || "",
    budget_level: entry.budget_level || data.budget_level || "",
    travel_style: entry.travel_style || data.travel_style || "",
    data,
  };
}

function isMatchingHistoryEntry(entry, identifier) {
  const token = String(identifier || "");
  if (!token) {
    return false;
  }

  const entryId = String(entry?.id || "");
  const generatedAt = String(entry?.data?.generated_at || "");
  const entryDbId = parseDatabaseId(entry?.db_id ?? entry?.data?.itinerary_id ?? entryId);
  const tokenDbId = parseDatabaseId(token);

  return (
    (entryId && entryId === token)
    || (generatedAt && generatedAt === token)
    || (tokenDbId && entryDbId && tokenDbId === entryDbId)
  );
}

function loadHistory() {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(HISTORY_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }

    const normalized = parsed
      .map((entry, index) => normalizeHistoryEntry(entry, index))
      .filter(Boolean);

    if (JSON.stringify(normalized) !== raw) {
      persistHistory(normalized);
    }

    return normalized;
  } catch {
    return [];
  }
}

function persistHistory(history) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
  } catch {
    // Ignore storage errors and keep app usable.
  }
}

function createHistoryEntry(result) {
  const normalized = normalizeResultPayload(result);
  const dbId = parseDatabaseId(normalized.itinerary_id);
  const id = dbId
    ? `db-${dbId}`
    : typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

  return {
    id,
    db_id: dbId,
    createdAt: new Date().toISOString(),
    destination: normalized.destination || "Untitled itinerary",
    days: normalized.days ?? null,
    month: normalized.month || "",
    budget_level: normalized.budget_level || "",
    travel_style: normalized.travel_style || "",
    data: normalized,
  };
}

function buildInitialPersistenceState() {
  const history = loadHistory();
  const activeToken = loadActiveHistoryToken();
  const selected = history.find((item) => isMatchingHistoryEntry(item, activeToken)) || null;

  return {
    history,
    activeHistoryToken: selected?.id || null,
    result: selected?.data || null,
    form: selected ? toFormFromHistory(selected, defaultForm) : defaultForm,
  };
}

const initialState = buildInitialPersistenceState();

export const useTripStore = create((set) => ({
  form: initialState.form,
  loading: false,
  progress: { stage: 0, label: "", progress: 0 },
  result: initialState.result,
  error: null,
  history: initialState.history,
  activeHistoryToken: initialState.activeHistoryToken,
  setForm: (payload) => set((state) => ({ form: { ...state.form, ...payload } })),
  setLoading: (loading) => set({ loading }),
  setProgress: (progress) => set({ progress }),
  setResult: (result) => set({ result: result ? normalizeResultPayload(result) : null }),
  setError: (error) => set({ error }),
  setHistory: (items) =>
    set((state) => {
      const normalized = (Array.isArray(items) ? items : [])
        .map((entry, index) => normalizeHistoryEntry(entry, index))
        .filter(Boolean)
        .slice(0, 100);

      persistHistory(normalized);

      const selected = normalized.find((item) => isMatchingHistoryEntry(item, state.activeHistoryToken)) || normalized[0] || null;
      const nextToken = selected?.id || null;
      persistActiveHistoryToken(nextToken);

      return {
        history: normalized,
        activeHistoryToken: nextToken,
        result: selected?.data || null,
        form: selected ? toFormFromHistory(selected, state.form) : state.form,
      };
    }),
  addHistory: (result) =>
    set((state) => {
      if (!result || typeof result !== "object") {
        return {};
      }

      const normalizedResult = normalizeResultPayload(result);

      const currentKey = String(normalizedResult.generated_at || "");
      const currentDbId = parseDatabaseId(normalizedResult.itinerary_id);
      const deduped = state.history.filter((item) => {
        const sameGeneratedAt = currentKey && String(item?.data?.generated_at || "") === currentKey;
        const itemDbId = parseDatabaseId(item?.db_id ?? item?.data?.itinerary_id ?? item?.id);
        const sameDbId = currentDbId && itemDbId && currentDbId === itemDbId;
        return !(sameGeneratedAt || sameDbId);
      });
      const createdEntry = createHistoryEntry(normalizedResult);
      const history = [createdEntry, ...deduped]
        .map((entry, index) => normalizeHistoryEntry(entry, index))
        .filter(Boolean)
        .slice(0, 20);

      persistHistory(history);
      persistActiveHistoryToken(createdEntry.id);

      return {
        history,
        activeHistoryToken: createdEntry.id,
      };
    }),
  loadHistoryEntry: (identifier) =>
    set((state) => {
      const selected = state.history.find((item) => isMatchingHistoryEntry(item, identifier));
      if (!selected) {
        return {};
      }

      const selectedData = selected.data && typeof selected.data === "object" ? selected.data : null;
      if (!selectedData) {
        return {};
      }

      persistActiveHistoryToken(selected.id);

      return {
        result: selectedData,
        loading: false,
        error: null,
        progress: { stage: 0, label: "", progress: 0 },
        form: toFormFromHistory(selected, state.form),
        activeHistoryToken: selected.id,
      };
    }),
  deleteHistoryEntry: (identifier) =>
    set((state) => {
      const removed = state.history.find((item) => isMatchingHistoryEntry(item, identifier));
      const history = state.history.filter((item) => !isMatchingHistoryEntry(item, identifier));
      persistHistory(history);

      const activeGeneratedAt = String(state.result?.generated_at || "");
      const removedGeneratedAt = String(removed?.data?.generated_at || "");
      const removedIsActiveByReference = Boolean(removed && state.result === removed.data);
      const removedIsActiveByToken = Boolean(removed && isMatchingHistoryEntry(removed, state.activeHistoryToken));

      if (
        removedIsActiveByReference
        || removedIsActiveByToken
        || (activeGeneratedAt && removedGeneratedAt && activeGeneratedAt === removedGeneratedAt)
      ) {
        const fallbackEntry = history[0] || null;
        const nextToken = fallbackEntry?.id || null;

        persistActiveHistoryToken(nextToken);

        return {
          history,
          activeHistoryToken: nextToken,
          result: fallbackEntry?.data || null,
          form: fallbackEntry ? toFormFromHistory(fallbackEntry, state.form) : state.form,
        };
      }

      return { history };
    }),
  clearHistory: () =>
    set(() => {
      persistHistory([]);
      persistActiveHistoryToken(null);
      return { history: [], activeHistoryToken: null, result: null };
    }),
  reset: () =>
    set(() => {
      persistActiveHistoryToken(null);
      return {
        loading: false,
        progress: { stage: 0, label: "", progress: 0 },
        result: null,
        error: null,
        activeHistoryToken: null,
      };
    }),
}));
