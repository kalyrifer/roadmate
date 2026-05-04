export const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const wsDefault = (() => {
  if (typeof window === 'undefined') return 'ws://localhost:8000/ws';
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/ws`;
})();

export const WS_URL = import.meta.env.VITE_WS_URL || wsDefault;

export const APP_NAME = 'RoadMate';

export const DEFAULT_LANGUAGE = 'ru';
