/* ===================================================================
 * Terra — 일상 탄소 측정 입력 화면 (데모)
 *
 * 계약(docs/CONTRACT.md) 정합:
 *  - 탄소 단위는 gCO2e (g). tier 임계값 700 / 2500.
 *  - 추출 결과(§1 ExtractionResult)에는 숫자(탄소)가 없음 — 계산은 엔진.
 *    실제 연동: §1 → POST /compute → §2-A PersonalResult 를 "표시만".
 *    아래 buildExtraction*() 가 §1, mockCompute() 가 §2-A 자리(엔진 대체).
 *  - 데모 시드 계수(엔진측 임시): 스크린타임 0.15 gCO2e/분, 전력 459.4 gCO2e/kWh.
 *  - 이미지 분석/스크린타임 연동은 데모 mock — 실제 API로 교체 지점은 buildExtraction*().
 * =================================================================== */

/* ---------- tier (계약 §3) ---------- */
function tierFromGrams(g) {
  if (g <= 700) return "low";
  if (g > 2500) return "high";
  return "mid";
}
const TIER_LABEL = { low: "낮음 🌿", mid: "보통", high: "높음 ⚠️" };

/* ---------- 데모 시드 계수 (엔진측 임시값) ---------- */
const SEED = {
  screentimePerMin: 0.15, // gCO2e/분 (스마트폰) — 계약 4-A
  energyPerKwh: 459.4,    // gCO2e/kWh (한국 전력, 0.4594 kg)
};
// 메뉴 1끼 gCO2e (계약 §3 예시값)
const MENU = [
  { name: "제육덮밥", g: 1185 },
  { name: "김치찌개", g: 1065 },
  { name: "치킨마요덮밥", g: 1140 },
  { name: "비건비빔밥", g: 570 },
  { name: "잔치국수", g: 305 },
  { name: "소불고기덮밥", g: 8150 },
];
// 영수증 품목 개당 gCO2e
const PURCHASE = [
  { item: "아메리카노", g: 210 },
  { item: "삼각김밥", g: 380 },
  { item: "도시락", g: 900 },
  { item: "생수", g: 160 },
  { item: "과자", g: 300 },
];

