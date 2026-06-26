/**
 * Terra 도메인 타입 — 단일 진실은 docs/CONTRACT.md.
 * 추출(민지) → 계산엔진(주영) → 3D 행성(연성) 사이 JSON 계약을 TypeScript로 박제.
 *
 * ⚠️ CONTRACT.md 가 바뀌면 이 파일도 함께 수정 (백엔드 모델과 형식 일치).
 */

/* ──────────────────────────────────────────────────────────────────────────
 * 1) 추출 출력 = 계산엔진 입력  (민지 → 주영)
 *    Bedrock 멀티모달이 식판·영수증·스크린타임·전력을 정규화한 결과.
 *    숫자(탄소)는 없음 — 계산은 엔진이.
 * ────────────────────────────────────────────────────────────────────────── */

export type ActivityType = "menu" | "food" | "purchase" | "screentime" | "energy";

/** 식단 메뉴명 */
export interface MenuActivity {
  type: "menu";
  /** 계수 테이블(menu_recipes) 키 */
  name: string;
}

/** 식단 품목 + 무게(g) */
export interface FoodActivity {
  type: "food";
  /** 계수 테이블(food_factors) 키 */
  item: string;
  grams: number;
}

/** 영수증 품목 + 수량(개). 금액기반 ₩ 계수도 가능 — 확인 필요. */
export interface PurchaseActivity {
  type: "purchase";
  /** 계수 테이블(purchase_factors) 키 */
  item: string;
  qty: number;
}

/** 스크린타임 사용시간(분) */
export interface ScreentimeActivity {
  type: "screentime";
  /** 계수 테이블(screentime_factor) 키 */
  item: string;
  minutes: number;
}

/** 전력(kWh) */
export interface EnergyActivity {
  type: "energy";
  /** 계수 테이블(energy_factors) 키 */
  item: string;
  kwh: number;
}

export type Activity =
  | MenuActivity
  | FoodActivity
  | PurchaseActivity
  | ScreentimeActivity
  | EnergyActivity;

export interface ExtractionResult {
  activities: Activity[];
  confidence: number;
  /** true → UI "확인 필요" 배지 */
  needs_review: boolean;
}

/* ──────────────────────────────────────────────────────────────────────────
 * tier — 행성 비주얼 단계 (CONTRACT.md §3)
 * ────────────────────────────────────────────────────────────────────────── */

export type Tier = "low" | "mid" | "high";

/**
 * tier 임계값 (gCO2e). ⚠️ 계산엔진·계수 확정 후 재튜닝 (주영/민지).
 * low ≤ 700 · mid 700–2500 · high > 2500
 */
export const TIER_THRESHOLDS = {
  /** 이하 = low */
  low: 700,
  /** 초과 = high */
  high: 2500,
} as const;

/** gCO2e → tier. (700=low 경계 포함, 2500=mid 경계 포함) */
export function tierFromGrams(grams: number): Tier {
  if (grams <= TIER_THRESHOLDS.low) return "low";
  if (grams > TIER_THRESHOLDS.high) return "high";
  return "mid";
}

/* ──────────────────────────────────────────────────────────────────────────
 * 2-A) 개인 결과 = 개인 행성 입력  (주영 → 연성)
 * ────────────────────────────────────────────────────────────────────────── */

export interface EmissionBreakdown {
  label: string;
  grams_co2e: number;
  /** 출처 (계수 근거) */
  source: string;
}

export interface EmissionItem {
  name: string;
  total_grams_co2e: number;
  breakdown: EmissionBreakdown[];
  sources: string[];
}

/** 코칭/매직모먼트용 더 나은 대안 */
export interface BestAlternative {
  name: string;
  grams_co2e: number;
  saving_grams: number;
}

export interface PersonalResult {
  user_id: string;
  dept_id: string;
  total_grams_co2e: number;
  tier: Tier;
  items: EmissionItem[];
  best_alternative?: BestAlternative;
  /** 탄소 절감 시 모으는 도감 항목(동물·풍력발전소 등). 해금 규칙 확인 필요. */
  unlocks: string[];
}

/* ──────────────────────────────────────────────────────────────────────────
 * 2-B) 집계 결과 = 학과 / 캠퍼스 행성 입력  (주영 → 연성)
 *    행성 크기 = participation_rate · 깨끗한 정도 = avg_grams_co2e(tier)
 * ────────────────────────────────────────────────────────────────────────── */

export interface DepartmentAggregate {
  dept_id: string;
  name: string;
  participants: number;
  total_students: number;
  /** participants / total_students → 행성 크기 */
  participation_rate: number;
  /** 참여 인원 평균 배출량 → 깨끗한 정도 */
  avg_grams_co2e: number;
  tier: Tier;
}

export interface CampusSystem {
  campus_id: string;
  participation_rate: number;
  avg_grams_co2e: number;
  tier: Tier;
  departments: DepartmentAggregate[];
}

export interface AggregateResult {
  campus_system: CampusSystem;
}
