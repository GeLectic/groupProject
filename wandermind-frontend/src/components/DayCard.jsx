import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, MapPinned, Timer } from "lucide-react";
import { memo, useState } from "react";

import TimelineBlock from "./TimelineBlock";

function DayCard({ dayData, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <motion.article
      className="panel-surface heavy-section overflow-hidden rounded-2xl"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24, ease: "easeOut" }}
    >
      <button
        onClick={() => setOpen((value) => !value)}
        className={`flex w-full items-center justify-between px-5 py-4 text-left transition-transform duration-200 hover:-translate-y-0.5 ${
          open ? "border-b border-gold/20" : ""
        }`}
      >
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-gold/75">Day {dayData.day}</p>
          <h4 className="font-display text-2xl text-parchment">{dayData.theme || "Planned Day"}</h4>
        </div>
        <ChevronDown
          className={`text-gold transition-transform ${open ? "rotate-180" : "rotate-0"}`}
          size={20}
        />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="px-5 pb-5"
          >
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <TimelineBlock title="Morning" block={dayData.morning} />
              <TimelineBlock title="Afternoon" block={dayData.afternoon} />
              <TimelineBlock title="Evening" block={dayData.evening} />
              <TimelineBlock title="Night" block={dayData.night} />
            </div>

            {Array.isArray(dayData.travel_times) && dayData.travel_times.length > 0 && (
              <div className="mt-4 rounded-xl border border-emerald/30 bg-emerald/10 p-4">
                <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-emerald">
                  <Timer size={14} /> Estimated Transfers
                </p>
                <div className="space-y-1 text-sm text-parchment/85">
                  {dayData.travel_times.map((item, idx) => (
                    <p key={`${item.from}-${item.to}-${idx}`}>
                      {item.from} {"->"} {item.to}: {item.minutes} min ({item.mode})
                    </p>
                  ))}
                </div>
              </div>
            )}

            {Array.isArray(dayData.opening_hours_warnings) && dayData.opening_hours_warnings.length > 0 && (
              <div className="mt-4 rounded-xl border border-amber-500/35 bg-amber-200/50 p-4">
                <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-800">
                  <MapPinned size={14} /> Opening Hour Warnings
                </p>
                <ul className="space-y-1 text-sm text-parchment/90">
                  {dayData.opening_hours_warnings.map((warning, idx) => (
                    <li key={`${warning}-${idx}`}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            {dayData.day_notes && <p className="mt-4 text-sm text-parchment/70">{dayData.day_notes}</p>}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}

export default memo(DayCard);