/* ---------- 유틸 ---------- */
function rand(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function randNum(min, max) { return Math.random() * (max - min) + min; }
function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function gLabel(g) { return `${Math.round(g).toLocaleString()} gCO₂e`; }

/* ===================================================================
 * 계산엔진 대체 (mock). 실제로는 POST /compute(body: {user_id, dept_id,
 * extraction, campus_id?}) → §2-A PersonalResult. 여기선 시드 계수로 산출.
 * =================================================================== */
function mockCompute(extraction) {
  const items = extraction.activities.map((a) => {
    let grams = 0;
    const label = a.name || a.item || a.type;
    if (a.type === "menu") grams = (MENU.find((m) => m.name === a.name) || { g: 0 }).g;
    else if (a.type === "purchase") grams = (PURCHASE.find((p) => p.item === a.item) || { g: 0 }).g * (a.qty || 1);
    else if (a.type === "screentime") grams = (a.minutes || 0) * SEED.screentimePerMin;
    else if (a.type === "energy") grams = (a.kwh || 0) * SEED.energyPerKwh;
    grams = Math.round(grams);
    return { name: label, total_grams_co2e: grams, breakdown: [{ label, grams_co2e: grams, source: "seed(데모)" }], sources: ["seed"] };
  });
  const total = items.reduce((s, i) => s + i.total_grams_co2e, 0);
  return { user_id: "demo", dept_id: "cs", total_grams_co2e: total, tier: tierFromGrams(total), items, unlocks: [] };
}

/* ---------- 화면 전환 ---------- */
const screens = document.querySelectorAll(".screen");
const backBtn = document.getElementById("backBtn");
const appTitle = document.getElementById("appTitle");

function showScreen(id) {
  screens.forEach((s) => s.classList.toggle("active", s.id === id));
  const isHome = id === "screen-home";
  backBtn.hidden = false;   // 홈에선 '행성으로', 하위화면에선 '홈으로' (항상 노출)
  appTitle.textContent = isHome ? "탄소 측정" : "측정하기";
  const co2 = document.getElementById("iconCO2");
  const sprout = document.getElementById("iconLeaf");
  if (isHome) { co2.removeAttribute("hidden"); sprout.setAttribute("hidden", ""); }
  else { co2.setAttribute("hidden", ""); sprout.removeAttribute("hidden"); }
  window.scrollTo(0, 0);
}
document.querySelectorAll(".menu-card").forEach((card) => {
  card.addEventListener("click", () => showScreen(card.dataset.target));
});
backBtn.addEventListener("click", () => {
  const onHome = document.getElementById("screen-home").classList.contains("active");
  if (onHome) window.location.href = "planet.html";   // 홈에서 뒤로 = 3D 행성으로 복귀
  else showScreen("screen-home");                      // 하위화면 → 홈
});
document.getElementById("heroCta")?.addEventListener("click", () => {
  document.querySelector(".menu-grid")?.scrollIntoView({ behavior: "smooth", block: "center" });
});

/* ---------- 사진 업로드 + 미리보기 ---------- */
function setupUpload(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const box = input.closest(".upload-box");
  const placeholder = box.querySelector(".upload-placeholder");
  const preview = box.querySelector(".preview");
  const screen = input.closest(".screen");
  const analyzeBtn = screen.querySelector(".analyze-btn");
  input.addEventListener("change", () => {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      preview.src = e.target.result;
      preview.hidden = false;
      placeholder.hidden = true;
      box.classList.add("has-image");
      if (analyzeBtn) analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
  });
}
["diet-breakfast", "diet-lunch", "diet-dinner", "power-file", "receipt-file"].forEach(setupUpload);

/* ---------- 결과 렌더링 (XSS 방지: 모든 동적 값 esc) ---------- */
// kind별 오늘 기여분 — 재분석 시 이전값을 빼고 더해 중복합산 방지
const lastContribution = {};
function addCarbonForKind(kind, grams) {
  const prev = lastContribution[kind] || 0;
  addCarbon(grams - prev);
  lastContribution[kind] = grams;
}

function renderResult(screen, kind, rows, grams) {
  const card = screen.querySelector(".result-card");
  const list = card.querySelector(".result-list");
  const carbonValue = card.querySelector(".carbon-value");
  list.innerHTML = rows
    .map((r) => `<li><span class="k">${esc(r.k)}</span><span class="v">${esc(r.v)}</span></li>`)
    .join("");
  carbonValue.textContent = gLabel(grams);
  card.hidden = false;
  addCarbonForKind(kind, grams);
}

// PersonalResult(§2-A) → 결과 화면
function showResult(screen, kind, result, leadRows = []) {
  const rows = [
    ...leadRows,
    ...result.items.map((i) => ({ k: i.name, v: gLabel(i.total_grams_co2e) })),
    { k: "등급(tier)", v: TIER_LABEL[result.tier] },
  ];
  renderResult(screen, kind, rows, result.total_grams_co2e);
}

function withLoading(btn, label, fn) {
  const original = btn.textContent;
  btn.classList.add("loading");
  btn.disabled = true;
  btn.textContent = label;
  setTimeout(() => {
    fn();
    btn.classList.remove("loading");
    btn.disabled = false;
    btn.textContent = original;
  }, 900);
}

/* ===================================================================
 * §1 ExtractionResult 빌더 (실제로는 POST /extract = Bedrock 비전/UsageStats).
 * 데모에서는 업로드 여부만 보고 가상 추출값을 만든다 (숫자 없음).
 * =================================================================== */
// 식단: 아침/점심/저녁
function analyzeDiet(screen) {
  const slots = [["아침", "diet-breakfast"], ["점심", "diet-lunch"], ["저녁", "diet-dinner"]];
  const activities = [];
  const labels = [];
  slots.forEach(([label, id]) => {
    const inp = document.getElementById(id);
    if (inp && inp.files && inp.files[0]) {
      activities.push({ type: "menu", name: rand(MENU).name }); // §1: 숫자 없음
      labels.push(label);
    }
  });
  if (activities.length === 0) return;
  const result = mockCompute({ activities, confidence: 0.82, needs_review: false });
  result.items.forEach((it, idx) => { it.name = `${labels[idx]} · ${it.name}`; });
  showResult(screen, "diet", result);
}

// 전기계량기: 전력(kWh) 수치
function analyzePower(screen) {
  const kwh = +randNum(0.8, 4.5).toFixed(1);
  const result = mockCompute({
    activities: [{ type: "energy", item: "전력_가정용체감", kwh }],
    confidence: 0.8, needs_review: false,
  });
  showResult(screen, "power", result, [{ k: "인식된 사용량", v: `${kwh} kWh` }]);
}

// 휴대폰: 스크린타임(분)
function analyzePhone(screen) {
  const minutes = Math.round(randNum(120, 450)); // UsageStatsManager (분)
  const result = mockCompute({
    activities: [{ type: "screentime", item: "스마트폰", minutes }],
    confidence: 0.9, needs_review: false,
  });
  const h = Math.floor(minutes / 60), m = minutes % 60;
  showResult(screen, "phone", result, [{ k: "오늘 사용 시간", v: `${h}시간 ${m}분 (${minutes}분)` }]);
}

const ANALYZERS = { diet: analyzeDiet, power: analyzePower, phone: analyzePhone };

document.querySelectorAll(".analyze-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const kind = btn.dataset.kind;
    const fn = ANALYZERS[kind];
    if (!fn) return; // receiptAdd 등은 별도 처리
    const screen = btn.closest(".screen");
    const label = kind === "phone" ? "연동 중…" : "분석 중…";
    withLoading(btn, label, () => fn(screen));
  });
});

