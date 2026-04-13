import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, Backpack, ChefHat, Coins, ShieldAlert } from "lucide-react";
import { useState } from "react";

export default function TipsPanel({ result }) {
  const [warningsOpen, setWarningsOpen] = useState(true);

  const warnings = Array.isArray(result?.warnings) ? result.warnings : [];
  const mustEat = Array.isArray(result?.must_eat) ? result.must_eat : [];
  const culturalTips = Array.isArray(result?.cultural_tips) ? result.cultural_tips : [];
  const packing = Array.isArray(result?.packing) ? result.packing : [];
  const budget = result?.budget_breakdown || {};

  return (
    <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <article className="panel-surface rounded-2xl p-5">
        <button
          className="mb-3 flex w-full items-center justify-between text-left"
          onClick={() => setWarningsOpen((value) => !value)}
        >
          <h4 className="flex items-center gap-2 font-display text-2xl text-parchment">
            <ShieldAlert size={20} className="text-amber-300" /> Warnings
          </h4>
          <span className="text-xs uppercase tracking-[0.15em] text-parchment/60">Toggle</span>
        </button>

        <AnimatePresence initial={false}>
          {warningsOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.28 }}
              className="space-y-3"
            >
              {warnings.map((item, idx) => (
                <div
                  key={`${item?.issue || "issue"}-${idx}`}
                  className="rounded-lg border-l-4 border-amber-500 bg-amber-100/70 p-3"
                >
                  <p className="font-medium text-amber-900">{item?.issue || "Travel advisory"}</p>
                  <p className="mt-1 text-sm text-parchment/85">{item?.advice || "Stay alert and verify local updates."}</p>
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </article>

      <article className="panel-surface rounded-2xl p-5">
        <h4 className="mb-3 flex items-center gap-2 font-display text-2xl text-parchment">
          <ChefHat size={20} className="text-emerald" /> Must Eat
        </h4>
        <div className="space-y-2">
          {mustEat.map((food, idx) => (
            <div key={`${food?.dish || "dish"}-${idx}`} className="rounded-lg border border-gold/20 bg-surface/80 p-3 shadow-soft">
              <p className="font-medium text-gold">{food?.dish || "Local dish"}</p>
              <p className="text-sm text-parchment/80">{food?.where_to_find || "Popular food lane"}</p>
              <p className="text-xs text-emerald">{food?.approx_cost || "Estimated cost varies"}</p>
            </div>
          ))}
        </div>
      </article>

      <article className="panel-surface rounded-2xl p-5">
        <h4 className="mb-3 flex items-center gap-2 font-display text-2xl text-parchment">
          <AlertTriangle size={20} className="text-gold" /> Cultural Tips
        </h4>
        <ul className="space-y-2 text-sm text-parchment/85">
          {culturalTips.map((tip, idx) => (
            <li key={`${tip}-${idx}`} className="rounded-lg border border-gold/15 bg-surface/80 p-3 shadow-soft">
              {tip}
            </li>
          ))}
        </ul>
      </article>

      <article className="panel-surface rounded-2xl p-5">
        <h4 className="mb-3 flex items-center gap-2 font-display text-2xl text-parchment">
          <Backpack size={20} className="text-emerald" /> Packing Essentials
        </h4>
        <div className="mb-4 flex flex-wrap gap-2">
          {packing.map((item, idx) => (
            <span
              key={`${item}-${idx}`}
              className="rounded-full border border-emerald/45 bg-emerald/10 px-3 py-1 text-xs font-medium text-emerald"
            >
              {item}
            </span>
          ))}
        </div>

        <h5 className="mb-2 flex items-center gap-2 text-sm uppercase tracking-[0.15em] text-gold">
          <Coins size={14} /> Budget Breakdown
        </h5>
        <div className="overflow-hidden rounded-xl border border-gold/20">
          <table className="w-full text-left text-sm">
            <thead className="bg-gold text-ink">
              <tr>
                <th className="px-3 py-2">Category</th>
                <th className="px-3 py-2">Estimate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gold/10 bg-surface/80 text-parchment/85">
              {Object.entries(budget).map(([key, value]) => (
                <tr key={key}>
                  <td className="px-3 py-2">{key.replaceAll("_", " ")}</td>
                  <td className="px-3 py-2">{String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}
