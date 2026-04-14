import { motion } from "framer-motion";
import { KeyRound, LogIn, Mail, ShieldCheck, UserPlus } from "lucide-react";
import { useMemo, useState } from "react";

export default function AuthPanel({ loading, error, onLogin, onRegister }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [localError, setLocalError] = useState("");

  const isRegister = mode === "register";

  const canSubmit = useMemo(() => {
    if (!email || !password) return false;
    if (password.length < 8) return false;
    if (isRegister && confirmPassword !== password) return false;
    return true;
  }, [confirmPassword, email, isRegister, password]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLocalError("");

    if (!canSubmit) {
      setLocalError("Enter a valid email and a password with at least 8 characters.");
      return;
    }

    if (isRegister) {
      await onRegister({ email, password });
      return;
    }

    await onLogin({ email, password });
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="panel-surface mx-auto max-w-xl rounded-3xl p-6 sm:p-8"
    >
      <div className="mb-6">
        <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-gold/75">
          <ShieldCheck size={14} /> Secure Access
        </p>
        <h2 className="font-display text-3xl text-parchment">Sign In To Your Account</h2>
        <p className="mt-2 text-sm text-parchment/70">
          Your generated itineraries are attached to your account and available in the sidebar on future sessions.
        </p>
      </div>

      <div className="mb-5 flex gap-2 rounded-full border border-gold/30 bg-surface/70 p-1">
        <button
          type="button"
          onClick={() => {
            setMode("login");
            setLocalError("");
          }}
          className={`flex-1 rounded-full px-3 py-2 text-sm font-medium transition ${
            !isRegister ? "bg-gold text-ink" : "text-parchment/75 hover:text-parchment"
          }`}
        >
          Login
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("register");
            setLocalError("");
          }}
          className={`flex-1 rounded-full px-3 py-2 text-sm font-medium transition ${
            isRegister ? "bg-gold text-ink" : "text-parchment/75 hover:text-parchment"
          }`}
        >
          Register
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <label className="block">
          <span className="mb-2 flex items-center gap-2 text-sm text-parchment/80">
            <Mail size={15} className="text-gold" /> Email
          </span>
          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="field-shell w-full rounded-xl px-4 py-3 outline-none"
            placeholder="you@example.com"
          />
        </label>

        <label className="block">
          <span className="mb-2 flex items-center gap-2 text-sm text-parchment/80">
            <KeyRound size={15} className="text-gold" /> Password
          </span>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="field-shell w-full rounded-xl px-4 py-3 outline-none"
            placeholder="At least 8 characters"
          />
        </label>

        {isRegister ? (
          <label className="block">
            <span className="mb-2 flex items-center gap-2 text-sm text-parchment/80">
              <KeyRound size={15} className="text-gold" /> Confirm Password
            </span>
            <input
              type="password"
              required
              minLength={8}
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              className="field-shell w-full rounded-xl px-4 py-3 outline-none"
              placeholder="Repeat password"
            />
          </label>
        ) : null}

        {localError ? (
          <div className="rounded-xl border border-rose-400/45 bg-rose-100/65 px-3 py-2 text-sm text-rose-900">
            {localError}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-xl border border-rose-400/45 bg-rose-100/65 px-3 py-2 text-sm text-rose-900">
            {error}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={loading || !canSubmit}
          className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-gold via-amber-300 to-gold px-5 py-3 font-semibold text-ink shadow-gold transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-55"
        >
          {isRegister ? <UserPlus size={17} /> : <LogIn size={17} />}
          {loading ? "Please wait..." : isRegister ? "Create Account" : "Sign In"}
        </button>
      </form>
    </motion.section>
  );
}
