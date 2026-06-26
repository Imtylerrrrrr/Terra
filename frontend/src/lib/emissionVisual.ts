/**
 * 탄소 → 행성 비주얼 매핑 (단일 진실). frontend-conventions §5.
 *
 * 매핑 규칙(README · CONTRACT.md):
 *   - tier               → 행성 색 (CSS 토큰 --color-emission-*)
 *   - participation_rate → 행성 크기 (참여율)
 *   - avg_grams_co2e     → 깨끗한 정도 (평균 배출량)
 *
 * 색의 실제 값은 CSS 토큰(src/styles/tokens.css)이 단일 진실이므로
 * 여기서는 토큰 "이름"만 반환한다 (하드코딩 금지).
 *
 * ⚠️ 크기/깨끗함 스케일 상수는 계산엔진·계수 확정 후 재튜닝 (주영/민지).
 */

import type { Tier } from "../types/contract";

export type EmissionToken =
  | "var(--color-emission-low)"
  | "var(--color-emission-mid)"
  | "var(--color-emission-high)";

export const TIER_TO_TOKEN: Record<Tier, EmissionToken> = {
  low: "var(--color-emission-low)",
  mid: "var(--color-emission-mid)",
  high: "var(--color-emission-high)",
};

/** 행성 크기 배율 범위 (참여율 0~1 → min~max). TODO: 데모 보고 튜닝. */
export const PLANET_SIZE = { min: 0.5, max: 1.5 } as const;

/** 깨끗함 0→1 선형 매핑 기준 상한(gCO2e). 이 값 이상이면 0(황폐). TODO 재튜닝. */
export const CLEAN_SCALE_MAX_GRAMS = 2500;

export interface PlanetVisual {
  /** tier 색 토큰 (CSS var) */
  colorToken: EmissionToken;
  /** 행성 크기 배율 (참여율 기반) */
  size: number;
  /** 깨끗한 정도 0(황폐) ~ 1(청정) — 평균 배출량 기반 */
  cleanliness: number;
  tier: Tier;
}

/** 0~1 로 클램프 */
function clamp01(n: number): number {
  if (Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

/** 참여율(0~1) → 행성 크기 배율 (선형) */
export function sizeFromParticipation(rate: number): number {
  const r = clamp01(rate);
  return PLANET_SIZE.min + (PLANET_SIZE.max - PLANET_SIZE.min) * r;
}

/** 평균 배출량(gCO2e) → 깨끗한 정도 0~1 (낮을수록 깨끗 = 1) */
export function cleanlinessFromAvg(avgGrams: number): number {
  return clamp01(1 - avgGrams / CLEAN_SCALE_MAX_GRAMS);
}

/** tier → 색 토큰 */
export function colorTokenFromTier(tier: Tier): EmissionToken {
  return TIER_TO_TOKEN[tier];
}

export interface PlanetVisualInput {
  tier: Tier;
  participation_rate: number;
  avg_grams_co2e: number;
}

/**
 * 학과/캠퍼스 행성의 비주얼 파라미터 산출.
 * DepartmentAggregate · CampusSystem 둘 다 이 input 형태와 호환.
 */
export function planetVisual(input: PlanetVisualInput): PlanetVisual {
  return {
    colorToken: colorTokenFromTier(input.tier),
    size: sizeFromParticipation(input.participation_rate),
    cleanliness: cleanlinessFromAvg(input.avg_grams_co2e),
    tier: input.tier,
  };
}
