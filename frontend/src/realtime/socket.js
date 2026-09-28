export function createSocket(url, { onMessage, onStatus }) {
  let ws = null;
  let closed = false;
  let reconnectAttempts = 0;
  let timer = null;

  function connect() {
    if (closed) return;
    onStatus('connecting');
    ws = new WebSocket(url);

    ws.onopen = () => {
      reconnectAttempts = 0;
      onStatus('connected');
    };

    ws.onmessage = (e) => {
      try {
        onMessage(JSON.parse(e.data));
      } catch {
        // ignore malformed frames
      }
    };

    ws.onclose = () => {
      if (closed) return;
      scheduleReconnect();
    };

    ws.onerror = () => {
      // onclose follows and drives the reconnect
    };
  }

  function scheduleReconnect() {
    onStatus('reconnecting');
    const delay = Math.min(1000 * 2 ** reconnectAttempts, 10000);
    reconnectAttempts += 1;
    timer = setTimeout(connect, delay);
  }

  function close() {
    closed = true;
    if (timer) clearTimeout(timer);
    if (ws) ws.close();
  }

  connect();
  return { close };
}
