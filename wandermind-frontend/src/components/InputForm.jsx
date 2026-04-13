import { motion } from "framer-motion";
import { CalendarDays, Compass, Gem, MapPinned, Wallet } from "lucide-react";

const months = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export default function InputForm({ form, setForm, onSubmit }) {
  const update = (field) => (event) => {
    const value = field === "days" ? Number(event.target.value) : event.target.value;
    setForm({ [field]: value });
  };

  const inputClassName =
    "field-shell w-full rounded-xl px-4 py-3 outline-none transition duration-300";

  return (
    <motion.form
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(form);
      }}
      className="panel-surface mx-auto max-w-3xl rounded-3xl p-6 sm:p-8"
    >
      <div className="mb-8">
        <p className="mb-3 text-sm uppercase tracking-[0.24em] text-gold/80">WanderMind Intake</p>
        <h2 className="font-display text-3xl text-parchment sm:text-4xl">Craft a White-Glove Travel Plan</h2>
        <p className="mt-2 text-sm text-parchment/70">
          Tell us where and when you are going. WanderMind orchestrates the rest with polished, source-backed planning.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <label className="col-span-1 sm:col-span-2">
          <span className="mb-2 flex items-center gap-2 text-sm text-parchment/80">
            <MapPinned size={16} className="text-gold" /> Destination
          </span>
          <input
            required
            value={form.destination}
            onChange={update("destination")}
            placeholder="Manali, Himachal Pradesh"
            className={inputClassName}
          />
        </label>

        <label>
          <span className="mb-2 flex items-center gap-2 text-sm text-parchment/80">
            <CalendarDays size={16} className="text-gold" /> Trip Duration (days)
          </span>
          <input
            type="number"
            min={1}
            max={21}
            value={form.days}
            onChange={update("days")}
            className={inputClassName}
          />
        </label>

        <label>
          <span className="mb-2 flex items-center gap-2 text-sm text-parchment/80">
            <CalendarDays size={16} className="text-gold" /> Travel Month
          </span>
          <select
            value={form.month}
            onChange={update("month")}
            className={inputClassName}
          >
            {months.map((month) => (
              <option key={month} value={month}>
                {month}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span className="mb-2 flex items-center gap-2 text-sm text-parchment/80">
            <Wallet size={16} className="text-gold" /> Budget Level
          </span>
          <select
            value={form.budget_level}
            onChange={update("budget_level")}
            className={inputClassName}
          >
            <option value="budget">Budget</option>
            <option value="mid-range">Mid-Range</option>
            <option value="luxury">Luxury</option>
          </select>
        </label>

        <label>
          <span className="mb-2 flex items-center gap-2 text-sm text-parchment/80">
            <Compass size={16} className="text-gold" /> Travel Style
          </span>
          <select
            value={form.travel_style}
            onChange={update("travel_style")}
            className={inputClassName}
          >
            <option value="adventure">Adventure</option>
            <option value="culture">Culture</option>
            <option value="relaxation">Relaxation</option>
            <option value="foodie">Foodie</option>
          </select>
        </label>
      </div>

      <button
        type="submit"
        className="mt-8 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-gold via-amber-300 to-gold px-5 py-3 font-semibold text-ink shadow-gold transition duration-300 hover:-translate-y-0.5 hover:brightness-105"
      >
        <Gem size={18} />
        Generate Itinerary
      </button>
    </motion.form>
  );
}
