import { Building2, Coins, Star } from "lucide-react";
import { useMemo, useState } from "react";

const tabLabels = {
  budget: "Budget",
  mid_range: "Mid-Range",
  luxury: "Luxury",
};

function _extractNumeric(value) {
  if (typeof value === "number") return value;
  if (typeof value !== "string") return null;
  const cleaned = value.replaceAll(",", " ");
  const match = cleaned.match(/\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : null;
}

function priceInINR(hotel) {
  const inr = hotel?.est_cost_per_night_inr;
  if (typeof inr === "string" && inr.trim()) {
    return inr;
  }
  if (typeof inr === "number") {
    return `INR ${Math.round(inr).toLocaleString("en-IN")}`;
  }

  const usd = hotel?.est_cost_per_night_usd;
  const usdNumeric = _extractNumeric(usd);
  if (usdNumeric !== null && !Number.isNaN(usdNumeric)) {
    const converted = Math.round(usdNumeric * 83);
    return `INR ${converted.toLocaleString("en-IN")}`;
  }

  return "INR Estimated";
}

export default function HotelSection({ hotels }) {
  const [active, setActive] = useState("budget");

  const normalized = useMemo(
    () => ({
      budget: Array.isArray(hotels?.budget) ? hotels.budget : [],
      mid_range: Array.isArray(hotels?.mid_range) ? hotels.mid_range : [],
      luxury: Array.isArray(hotels?.luxury) ? hotels.luxury : [],
    }),
    [hotels]
  );

  return (
    <section className="panel-surface heavy-section rounded-3xl p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-display text-3xl text-parchment">Hotel Picks</h3>
        <p className="text-xs uppercase tracking-[0.16em] text-gold/75">Estimated Pricing</p>
      </div>

      <div className="mb-5 flex flex-wrap gap-2">
        {Object.entries(tabLabels).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setActive(key)}
            className={`rounded-full px-4 py-2 text-sm transition ${
              active === key
                ? "bg-gold text-ink shadow-soft"
                : "border border-gold/30 bg-surface/80 text-parchment hover:-translate-y-0.5 hover:border-gold"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {normalized[active].map((hotel, idx) => {
          const hasMixed = String(hotel?.cons || "").toLowerCase().includes("mixed");

          return (
            <div key={`${hotel?.name}-${idx}`} className="group hotel-flip-card [perspective:1000px]">
              <div className="hotel-flip-inner relative h-56 rounded-2xl transition-transform duration-500 [transform-style:preserve-3d] motion-safe:group-hover:[transform:rotateY(180deg)]">
                <div className="hotel-front-face absolute inset-0 rounded-2xl border border-gold/30 bg-surface/88 p-4 shadow-soft [backface-visibility:hidden]">
                  <div className="mb-3 flex items-center justify-between">
                    <Building2 className="text-gold" size={18} />
                    {hasMixed && (
                      <span className="rounded-full bg-amber-200/70 px-2 py-1 text-xs text-amber-900">Mixed Reviews</span>
                    )}
                  </div>
                  <h4 className="font-display text-xl text-parchment">{hotel?.name || "Suggested Stay"}</h4>
                  <p className="mt-1 text-sm text-parchment/70">{hotel?.area || "Popular area"}</p>
                  <p className="mt-3 flex items-center gap-2 text-sm text-emerald">
                    <Coins size={14} />
                    {priceInINR(hotel)} / night
                  </p>
                  <p className="mt-2 text-sm text-parchment/80">Best for: {hotel?.best_for || "General travelers"}</p>
                </div>

                <div className="hotel-back-face absolute inset-0 rounded-2xl border border-gold/30 bg-mist p-4 shadow-soft [backface-visibility:hidden] [transform:rotateY(180deg)]">
                  <p className="mb-2 flex items-center gap-2 text-sm text-gold">
                    <Star size={14} /> Pros
                  </p>
                  <p className="mb-4 text-sm text-parchment/85">{hotel?.pros || "No pros provided"}</p>
                  <p className="mb-2 text-sm text-rose-700">Cons</p>
                  <p className="text-sm text-parchment/75">{hotel?.cons || "No notable cons"}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