/* ===================================================================
 * 영수증: 여러 장 추가 + 3장째부터 모달
 *  - 영수증 1장 = §1 purchase 활동 묶음 → mockCompute → 합계(g)
 * =================================================================== */
const receiptEntries = [];
const receiptAddBtn = document.getElementById("receiptAddBtn");
const receiptFileInput = document.getElementById("receipt-file");

function analyzeOneReceipt() {
  const n = Math.floor(randNum(2, 4));
  const used = new Set();
  const activities = [];
  while (activities.length < n) {
    const p = rand(PURCHASE);
    if (used.has(p.item)) continue;
    used.add(p.item);
    activities.push({ type: "purchase", item: p.item, qty: Math.floor(randNum(1, 3)) });
  }
  const result = mockCompute({ activities, confidence: 0.78, needs_review: false });
  return { items: result.items, total: result.total_grams_co2e };
}

function summarizeItems(items) {
  const names = items.map((i) => i.name);
  if (names.length <= 2) return names.join(", ");
  return `${names.slice(0, 2).join(", ")} 외 ${names.length - 2}건`;
}
function receiptItemHtml(e, idx) {
  return `<li class="receipt-item">
        <div class="receipt-item-main">
          <span class="receipt-item-title">영수증 #${idx + 1}</span>
          <span class="receipt-item-sub">${esc(summarizeItems(e.items))}</span>
        </div>
        <span class="receipt-item-carbon">${esc(gLabel(e.total))}</span>
        <button class="receipt-del" data-idx="${idx}" aria-label="삭제">×</button>
      </li>`;
}
const RECEIPT_INLINE_LIMIT = 2;
function openReceiptModal() { document.getElementById("receiptModal").hidden = false; }
function closeReceiptModal() { document.getElementById("receiptModal").hidden = true; }

function renderReceiptList() {
  const summary = document.getElementById("receiptSummary");
  const list = document.getElementById("receiptList");
  const modalList = document.getElementById("receiptModalList");
  const countEl = document.getElementById("receiptCount");
  const totalEl = document.getElementById("receiptTotal");
  const moreBtn = document.getElementById("receiptMoreBtn");

  summary.hidden = receiptEntries.length === 0;
  countEl.textContent = receiptEntries.length;
  list.innerHTML = receiptEntries.slice(0, RECEIPT_INLINE_LIMIT).map(receiptItemHtml).join("");
  modalList.innerHTML = receiptEntries.map(receiptItemHtml).join("");

  const hiddenCount = receiptEntries.length - RECEIPT_INLINE_LIMIT;
  moreBtn.hidden = hiddenCount <= 0;
  if (hiddenCount > 0) moreBtn.textContent = `+${hiddenCount}장 더 보기 (전체 ${receiptEntries.length}장)`;

  const total = receiptEntries.reduce((s, e) => s + e.total, 0);
  totalEl.textContent = gLabel(total);
  if (receiptEntries.length === 0) closeReceiptModal();
}

