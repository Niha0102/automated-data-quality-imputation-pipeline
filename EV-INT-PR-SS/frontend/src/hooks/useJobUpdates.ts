import { useEffect, useRef } from "react";
import { useJobStore } from "@/store/jobStore";
import { useAuthStore } from "@/store/authStore";

export function useJobUpdates(jobId: string | undefined) {
  const updateJob = useJobStore((s) => s.updateJob);
  const token = useAuthStore((s) => s.token);
  const wsRef = useRef<WebSocket | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId || !token) return;

    const wsUrl = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/jobs/${jobId}?token=${token}`;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            if (!data.ping) updateJob(jobId, data);
          } catch {}
        };

        ws.onerror = () => startPolling();
        ws.onclose = () => startPolling();
      } catch {
        startPolling();
      }
    };

    const startPolling = () => {
      if (pollRef.current) return;
      pollRef.current = setInterval(async () => {
        try {
          const res = await fetch(`/api/v1/jobs/${jobId}/status`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (res.ok) {
            const data = await res.json();
            updateJob(jobId, data);
            if (data.status === "COMPLETED" || data.status === "FAILED") {
              clearInterval(pollRef.current!);
              pollRef.current = null;
            }
          }
        } catch {}
      }, 5000);
    };

    connect();

    return () => {
      wsRef.current?.close();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [jobId, token, updateJob]);
}
