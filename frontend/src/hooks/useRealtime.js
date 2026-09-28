import { useEffect, useRef } from 'react';
import { createSocket } from '../realtime/socket';
import { store } from '../store/store';

function wsUrl(sessionId) {
  const base = import.meta.env.VITE_WS_URL || '';
  if (base) return `${base.replace(/\/+$/, '')}/ws/${sessionId}`;
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/ws/${sessionId}`;
}

export function useRealtime(sessionId) {
  const socketRef = useRef(null);

  useEffect(() => {
    if (!sessionId) {
      store.reset();
      return undefined;
    }

    store.setConnection('connecting');

    const socket = createSocket(wsUrl(sessionId), {
      onMessage: (event) => store.dispatch(event),
      onStatus: (status) => store.setConnection(status),
    });
    socketRef.current = socket;

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [sessionId]);
}
