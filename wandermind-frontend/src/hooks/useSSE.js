import { API_BASE_URL, getAuthToken } from "../api/client";

export function useSSE() {
  const streamItinerary = async ({ payload, onEvent, onError }) => {
    const controller = new AbortController();

    try {
      const token = getAuthToken();
      const headers = { "Content-Type": "application/json" };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE_URL}/api/generate-itinerary`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const event of events) {
          const dataLine = event
            .split("\n")
            .find((line) => line.trim().startsWith("data:"));

          if (!dataLine) continue;

          const jsonString = dataLine.replace(/^data:\s*/, "").trim();
          if (!jsonString) continue;

          try {
            const parsed = JSON.parse(jsonString);
            onEvent?.(parsed);
          } catch {
            // Ignore malformed chunks and keep stream alive.
          }
        }
      }
    } catch (error) {
      onError?.(error instanceof Error ? error.message : "Streaming error");
    }

    return () => controller.abort();
  };

  return { streamItinerary };
}