function resetReceiptUpload() {
  const box = receiptFileInput.closest(".upload-box");
  box.classList.remove("has-image");
  box.querySelector(".preview").hidden = true;
  box.querySelector(".upload-placeholder").hidden = false;
  receiptFileInput.value = "";
  receiptAddBtn.disabled = true;
}

if (receiptAddBtn) {
  receiptAddBtn.addEventListener("click", () => {
    if (receiptAddBtn.disabled) return;
    const original = receiptAddBtn.textContent;
    receiptAddBtn.classList.add("loading");
    receiptAddBtn.disabled = true;
    receiptAddBtn.textContent = "분석 중…";
    setTimeout(() => {
      const { items, total } = analyzeOneReceipt();
      receiptEntries.push({ items, total });
      renderReceiptList();
      addCarbon(total);     // 영수증은 장 단위로 누적 (삭제 시 차감)
      resetReceiptUpload();
      receiptAddBtn.classList.remove("loading");
      receiptAddBtn.textContent = original;
    }, 900);
  });
}

function handleReceiptDelete(e) {
  const del = e.target.closest(".receipt-del");
  if (!del) return;
  const idx = Number(del.dataset.idx);
  const removed = receiptEntries.splice(idx, 1)[0];
  if (removed) addCarbon(-removed.total);
  renderReceiptList();
}
document.getElementById("receiptList")?.addEventListener("click", handleReceiptDelete);
document.getElementById("receiptModalList")?.addEventListener("click", handleReceiptDelete);
document.getElementById("receiptMoreBtn")?.addEventListener("click", openReceiptModal);
document.getElementById("receiptModalClose")?.addEventListener("click", closeReceiptModal);
document.getElementById("receiptModalBackdrop")?.addEventListener("click", closeReceiptModal);

/* ===================================================================
 * 대시보드: 최근 7일 추이 (gCO2e)
 *  - 측정 시 addCarbon() 으로 오늘 누적에 합산
 *  - 날짜별 localStorage 저장 → 새 날짜는 자동으로 0부터 (일일 초기화)
 * =================================================================== */
const HISTORY_KEY = "terra.history.v2"; // 단위 g로 변경되어 키 버전 업
const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

