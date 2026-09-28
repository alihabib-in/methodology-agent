import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react';

const JITSI_DOMAIN = import.meta.env.VITE_JITSI_DOMAIN || 'localhost:8443';
const JITSI_BASE_URL = `https://${JITSI_DOMAIN}`;

/**
 * Jitsi IFrame component. Owns the JitsiMeetExternalAPI lifecycle and
 * normalizes raw Jitsi events into application callbacks. No methodology
 * business logic lives here.
 *
 * The effect depends ONLY on roomName/jwt/displayName (stable identifiers);
 * callbacks are read through a ref so re-renders of the parent never tear
 * down and recreate the iframe.
 */
const JitsiMeeting = forwardRef(function JitsiMeeting(props, ref) {
  const {
    roomName,
    jwt,
    displayName,
    onReady,
    onParticipantJoined,
    onParticipantLeft,
    onMeetingEnded,
    onEvent,
  } = props;

  const containerRef = useRef(null);
  const apiRef = useRef(null);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState(null);
  const callbacksRef = useRef({
    onReady,
    onParticipantJoined,
    onParticipantLeft,
    onMeetingEnded,
    onEvent,
  });
  callbacksRef.current = {
    onReady,
    onParticipantJoined,
    onParticipantLeft,
    onMeetingEnded,
    onEvent,
  };

  useImperativeHandle(ref, () => ({
    sendChatMessage(text) {
      apiRef.current?.executeCommand('sendChatMessage', text, false);
    },
    endMeeting() {
      apiRef.current?.executeCommand('hangup');
    },
  }));

  useEffect(() => {
    let cancelled = false;
    let script = null;

    function init() {
      if (cancelled || !window.JitsiMeetExternalAPI || !containerRef.current) {
        return;
      }
      try {
        const options = {
          roomName,
          parentNode: containerRef.current,
          jwt: jwt || undefined,
          userInfo: { displayName: displayName || 'Participant' },
          configOverwrite: {
            startWithAudioMuted: true,
            startWithVideoMuted: true,
            prejoinConfig: { enabled: false },
          },
          interfaceConfigOverwrite: {
            SHOW_JITSI_WATERMARK: false,
            SHOW_WATERMARK_FOR_GUESTS: false,
            JITSI_WATERMARK_LINK: '',
            DEFAULT_LOGO_URL: '',
            DEFAULT_WELCOME_PAGE_LOGO_URL: '',
          },
        };
        apiRef.current = new window.JitsiMeetExternalAPI(JITSI_DOMAIN, options);

        const api = apiRef.current;
        api.addListener('videoConferenceJoined', () => {
          setStatus('ready');
          callbacksRef.current.onReady?.();
          callbacksRef.current.onEvent?.('meeting.joined');
        });
        api.addListener('participantJoined', (p) => {
          callbacksRef.current.onParticipantJoined?.(p);
          callbacksRef.current.onEvent?.('participant.joined', p);
        });
        api.addListener('participantLeft', (p) => {
          callbacksRef.current.onParticipantLeft?.(p);
          callbacksRef.current.onEvent?.('participant.left', p);
        });
        api.addListener('readyToClose', () => {
          callbacksRef.current.onMeetingEnded?.();
          callbacksRef.current.onEvent?.('meeting.ended');
        });
      } catch (e) {
        setStatus('error');
        setError(String(e));
      }
    }

    if (window.JitsiMeetExternalAPI) {
      init();
    } else {
      script = document.createElement('script');
      script.src = `${JITSI_BASE_URL}/external_api.js`;
      script.async = true;
      script.onload = init;
      script.onerror = () => {
        if (cancelled) return;
        setStatus('error');
        setError(
          `Could not load ${JITSI_BASE_URL}/external_api.js. ` +
            'Check that the Jitsi server is reachable and its TLS certificate ' +
            'is trusted for this address.'
        );
      };
      document.head.appendChild(script);
    }

    const loadingTimeout = setTimeout(() => {
      if (!cancelled) {
        setStatus((prev) => (prev === 'loading' ? 'ready' : prev));
      }
    }, 20000);

    return () => {
      cancelled = true;
      clearTimeout(loadingTimeout);
      if (script) {
        script.onload = null;
        script.onerror = null;
      }
      if (apiRef.current) {
        apiRef.current.dispose();
        apiRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roomName, jwt, displayName]);

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />
      {status === 'loading' && (
        <div className="absolute inset-0 flex items-center justify-center bg-black text-sm text-white">
          Loading meeting…
        </div>
      )}
      {status === 'error' && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-950 p-4 text-center text-sm text-red-200">
          {error}
        </div>
      )}
    </div>
  );
});

export default JitsiMeeting;
