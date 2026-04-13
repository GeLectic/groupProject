import { motion } from "framer-motion";
import { Gem, Navigation2 } from "lucide-react";
import { memo } from "react";

function HiddenGemCard({ gem }) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      whileHover={{ y: -2 }}
      className="shimmer-border panel-surface heavy-section relative rounded-2xl p-4"
    >
      <div className="mb-2 flex items-center gap-2 text-gold">
        <Gem size={16} />
        <h4 className="font-display text-xl">{gem?.name || "Hidden Spot"}</h4>
      </div>
      <p className="text-sm text-parchment/85">{gem?.why_special || "Special details unavailable."}</p>
      <p className="mt-3 flex items-center gap-2 text-xs text-emerald/90">
        <Navigation2 size={12} />
        {gem?.how_to_get_there || "Ask locals for best route"}
      </p>
    </motion.article>
  );
}

export default memo(HiddenGemCard);
