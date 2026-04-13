import { AnimatePresence, motion } from "framer-motion";
import { CalendarDays, Clock3, History, MapPinned, Trash2 } from "lucide-react";

function formatCreatedAt(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function resolveHistoryToken(item, index) {
  if (item?.id) {
    return String(item.id);
  }

  if (item?.data?.generated_at) {
    return String(item.data.generated_at);
  }

  if (item?.createdAt) {
    return `created-${item.createdAt}-${index}`;
  }

  return `legacy-${index}`;
}

export default function ItineraryHistoryPanel({
  items,
  activeToken,
  activeGeneratedAt,
  onSelect,
  onDelete,
  onClear,
}) {
  const hasItems = Array.isArray(items) && items.length > 0;

  return (
    <section className="panel-surface shimmer-border rounded-3xl p-4 sm:p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2 text-[#53371a]">
          <History className="h-4 w-4 text-[#af7422]" />
          <h2 className="truncate font-[Sora] text-sm font-semibold uppercase tracking-[0.14em]">
            Recent Itineraries
          </h2>
        </div>
        {hasItems ? (
          <button
            onClick={onClear}
            className="rounded-full border border-[#c89b5f]/45 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[#8f5f25] transition hover:bg-[#fff5df]"
          >
            Clear
          </button>
        ) : null}
      </div>

      {!hasItems ? (
        <div className="rounded-2xl border border-dashed border-[#d9bd8c]/55 bg-white/70 px-4 py-5 text-sm text-[#7b5b34]">
          Your generated trips will appear here. Select any itinerary to open it again.
        </div>
      ) : (
        <ul className="max-h-[68vh] space-y-2 overflow-y-auto pr-1">
          <AnimatePresence initial={false}>
            {items.map((item, index) => {
              const itemToken = resolveHistoryToken(item, index);
              const activeByToken = String(itemToken) === String(activeToken || "");
              const activeByGeneratedAt = String(item?.data?.generated_at || "") === String(activeGeneratedAt || "");
              const active = activeByToken || activeByGeneratedAt;

              return (
                <motion.li
                  key={itemToken}
                  layout="position"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className={`group rounded-2xl border p-3 transition ${
                    active
                      ? "border-[#bf8a40]/65 bg-[#fff4de]/92 shadow-[0_10px_25px_rgba(181,129,53,0.18)]"
                      : "border-[#dec8a4]/65 bg-white/76 hover:border-[#caa06a]"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <button
                      type="button"
                      onClick={() => onSelect(itemToken)}
                      className="flex-1 text-left"
                    >
                      <div className="mb-1 flex items-start gap-2 text-[#5b3d19]">
                        <MapPinned className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#b3731f]" />
                        <p className="font-[Sora] text-sm font-semibold leading-snug">
                          {item.destination || item?.data?.destination || "Untitled itinerary"}
                        </p>
                      </div>

                      <div className="mb-2 flex flex-wrap gap-1.5 text-[11px] uppercase tracking-[0.09em] text-[#7c5a32]">
                        {(item.days ?? item?.data?.days) ? (
                          <span className="rounded-full bg-[#f7ead4] px-2 py-0.5">{item.days ?? item?.data?.days} Days</span>
                        ) : null}
                        {(item.month || item?.data?.month) ? (
                          <span className="rounded-full bg-[#f7ead4] px-2 py-0.5">{item.month || item?.data?.month}</span>
                        ) : null}
                        {(item.travel_style || item?.data?.travel_style) ? (
                          <span className="rounded-full bg-[#f7ead4] px-2 py-0.5">{item.travel_style || item?.data?.travel_style}</span>
                        ) : null}
                      </div>

                      <div className="flex items-center gap-1.5 text-[11px] text-[#8f6c43]">
                        <CalendarDays className="h-3 w-3" />
                        <span>{formatCreatedAt(item.createdAt || item?.data?.generated_at)}</span>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => onDelete(itemToken)}
                      className="rounded-full border border-transparent p-1.5 text-[#9b6f36] transition hover:border-[#d2b083] hover:bg-[#fff0d6] hover:text-[#7a4b14]"
                      aria-label="Delete itinerary"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </motion.li>
              );
            })}
          </AnimatePresence>
        </ul>
      )}

      {hasItems ? (
        <div className="mt-3 flex items-center gap-2 text-[11px] uppercase tracking-[0.12em] text-[#8f6f3f]">
          <Clock3 className="h-3 w-3" />
          <span>Saved in this browser</span>
        </div>
      ) : null}
    </section>
  );
}
