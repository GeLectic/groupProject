import { Clock3, MapPin, Utensils } from "lucide-react";

export default function TimelineBlock({ title, block }) {
  if (!block || typeof block !== "object") return null;

  return (
    <div className="rounded-xl border border-gold/20 bg-surface/75 p-4 shadow-soft">
      <h5 className="mb-2 font-display text-xl text-gold">{title}</h5>
      <div className="space-y-2 text-sm text-parchment/90">
        {block.time && (
          <p className="flex items-center gap-2">
            <Clock3 size={14} className="text-emerald" />
            {block.time}
          </p>
        )}
        {block.location && (
          <p className="flex items-center gap-2">
            <MapPin size={14} className="text-gold" />
            {block.location}
          </p>
        )}
        {block.activity && <p>{block.activity}</p>}
        {block.food_nearby && (
          <p className="flex items-center gap-2 text-parchment/80">
            <Utensils size={14} className="text-emerald" />
            {block.food_nearby}
          </p>
        )}
        {block.dinner_spot && <p className="text-parchment/80">Dinner: {block.dinner_spot}</p>}
        {block.travel_time_from_hotel && <p className="text-parchment/70">Travel: {block.travel_time_from_hotel}</p>}
        {block.tip && <p className="text-parchment/70">Tip: {block.tip}</p>}
      </div>
    </div>
  );
}
