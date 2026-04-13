import { AnimatePresence, MotionConfig, motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { Copy, Download, LogOut, MapPinned, Orbit, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { apiClient, clearAuthToken, getAuthToken, setAuthToken } from "./api/client";
import AuthPanel from "./components/AuthPanel";
import DayCard from "./components/DayCard";
import HiddenGemCard from "./components/HiddenGemCard";
import HotelSection from "./components/HotelSection";
import InputForm from "./components/InputForm";
import ItineraryHistoryPanel from "./components/ItineraryHistoryPanel";
import PipelineProgress from "./components/PipelineProgress";
import TipsPanel from "./components/TipsPanel";
import { useItinerary } from "./hooks/useItinerary";

const resultContainer = {
  hidden: { opacity: 0, y: 12 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.45,
      staggerChildren: 0.08,
      delayChildren: 0.06,
    },
  },
};

const revealItem = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.42 } },
};

function parseDatabaseToken(token) {
  const matched = String(token || "").match(/^db-(\d+)$/i);
  if (!matched) {
    return null;
  }

  const itineraryId = Number(matched[1]);
  return Number.isInteger(itineraryId) && itineraryId > 0 ? itineraryId : null;
}

function extractApiError(error, fallbackMessage) {
  const maybeDetail = error?.response?.data?.detail;
  return typeof maybeDetail === "string" && maybeDetail.trim() ? maybeDetail : fallbackMessage;
}