function dateKey(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function saveHistory(h) { try { localStorage.setItem(HISTORY_KEY, JSON.stringify(h)); } catch (e) { /* 무시 */ } }
function loadHistory() {
  let h = null;
  try { h = JSON.parse(localStorage.getItem(HISTORY_KEY)); } catch (e) { h = null; }
  if (!h || typeof h !== "object") {
    h = {};
    for (let i = 6; i >= 0; i--) {
      const d = new Date(); d.setDate(d.getDate() - i);
      h[dateKey(d)] = i === 0 ? 0 : Math.round(randNum(800, 4000)); // 과거 6일 데모 시드 (g)
    }
    saveHistory(h);
  }
  return h;
}
let carbonHistory = loadHistory();

function addCarbon(grams) {
  const k = dateKey(new Date());
  carbonHistory[k] = Math.max(0, Math.round((carbonHistory[k] || 0) + grams));
  saveHistory(carbonHistory);
  renderDashboard();
}

function renderDashboard() {
  const today = new Date();
  const todayVal = carbonHistory[dateKey(today)] || 0;

  const statToday = document.getElementById("statToday");
  if (statToday) statToday.textContent = Math.round(todayVal).toLocaleString();

  const days = [];
  for (let i = 6; i >= 0; i--) { const d = new Date(); d.setDate(d.getDate() - i); days.push(d); }
  const vals = days.map((d) => carbonHistory[dateKey(d)] || 0);
  const statWeek = document.getElementById("statWeek");
  if (statWeek) statWeek.textContent = Math.round(vals.reduce((s, v) => s + v, 0)).toLocaleString();

  const max = Math.max(...vals, 1);
  const chart = document.getElementById("weekChart");
  if (chart) {
    chart.innerHTML = days.map((d, i) => {
      const barH = Math.max(4, Math.round((vals[i] / max) * 92));
      const isToday = i === days.length - 1;
      const dateLabel = `${d.getMonth() + 1}/${d.getDate()}`;
      return `<div class="bar-wrap${isToday ? " today" : ""}">
        <div class="bar" style="height:${barH}px" data-date="${dateLabel}" data-val="${Math.round(vals[i])}"></div>
        <span class="bar-label">${WEEKDAYS[d.getDay()]}</span>
      </div>`;
    }).join("");
  }
}
renderDashboard();

/* ---------- 전기계량기: 매달 1일에만 업로드 ---------- */
function applyPowerLock() {
  const isFirst = new Date().getDate() === 1;
  const box = document.getElementById("powerBox");
  const input = document.getElementById("power-file");
  const note = document.getElementById("powerLock");
  const nextEl = document.getElementById("powerNextDate");
  const analyzeBtn = document.querySelector('#screen-power .analyze-btn');
  if (isFirst) {
    if (box) box.classList.remove("locked");
    if (input) input.disabled = false;
    if (note) note.hidden = true;
    return;
  }
  if (box) box.classList.add("locked");
  if (input) input.disabled = true;
  if (analyzeBtn) analyzeBtn.disabled = true;
  if (note) note.hidden = false;
  if (nextEl) {
    const now = new Date();
    const next = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    nextEl.textContent = `다음 업로드 가능일: ${next.getMonth() + 1}월 1일`;
  }
}
applyPowerLock();

/* ---------- 7일 그래프 막대 호버 툴팁 ---------- */
(function setupChartTip() {
  const chart = document.getElementById("weekChart");
  const tip = document.getElementById("chartTip");
  if (!chart || !tip) return;
  const card = chart.closest(".week-card");
  function show(bar) {
    tip.textContent = `${bar.dataset.date} · ${Number(bar.dataset.val).toLocaleString()} gCO₂e`;
    tip.hidden = false;
  }
  function place(x, y) {
    const rect = card.getBoundingClientRect();
    tip.style.left = `${x - rect.left}px`;
    tip.style.top = `${y - rect.top - 36}px`;
  }
  chart.addEventListener("mouseover", (e) => { const b = e.target.closest(".bar"); if (b) { show(b); place(e.clientX, e.clientY); } });
  chart.addEventListener("mousemove", (e) => { if (!tip.hidden) place(e.clientX, e.clientY); });
  chart.addEventListener("mouseout", (e) => { if (e.target.closest(".bar")) tip.hidden = true; });
  chart.addEventListener("click", (e) => {
    const b = e.target.closest(".bar"); if (!b) return;
    show(b);
    const r = b.getBoundingClientRect();
    place(r.left + r.width / 2, r.top);
    setTimeout(() => { tip.hidden = true; }, 1500);
  });
})();

/* ===================================================================
 * 하루가 지나면 모든 화면 초기화
 *  - 영수증/업로드/결과/분석버튼/오늘 기여분(lastContribution) 초기화
 *  - 오늘 누적은 날짜 키 기반이라 새 날짜에 자동 0
 *  - 자정을 넘겨 앱을 켜둔 경우도 30초마다 감지
 * =================================================================== */
const LAST_DATE_KEY = "terra.lastDate";

function resetAllScreens() {
  receiptEntries.length = 0;
  renderReceiptList();
  closeReceiptModal();
  Object.keys(lastContribution).forEach((k) => delete lastContribution[k]);
  document.querySelectorAll(".upload-box").forEach((box) => {
    box.classList.remove("has-image");
    const pv = box.querySelector(".preview");
    if (pv) { pv.hidden = true; pv.removeAttribute("src"); }
    const ph = box.querySelector(".upload-placeholder");
    if (ph) ph.hidden = false;
    const input = box.querySelector('input[type="file"]');
    if (input) input.value = "";
  });
  document.querySelectorAll(".result-card").forEach((card) => {
    card.hidden = true;
    const list = card.querySelector(".result-list");
    if (list) list.innerHTML = "";
    const cv = card.querySelector(".carbon-value");
    if (cv) cv.textContent = "- gCO₂e";
  });
  document.querySelectorAll(".analyze-btn").forEach((btn) => {
    if (!btn.classList.contains("screentime-btn")) btn.disabled = true;
  });
  applyPowerLock();
}

function checkDayRollover() {
  const today = dateKey(new Date());
  const last = localStorage.getItem(LAST_DATE_KEY);
  if (last === today) return;
  localStorage.setItem(LAST_DATE_KEY, today);
  if (last !== null) {
    resetAllScreens();
    renderDashboard();
  }
}
checkDayRollover();
setInterval(checkDayRollover, 30 * 1000);
