import { useState, useEffect, useRef } from 'react';
import { TelemetryPayload } from '../types/network';

export function useTelemetry() {
  const [telemetry, setTelemetry] = useState<TelemetryPayload | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  useEffect(() => {
    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/network`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
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
          console.error('Error parsing telemetry JSON:', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Retry connection after 2 seconds
        reconnectTimeoutRef.current = setTimeout(connect, 2000);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return { telemetry, history, isConnected };
}
