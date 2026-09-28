// Text-to-speech via the backend's neural voices (Microsoft Edge TTS).
// Produces natural, consistent female speech with no API key. If the backend
// is unreachable or TTS is unavailable, we fall back to the browser's Web
// Speech API so a question is never silent.

const API_URL = import.meta.env.VITE_API_URL || '';
const TTS_VOICE = 'en-US-JennyNeural';

let audio = null;

function getAudio() {
  if (!audio) audio = new Audio();
  return audio;
}

function stopCurrent() {
  const el = getAudio();
  el.pause();
  el.currentTime = 0;
}

async function speakNeural(text, voice) {
  const res = await fetch(
    `${API_URL}/tts?text=${encodeURIComponent(text)}&voice=${encodeURIComponent(voice)}`
  );
  if (!res.ok) throw new Error(`TTS HTTP ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const el = getAudio();
  el.src = url;
  await el.play();
}

function speakBrowser(text) {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  const voices = window.speechSynthesis.getVoices();
  const voice =
    voices.find(
      (v) =>
        v.lang.toLowerCase().startsWith('en') &&
        /female|aria|jenny|sonia|libby|zira|samantha|victoria|ana/i.test(v.name)
    ) ||
    voices.find((v) => v.lang.toLowerCase().startsWith('en')) ||
    voices[0];
  if (voice) {
    utterance.voice = voice;
    utterance.lang = voice.lang;
  }
  utterance.rate = 1;
  utterance.pitch = 1.05;
  window.speechSynthesis.speak(utterance);
}

export async function speak(text, { voice = TTS_VOICE } = {}) {
  if (typeof window === 'undefined' || !text) return;
  stopCurrent();
  try {
    await speakNeural(text, voice);
  } catch {
    speakBrowser(text);
  }
}
