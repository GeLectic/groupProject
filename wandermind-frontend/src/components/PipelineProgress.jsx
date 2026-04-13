import { motion } from "framer-motion";
import { CheckCircle2, Database, Search, ShieldCheck, Sparkles, Telescope } from "lucide-react";

import StreamingText from "./StreamingText";

const stageMap = [
  { stage: 1, label: "Fetching YouTube vlogs...", icon: Search },
  { stage: 2, label: "Mining Reddit & Quora...", icon: Telescope },
  { stage: 3, label: "Building knowledge base...", icon: Database },
  { stage: 4, label: "Verifying information...", icon: ShieldCheck },
  { stage: 5, label: "Crafting your itinerary...", icon: Sparkles },
  { stage: 6, label: "Done!", icon: CheckCircle2 },
];

const stageStops = [6, 24, 42, 60, 78, 94];

const routePoints = [
  { p: 0, x: 2, y: 72 },
  { p: 18, x: 18, y: 24 },
  { p: 36, x: 36, y: 52 },
  { p: 54, x: 56, y: 76 },
  { p: 72, x: 76, y: 42 },
  { p: 90, x: 92, y: 52 },
  { p: 100, x: 98, y: 50 },
];

function routePosition(progressValue) {
  const clamped = Math.max(0, Math.min(100, progressValue));
  for (let i = 0; i < routePoints.length - 1; i += 1) {
    const start = routePoints[i];
    const end = routePoints[i + 1];
    if (clamped >= start.p && clamped <= end.p) {
      const span = end.p - start.p || 1;
      const t = (clamped - start.p) / span;
      return {
        x: start.x + (end.x - start.x) * t,
        y: start.y + (end.y - start.y) * t,
      };
    }
  }
  return { x: 98, y: 50 };
}

export default function PipelineProgress({ progress }) {
  const routeProgress = Math.max(0, Math.min(100, Number(progress?.progress || 0)));
  const marker = routePosition(routeProgress);
  const isDone = Number(progress?.stage || 0) >= 6;

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="panel-surface mx-auto max-w-4xl rounded-3xl p-6 sm:p-8"
    >
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h3 className="font-display text-3xl text-parchment">Composing Your Journey</h3>
        <div className="rounded-full border border-gold/35 bg-gold/10 px-4 py-1 text-sm text-gold shadow-soft">
          {routeProgress}% complete
        </div>
      </div>

      <div className="heavy-section relative mb-8 overflow-hidden rounded-2xl border border-gold/20 bg-mist/70 px-3 py-4 shadow-soft">
        <motion.div
          className="performance-layer pointer-events-none absolute inset-y-0 -left-1/2 w-1/2 bg-gradient-to-r from-transparent via-white/55 to-transparent"
          animate={{ x: ["0%", "300%"] }}
          transition={{ duration: 7.2, repeat: Infinity, ease: "linear" }}
        />

        <svg viewBox="0 0 1000 180" className="h-40 w-full" preserveAspectRatio="none">
          <defs>
            <linearGradient id="routeBase" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="rgba(187, 138, 46, 0.25)" />
              <stop offset="100%" stopColor="rgba(31, 154, 136, 0.25)" />
            </linearGradient>
            <linearGradient id="routeFill" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#bb8a2e" />
              <stop offset="45%" stopColor="#d6a64b" />
              <stop offset="100%" stopColor="#1f9a88" />
            </linearGradient>
          </defs>

          <path
            d="M 20 120 C 140 28, 240 28, 350 96 S 560 156, 690 104 S 860 36, 980 90"
            fill="none"
            stroke="url(#routeBase)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray="8 8"
          />

          <motion.path
            d="M 20 120 C 140 28, 240 28, 350 96 S 560 156, 690 104 S 860 36, 980 90"
            fill="none"
            stroke="url(#routeFill)"
            strokeWidth="8"
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: routeProgress / 100 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        </svg>

        {stageMap.map((item, idx) => {
          const isComplete = (progress.stage || 0) > item.stage;
          const isActive = (progress.stage || 0) === item.stage;
          const Icon = item.icon;
          const stopPoint = routePosition(stageStops[idx]);

          return (
            <motion.div
              key={item.stage}
              className="absolute"
              style={{
                left: `calc(${stopPoint.x}% - 12px)`,
                top: `calc(${stopPoint.y}% - 12px)`,
              }}
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: idx * 0.08 }}
            >
              <div
                className={`grid h-6 w-6 place-items-center rounded-full border text-[10px] ${
                  isComplete
                    ? "border-emerald bg-emerald/20 text-emerald"
                    : isActive
                      ? "border-gold bg-gold/20 text-gold"
                      : "border-gold/35 bg-white/80 text-parchment/55"
                }`}
              >
                <Icon size={12} />
              </div>
            </motion.div>
          );
        })}

        <motion.div
          className="performance-layer absolute h-5 w-5 rounded-full bg-gradient-to-br from-gold via-amber-300 to-emerald shadow-[0_0_14px_rgba(187,138,46,0.42)]"
          style={{ left: `calc(${marker.x}% - 10px)`, top: `calc(${marker.y}% - 10px)` }}
          transition={{ type: "spring", stiffness: 90, damping: 18 }}
        >
          {!isDone ? (
            <motion.span
              className="absolute inset-0 rounded-full border border-gold/50"
              animate={{ scale: [1, 1.7, 1], opacity: [0.55, 0.08, 0.55] }}
              transition={{ duration: 2.1, repeat: Infinity }}
            />
          ) : null}
        </motion.div>

        {!isDone ? (
          <motion.div
            className="performance-layer absolute h-2.5 w-2.5 rounded-full bg-gold/30"
            style={{
              left: `calc(${Math.max(0, marker.x - 1.6)}% - 5px)`,
              top: `calc(${Math.min(100, marker.y + 1.1)}% - 5px)`,
            }}
            animate={{ opacity: [0.26, 0.08, 0.26], scale: [1, 0.86, 1] }}
            transition={{ duration: 1.8, repeat: Infinity }}
          />
        ) : null}
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {stageMap.map((item, idx) => {
          const Icon = item.icon;
          const isComplete = (progress.stage || 0) > item.stage;
          const isActive = (progress.stage || 0) === item.stage;

          return (
            <motion.div
              key={item.stage}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.06, duration: 0.32 }}
              className={`stage-card relative rounded-xl px-4 py-3 transition ${isActive ? "stage-card-active" : ""}`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`stage-node relative z-10 ${
                    isComplete ? "border-emerald bg-emerald/25" : isActive ? "border-gold bg-gold/25" : ""
                  }`}
                >
                  {isActive && (
                    <motion.span
                      className="absolute inset-0 rounded-full bg-gold/25"
                      animate={{ scale: [1, 1.6, 1], opacity: [0.6, 0, 0.6] }}
                      transition={{ duration: 1.6, repeat: Infinity }}
                    />
                  )}
                </div>
                <Icon
                  size={18}
                  className={isComplete ? "text-emerald" : isActive ? "text-gold" : "text-parchment/40"}
                />
                <div className="text-sm text-parchment/85">
                  {isActive ? (
                    <StreamingText text={progress.label || item.label} speed={14} className="text-parchment" />
                  ) : (
                    item.label
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.section>
  );
}
