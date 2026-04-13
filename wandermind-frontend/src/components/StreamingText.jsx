import { useEffect, useMemo, useState } from "react";

export default function StreamingText({ text = "", speed = 18, className = "" }) {
  const safeText = useMemo(() => String(text || ""), [text]);
  const [visible, setVisible] = useState("");

  useEffect(() => {
    setVisible("");
    if (!safeText) return;

    let i = 0;
    const timer = setInterval(() => {
      i += 1;
      setVisible(safeText.slice(0, i));
      if (i >= safeText.length) {
        clearInterval(timer);
      }
    }, speed);

    return () => clearInterval(timer);
  }, [safeText, speed]);

  return <p className={className}>{visible}</p>;
}
