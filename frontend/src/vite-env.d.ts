/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 백엔드 API 베이스 URL (SAM 출력 ApiUrl). 예: https://xxxx.execute-api.ap-northeast-2.amazonaws.com/prod */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
