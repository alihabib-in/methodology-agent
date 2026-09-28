const API_URL = import.meta.env.VITE_API_URL || '';

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`Request failed (HTTP ${res.status}): ${path}`);
  }
  return res.json();
}

export const createSession = () =>
  request('/meetings', { method: 'POST', body: JSON.stringify({}) });

export const analyzeSession = (sessionId, text, language = null) =>
  request(`/meetings/${sessionId}/analyze`, {
    method: 'POST',
    body: JSON.stringify({ text, language }),
  });

export const getSessionState = (sessionId) =>
  request(`/meetings/${sessionId}/state`);

export const answerSession = (sessionId, answer, language = null) =>
  request(`/meetings/${sessionId}/answer`, {
    method: 'POST',
    body: JSON.stringify({ answer, language }),
  });

export const createMeeting = (sessionId, title, createdBy, displayName) =>
  request('/api/v1/meetings', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      title,
      created_by: createdBy,
      display_name: displayName,
    }),
  });

export const logEvent = (meetingId, eventType, payload = {}, sessionId = null) =>
  request(`/api/v1/meetings/${meetingId}/events`, {
    method: 'POST',
    body: JSON.stringify({ event_type: eventType, session_id: sessionId, payload }),
  });

export const listEvents = (meetingId) =>
  request(`/api/v1/meetings/${meetingId}/events`);

export const listKnowledge = () => request('/knowledge');

export const createKnowledgeCandidate = (concept, statement, domain = null, parentId = null) =>
  request('/knowledge/candidate', {
    method: 'POST',
    body: JSON.stringify({ concept, statement, domain, source: 'meeting', parent_id: parentId }),
  });

export const deleteKnowledge = (itemId) =>
  request(`/knowledge/${itemId}`, { method: 'DELETE' });