function AmbientLayer() {
  const pointerX = useMotionValue(typeof window !== "undefined" ? window.innerWidth / 2 : 0);
  const pointerY = useMotionValue(typeof window !== "undefined" ? window.innerHeight / 2 : 0);
  const [pointerInteractive, setPointerInteractive] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const finePointer = window.matchMedia("(pointer: fine)").matches;
    setPointerInteractive(!reducedMotion && finePointer);
  }, []);

  useEffect(() => {
    if (!pointerInteractive) {
      return undefined;
    }

    let rafId = 0;
    let nextX = 0;
    let nextY = 0;

    const commit = () => {
      pointerX.set(nextX);
      pointerY.set(nextY);
      rafId = 0;
    };

    const onPointerMove = (event) => {
      nextX = event.clientX;
      nextY = event.clientY;
      if (!rafId) {
        rafId = window.requestAnimationFrame(commit);
      }
    };

    window.addEventListener("pointermove", onPointerMove, { passive: true });
    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      if (rafId) {
        window.cancelAnimationFrame(rafId);
      }
    };
  }, [pointerInteractive, pointerX, pointerY]);

  const softX = useSpring(pointerX, { stiffness: 52, damping: 24, mass: 0.8 });
  const softY = useSpring(pointerY, { stiffness: 52, damping: 24, mass: 0.8 });

  const parallaxX = useTransform(softX, (value) => {
    const width = typeof window !== "undefined" ? window.innerWidth || 1 : 1;
    return ((value / width) - 0.5) * 46;
  });
  const parallaxY = useTransform(softY, (value) => {
    const height = typeof window !== "undefined" ? window.innerHeight || 1 : 1;
    return ((value / height) - 0.5) * 34;
  });

  const reverseParallaxX = useTransform(parallaxX, (value) => -value * 0.7);
  const reverseParallaxY = useTransform(parallaxY, (value) => -value * 0.7);

  const cursorGlowX = useTransform(softX, (value) => value - 190);
  const cursorGlowY = useTransform(softY, (value) => value - 190);

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <motion.div
        className="performance-layer absolute -left-20 top-20 h-72 w-72 rounded-full bg-gold/15 blur-3xl"
        style={{ x: parallaxX, y: parallaxY }}
        animate={{ scale: [1, 1.07, 1], opacity: [0.9, 1, 0.9] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="performance-layer absolute right-0 top-1/3 h-80 w-80 rounded-full bg-emerald/15 blur-3xl"
        style={{ x: reverseParallaxX, y: reverseParallaxY }}
        animate={{ scale: [1, 1.08, 1], opacity: [0.9, 1, 0.9] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="performance-layer absolute bottom-0 left-1/3 h-72 w-72 rounded-full bg-amber-200/30 blur-3xl"
        style={{ x: parallaxX, y: reverseParallaxY }}
        animate={{ scale: [1, 1.06, 1], opacity: [0.95, 1, 0.95] }}
        transition={{ duration: 11, repeat: Infinity, ease: "easeInOut" }}
      />
      {pointerInteractive ? (
        <motion.div
          className="performance-layer absolute h-[380px] w-[380px] rounded-full bg-[radial-gradient(circle,rgba(255,246,224,0.55)_0%,rgba(255,235,195,0.22)_38%,rgba(255,255,255,0)_68%)] blur-2xl"
          style={{ x: cursorGlowX, y: cursorGlowY }}
        />
      ) : null}
    </div>
  );
}

function HeaderActions({ canExport, onExportPdf, exporting, onCopyLink, copied }) {
  return (
    <div className="flex gap-2">
      <button
        onClick={onExportPdf}
        className="rounded-lg border border-gold/35 bg-surface/85 px-3 py-2 text-sm text-parchment/75 shadow-soft transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={!canExport || exporting}
      >
        <span className="flex items-center gap-2">
          <Download size={14} /> {exporting ? "Exporting..." : "Export PDF"}
        </span>
      </button>
      <button
        onClick={onCopyLink}
        className="rounded-lg border border-gold/35 bg-surface/85 px-3 py-2 text-sm text-parchment/75 shadow-soft transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={!canExport}
      >
        <span className="flex items-center gap-2">
          <Copy size={14} /> {copied ? "Copied" : "Copy Link"}
        </span>
      </button>
    </div>
  );
}

function DataSourceSummary({ result }) {
  const source = result?.data_sources || {};
  const youtubeCount = Array.isArray(source.youtube_videos_used) ? source.youtube_videos_used.length : 0;

  return (
    <motion.div variants={revealItem} className="heavy-section grid grid-cols-1 gap-3 md:grid-cols-3">
      <div className="panel-surface rounded-2xl p-4 text-sm text-parchment/80">
        <p className="mb-2 text-xs uppercase tracking-[0.16em] text-gold/80">YouTube</p>
        <p className="text-3xl font-semibold text-parchment">{youtubeCount}</p>
        <p className="text-xs text-parchment/65">videos considered</p>
      </div>
      <div className="panel-surface rounded-2xl p-4 text-sm text-parchment/80">
        <p className="mb-2 text-xs uppercase tracking-[0.16em] text-gold/80">Reddit</p>
        <p className="text-3xl font-semibold text-parchment">{source.reddit_posts_used || 0}</p>
        <p className="text-xs text-parchment/65">community threads used</p>
      </div>
      <div className="panel-surface rounded-2xl p-4 text-sm text-parchment/80">
        <p className="mb-2 text-xs uppercase tracking-[0.16em] text-gold/80">Quora</p>
        <p className="text-3xl font-semibold text-parchment">{source.quora_pages_used || 0}</p>
        <p className="text-xs text-parchment/65">answer pages mined</p>
      </div>
    </motion.div>
  );
}

export default function App() {
  const {
    form,
    loading,
    progress,
    result,
    error,
    history,
    activeHistoryToken,
    setForm,
    setHistory,
    submitTrip,
    reset,
    setError,
    loadHistoryEntry,
    deleteHistoryEntry,
    clearHistory,
  } = useItinerary();
  const [exporting, setExporting] = useState(false);
  const [copied, setCopied] = useState(false);
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authWorking, setAuthWorking] = useState(false);
  const [deletingAccount, setDeletingAccount] = useState(false);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    let active = true;

    const bootstrapSession = async () => {
      const token = getAuthToken();
      if (!token) {
        if (active) {
          setAuthLoading(false);
        }
        return;
      }

      try {
        const [meResponse, historyResponse] = await Promise.all([
          apiClient.get("/api/auth/me"),
          apiClient.get("/api/itineraries"),
        ]);

        if (!active) {
          return;
        }

        setUser(meResponse.data || null);
        setHistory(historyResponse.data || []);
        setAuthError("");
      } catch {
        clearAuthToken();
        if (!active) {
          return;
        }
        setUser(null);
        setHistory([]);
      } finally {
        if (active) {
          setAuthLoading(false);
        }
      }
    };

    bootstrapSession();

    return () => {
      active = false;
    };
  }, [setHistory]);

  const canExport = Boolean(result && !loading);

  const handleLogin = async ({ email, password }) => {
    setAuthWorking(true);
    setAuthError("");

    try {
      const authResponse = await apiClient.post("/api/auth/login", { email, password });
      const token = authResponse?.data?.access_token;
      if (!token) {
        throw new Error("Token missing from login response.");
      }

      setAuthToken(token);

      const [meResponse, historyResponse] = await Promise.all([
        apiClient.get("/api/auth/me"),
        apiClient.get("/api/itineraries"),
      ]);

      setUser(meResponse.data || null);
      setHistory(historyResponse.data || []);
      setAuthError("");
    } catch (error) {
      clearAuthToken();
      setUser(null);
      setAuthError(extractApiError(error, "Unable to sign in. Please verify your credentials."));
    } finally {
      setAuthWorking(false);
    }
  };

  const handleRegister = async ({ email, password }) => {
    setAuthWorking(true);
    setAuthError("");

    try {
      const authResponse = await apiClient.post("/api/auth/register", { email, password });
      const token = authResponse?.data?.access_token;
      if (!token) {
        throw new Error("Token missing from register response.");
      }

      setAuthToken(token);

      const [meResponse, historyResponse] = await Promise.all([
        apiClient.get("/api/auth/me"),
        apiClient.get("/api/itineraries"),
      ]);

      setUser(meResponse.data || null);
      setHistory(historyResponse.data || []);
      setAuthError("");
    } catch (error) {
      clearAuthToken();
      setUser(null);
      setAuthError(extractApiError(error, "Unable to create account. Please try another email."));
    } finally {
      setAuthWorking(false);
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    setUser(null);
    setAuthError("");
    setError(null);
    reset();
    clearHistory();
  };

  const handleDeleteAccount = async () => {
    if (!user || deletingAccount) {
      return;
    }

    const confirmed = window.confirm(
      "Delete account permanently? This will remove your profile and all saved itineraries."
    );
    if (!confirmed) {
      return;
    }

    const password = window.prompt("Enter your password to confirm account deletion:");
    if (password === null) {
      return;
    }

    if (!password.trim()) {
      setError("Password is required to delete your account.");
      return;
    }

    try {
      setDeletingAccount(true);
      await apiClient.delete("/api/auth/me", { data: { password } });

      clearAuthToken();
      setUser(null);
      setAuthError("");
      setError(null);
      reset();
      clearHistory();
    } catch (error) {
      setError(extractApiError(error, "Unable to delete account right now."));
    } finally {
      setDeletingAccount(false);
    }
  };

  const handleDeleteHistory = async (token) => {
    const itineraryId = parseDatabaseToken(token);

    if (itineraryId) {
      try {
        await apiClient.delete(`/api/itineraries/${itineraryId}`);
      } catch (error) {
        setError(extractApiError(error, "Unable to delete itinerary from server."));
        return;
      }
    }

    deleteHistoryEntry(token);
  };

  const handleClearHistory = async () => {
    if (history.length > 0) {
      try {
        await apiClient.delete("/api/itineraries");
      } catch (error) {
        setError(extractApiError(error, "Unable to clear saved itineraries right now."));
        return;
      }
    }

    clearHistory();
  };

  const handleExportPdf = async () => {
    if (!result || exporting) {
      return;
    }

    try {
      setExporting(true);
      const response = await apiClient.post("/api/export-pdf", result, { responseType: "blob" });
      const blob = new Blob([response.data], { type: "application/pdf" });
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const destination = (result.destination || "itinerary").toLowerCase().replace(/[^a-z0-9]+/g, "-");
      anchor.href = objectUrl;
      anchor.download = `wandermind-${destination || "itinerary"}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (err) {
      setError("Unable to export PDF right now. Please try again.");
    } finally {
      setExporting(false);
    }
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      setError("Copy link failed in this browser session.");
    }
  };

  return (
    <MotionConfig reducedMotion="user">
      <main className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
        <AmbientLayer />
        <div className="mx-auto max-w-6xl">
        <motion.header
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="panel-surface mb-8 rounded-3xl p-5 sm:p-6"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.28em] text-gold/80">
                <Orbit size={14} /> WanderMind
              </p>
              <h1 className="font-display text-4xl text-parchment sm:text-5xl">Enterprise Travel Intelligence</h1>
              <p className="mt-2 max-w-2xl text-sm text-parchment/70">
                A polished planning cockpit powered by traveler signals from YouTube, Reddit, Quora, and semantic retrieval.
              </p>
            </div>
            <div className="flex flex-col items-start gap-2 sm:items-end">
              <HeaderActions
                canExport={canExport && Boolean(user)}
                onExportPdf={handleExportPdf}
                exporting={exporting}
                onCopyLink={handleCopyLink}
                copied={copied}
              />

              {user ? (
                <div className="flex items-center gap-2">
                  <p className="rounded-full border border-gold/25 bg-surface/70 px-3 py-1 text-xs text-parchment/80">
                    {user.email}
                  </p>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="inline-flex items-center gap-1 rounded-full border border-gold/35 bg-surface/80 px-3 py-1 text-xs text-parchment/80 transition hover:border-gold"
                  >
                    <LogOut size={13} /> Logout
                  </button>
                  <button
                    type="button"
                    onClick={handleDeleteAccount}
                    disabled={deletingAccount}
                    className="inline-flex items-center gap-1 rounded-full border border-rose-500/40 bg-rose-100/70 px-3 py-1 text-xs text-rose-800 transition hover:border-rose-600/60 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <Trash2 size={13} /> {deletingAccount ? "Deleting..." : "Delete Account"}
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </motion.header>

        {error && (
          <div className="mb-6 rounded-xl border border-rose-400/50 bg-rose-200/40 px-4 py-3 text-sm text-rose-800">
            {error}
          </div>
        )}

        {authLoading ? (
          <div className="panel-surface mx-auto max-w-xl rounded-3xl p-8 text-center text-parchment/75">
            Restoring secure session...
          </div>
        ) : !user ? (
          <AuthPanel
            loading={authWorking}
            error={authError}
            onLogin={handleLogin}
            onRegister={handleRegister}
          />
        ) : (
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[300px,1fr]">
            <motion.aside
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35 }}
              className="xl:sticky xl:top-6 xl:self-start"
            >
              <ItineraryHistoryPanel
                items={history}
                activeToken={activeHistoryToken}
                activeGeneratedAt={result?.generated_at}
                onSelect={loadHistoryEntry}
                onDelete={handleDeleteHistory}
                onClear={handleClearHistory}
              />
            </motion.aside>

            <AnimatePresence mode="wait">
              {!loading && !result && (
                <motion.div
                  key="input"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  transition={{ duration: 0.45 }}
                >
                  <InputForm form={form} setForm={setForm} onSubmit={submitTrip} />
                </motion.div>
              )}

              {loading && (
                <motion.div
                  key="progress"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  transition={{ duration: 0.45 }}
                >
                  <PipelineProgress progress={progress} />
                </motion.div>
              )}

              {!loading && result && (
                <motion.section
                  key="result"
                  variants={resultContainer}
                  initial="hidden"
                  animate="show"
                  className="space-y-6"
                >
                  <motion.div variants={revealItem} className="panel-surface rounded-3xl p-6">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-gold/75">Generated Itinerary</p>
                        <h2 className="font-display text-4xl text-parchment">{result.destination}</h2>
                        <p className="mt-1 text-sm text-parchment/75">
                          {result.days} days in {result.month} • {result.budget_level} • {result.travel_style}
                        </p>
                      </div>
                      <button
                        onClick={reset}
                        className="rounded-lg border border-gold/35 bg-surface/85 px-4 py-2 text-sm text-parchment shadow-soft transition hover:-translate-y-0.5 hover:border-gold"
                      >
                        Plan Another Trip
                      </button>
                    </div>

                    {Array.isArray(result.notices) && result.notices.length > 0 && (
                      <div className="mt-4 rounded-xl border border-amber-500/35 bg-amber-200/55 p-3 text-sm text-amber-900">
                        {result.notices.join(" | ")}
                      </div>
                    )}
                  </motion.div>

                  <DataSourceSummary result={result} />

                  <motion.section variants={revealItem} className="heavy-section">
                    <h3 className="mb-3 flex items-center gap-2 font-display text-3xl text-parchment">
                      <MapPinned size={22} className="text-gold" /> Day-by-Day Plan
                    </h3>
                    <motion.div
                      initial="hidden"
                      animate="show"
                      variants={{
                        hidden: {},
                        show: { transition: { staggerChildren: 0.05 } },
                      }}
                      className="space-y-3"
                    >
                      {(result.itinerary || []).map((day, idx) => (
                        <DayCard key={`day-${day.day || idx}`} dayData={day} defaultOpen={idx === 0} />
                      ))}
                    </motion.div>
                  </motion.section>

                  <motion.div variants={revealItem} className="heavy-section">
                    <HotelSection hotels={result.hotels} />
                  </motion.div>

                  <motion.section variants={revealItem} className="heavy-section">
                    <h3 className="mb-3 font-display text-3xl text-parchment">Hidden Gems</h3>
                    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
                      {(result.hidden_gems || []).map((gem, idx) => (
                        <HiddenGemCard key={`${gem?.name || "gem"}-${idx}`} gem={gem} />
                      ))}
                    </div>
                  </motion.section>

                  <motion.div variants={revealItem} className="heavy-section">
                    <TipsPanel result={result} />
                  </motion.div>
                </motion.section>
              )}
            </AnimatePresence>
          </div>
        )}
        </div>
      </main>
    </MotionConfig>
  );
}
