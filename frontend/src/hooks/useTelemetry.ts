import { useState, useEffect, useRef } from 'react';
import { TelemetryPayload } from '../types/network';

export function useTelemetry() {
  const [telemetry, setTelemetry] = useState<TelemetryPayload | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const backoffDelayRef = useRef<number>(1000);
  const isMountedRef = useRef<boolean>(true);

  useEffect(() => {
    isMountedRef.current = true;

    function getWebSocketUrl(): string {
      const customUrl = (import.meta as any).env?.VITE_WS_URL;
      if (customUrl) return customUrl;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // Use relative host through Vite dev server proxy or Nginx reverse proxy
      return `${protocol}//${window.location.host}/ws/network`;
    }

    function connect() {
      if (!isMountedRef.current) return;

      // Close previous socket if still open to prevent duplicate streams
      if (wsRef.current) {
        try {
          wsRef.current.onclose = null;
          wsRef.current.onerror = null;
          wsRef.current.close();
        } catch {
          // ignore
        }
        wsRef.current = null;
      }

      const wsUrl = getWebSocketUrl();
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        setIsConnected(true);
        backoffDelayRef.current = 1000; // Reset exponential backoff on successful connection
      };

      ws.onmessage = (event) => {
        if (!isMountedRef.current) return;
        try {
          const data: TelemetryPayload = JSON.parse(event.data);
          setTelemetry(data);
          setHistory((prev) => {
            const next = [
              ...prev,
              {
                time: new Date(data.timestamp).toLocaleTimeString(),
                downKbps: Math.round(data.bandwidth.download_bytes_per_sec / 1024),
                upKbps: Math.round(data.bandwidth.upload_bytes_per_sec / 1024),
                ping: data.ping_ms || 0
              }
            ];
            return next.slice(-40);
          });
        } catch (e) {
          console.debug('Telemetry frame JSON parse error:', e);
        }
      };

      ws.onclose = () => {
        if (!isMountedRef.current) return;
        setIsConnected(false);
        wsRef.current = null;

        // Exponential backoff retry (1s -> 1.5s -> 2.25s -> max 10s)
        const delay = backoffDelayRef.current;
        backoffDelayRef.current = Math.min(delay * 1.5, 10000);

        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        reconnectTimeoutRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        // Close triggers onclose where backoff logic executes
        try {
          ws.close();
        } catch {
          // ignore
        }
      };
    }

    connect();

    return () => {
      isMountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        try {
          wsRef.current.onclose = null;
          wsRef.current.onerror = null;
          wsRef.current.close();
        } catch {
          // ignore
        }
        wsRef.current = null;
      }
    };
  }, []);

  return { telemetry, history, isConnected };
}
