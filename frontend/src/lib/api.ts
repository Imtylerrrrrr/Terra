/**
 * Terra 백엔드 API 클라이언트 (CONTRACT.md §5).
 * 프론트는 DB가 아니라 이 클라이언트로 API Gateway만 호출한다.
 *
 * 베이스 URL: 환경변수 VITE_API_URL (.env). 미설정 시 상대경로(프록시/동일 출처).
 */

import type {
  AggregateResult,
  ExtractionResult,
  PersonalResult,
} from "../types/contract";

const BASE_URL: string = import.meta.env.VITE_API_URL ?? "";

/** §5 에러 응답 `{ error: { code, message } }` → 예외 */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

export interface ComputeRequest {
  user_id: string;
  dept_id: string;
  extraction: ExtractionResult;
  /** 선택 — 기본 "main" (백엔드) */
  campus_id?: string;
}

/** 저장 여부 플래그가 붙은 개인 결과 (§5: /compute 응답에 항상 포함) */
export type ComputeResponse = PersonalResult & { persisted: boolean };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // Content-Type 은 바디가 있을 때만 (GET 에 붙이면 불필요한 CORS preflight 유발).
  // init.headers 는 덮어쓰지 않고 머지 — 호출측이 헤더를 추가/지정할 수 있게.
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body != null ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    // 바디 없음/비JSON
  }

  if (!res.ok) {
    const err = (data as { error?: { code?: string; message?: string } } | null)?.error;
    throw new ApiError(
      err?.code ?? "http_error",
      err?.message ?? res.statusText,
      res.status,
    );
  }
  // 2xx 인데 바디가 비었거나 JSON 이 아니면(계약상 항상 JSON) 명시적 에러로 — 호출측 null 접근 방지.
  if (data === null) {
    throw new ApiError("empty_response", "응답 바디가 비어 있거나 JSON이 아닙니다.", res.status);
  }
  return data as T;
}

/** POST /compute — 활동 추출 결과 → 개인 탄소 결과(2-A) */
export function postCompute(req: ComputeRequest): Promise<ComputeResponse> {
  return request<ComputeResponse>("/compute", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

/** GET /campus/{id} — 캠퍼스/학과 집계(2-B) */
export function getCampus(campusId: string): Promise<AggregateResult> {
  return request<AggregateResult>(`/campus/${encodeURIComponent(campusId)}`);
}
