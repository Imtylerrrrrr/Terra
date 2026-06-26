/* ===================================================================
 * 캠퍼스의 안부 🌱 (Terra) - 프론트엔드 로직
 *
 * 참고: 실제 이미지 AI 분석과 스크린타임(Screen Time / UsageStats) 연동은
 *       백엔드 API 또는 네이티브(iOS/Android) 권한이 필요합니다.
 *       analyze*() / fetchScreenTime() 의 "TODO: 실제 API 연동" 부분만
 *       교체하면 UI 변경 없이 그대로 동작하도록 구조를 잡아두었습니다.
 * =================================================================== */

/* ---------- 탄소 배출 계수 (추정치) ---------- */
const EF = {
  electricityPerKwh: 0.4594, // 한국 전력 배출계수 kgCO₂/kWh
  phonePerHour: 0.05,        // 휴대폰 사용 1시간당 kgCO₂ (기기+네트워크 추정)
};

/* ---------- 화면 전환 ---------- */
const screens = document.querySelectorAll(".screen");
const backBtn = document.getElementById("backBtn");
const appTitle = document.getElementById("appTitle");

function showScreen(id) {
  screens.forEach((s) => s.classList.toggle("active", s.id === id));
  const isHome = id === "screen-home";
  backBtn.hidden = isHome;
  appTitle.textContent = isHome ? "탄소 측정" : "측정하기";
  const co2 = document.getElementById("iconCO2");
  const sprout = document.getElementById("iconLeaf");
  if (isHome) {
    co2.removeAttribute("hidden");
    sprout.setAttribute("hidden", "");
  } else {
    co2.setAttribute("hidden", "");
    sprout.removeAttribute("hidden");
  }
  window.scrollTo(0, 0);
}

document.querySelectorAll(".menu-card").forEach((card) => {
  card.addEventListener("click", () => showScreen(card.dataset.target));
});
backBtn.addEventListener("click", () => showScreen("screen-home"));

// 히어로 CTA → 카테고리 섹션으로 스크롤
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

/* ---------- 결과 렌더링 ---------- */
function renderResult(screen, rows, carbonKg) {
  const card = screen.querySelector(".result-card");
  const list = card.querySelector(".result-list");
  const carbonValue = card.querySelector(".carbon-value");

  list.innerHTML = rows
    .map((r) => `<li><span class="k">${r.k}</span><span class="v">${r.v}</span></li>`)
    .join("");
  carbonValue.textContent = `${carbonKg.toFixed(2)} kg CO₂`;
  card.hidden = false;
  addCarbon(carbonKg);
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

/* ---------- 유틸 ---------- */
function rand(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function randNum(min, max) { return Math.random() * (max - min) + min; }

/* ---------- 식단 사진: 음식 종류 + 칼로리 → 탄소 ---------- */
const FOODS = [
  { name: "소고기 스테이크", efPerKcal: 0.012 },
  { name: "닭가슴살 샐러드", efPerKcal: 0.003 },
  { name: "비빔밥", efPerKcal: 0.0025 },
  { name: "치즈 피자", efPerKcal: 0.006 },
  { name: "연어 초밥", efPerKcal: 0.004 },
];
function analyzeDiet(screen) {
  // TODO: 실제 API 연동 - 업로드 이미지 → 음식 인식/칼로리 추정
  const meals = [
    ["아침", "diet-breakfast"],
    ["점심", "diet-lunch"],
    ["저녁", "diet-dinner"],
  ];
  const rows = [];
  let total = 0;
  meals.forEach(([label, id]) => {
    const input = document.getElementById(id);
    if (input && input.files && input.files[0]) {
      const food = rand(FOODS);
      const kcal = Math.round(randNum(350, 850));
      const carbon = kcal * food.efPerKcal;
      total += carbon;
      rows.push({ k: `${label} · ${food.name}`, v: `${kcal} kcal` });
    }
  });
  if (rows.length === 0) return;
  renderResult(screen, rows, total);
}

/* ---------- 전기계량기: kWh → 탄소 ---------- */
function analyzePower(screen) {
  // TODO: 실제 API 연동 - 계량기 이미지 OCR → 사용량(kWh)
  const kwh = randNum(120, 480);
  const carbon = kwh * EF.electricityPerKwh;
  renderResult(screen, [
    { k: "인식된 사용량", v: `${kwh.toFixed(1)} kWh` },
    { k: "적용 배출계수", v: `${EF.electricityPerKwh} kg/kWh` },
  ], carbon);
}

/* ---------- 영수증: 품목 종류 → 탄소 (여러 장 추가) ---------- */
const RECEIPT_ITEMS = [
  { name: "정육 (소/돼지)", carbon: 5.2 },
  { name: "채소·과일", carbon: 0.6 },
  { name: "가공식품", carbon: 1.4 },
  { name: "생활용품", carbon: 2.1 },
  { name: "음료", carbon: 0.9 },
];
// 영수증 한 장 분석 → {items, total}
function analyzeOneReceipt() {
  // TODO: 실제 API 연동 - 영수증 OCR → 품목 분류
  const count = Math.floor(randNum(2, 4));
  const picked = [];
  const used = new Set();
  while (picked.length < count) {
    const item = rand(RECEIPT_ITEMS);
    if (used.has(item.name)) continue;
    used.add(item.name);
    picked.push(item);
  }
  const total = picked.reduce((s, i) => s + i.carbon, 0);
  return { items: picked, total };
}

/* ---------- 휴대폰: 스크린타임 → 탄소 ---------- */
function fetchScreenTime() {
  // TODO: 실제 연동
  //   - iOS: Screen Time(DeviceActivity) API, 네이티브 앱 필요
  //   - Android: UsageStatsManager, PACKAGE_USAGE_STATS 권한 필요
  const hours = randNum(2.5, 7.5);
  return {
    totalHours: hours,
    topApps: [
      { name: "동영상/스트리밍", h: hours * 0.4 },
      { name: "SNS", h: hours * 0.35 },
      { name: "웹/기타", h: hours * 0.25 },
    ],
  };
}
function analyzePhone(screen) {
  const data = fetchScreenTime();
  const carbon = data.totalHours * EF.phonePerHour;
  const h = Math.floor(data.totalHours);
  const m = Math.round((data.totalHours - h) * 60);
  renderResult(
    screen,
    [
      { k: "오늘 총 사용 시간", v: `${h}시간 ${m}분` },
      ...data.topApps.map((a) => ({ k: a.name, v: `${a.h.toFixed(1)}시간` })),
    ],
    carbon
  );
}

const ANALYZERS = {
  diet: analyzeDiet,
  power: analyzePower,
  phone: analyzePhone,
};

/* ---------- 분석 버튼 바인딩 (영수증 추가 버튼 제외) ---------- */
document.querySelectorAll(".analyze-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const kind = btn.dataset.kind;
    const fn = ANALYZERS[kind];
    if (!fn) return; // receiptAdd 등 별도 처리 버튼은 건너뜀
    const screen = btn.closest(".screen");
    const label = kind === "phone" ? "연동 중…" : "분석 중…";
    withLoading(btn, label, () => fn(screen));
  });
});

/* ---------- 영수증: 여러 장 추가 + 간소화 목록 ---------- */
const receiptEntries = [];
const receiptAddBtn = document.getElementById("receiptAddBtn");
const receiptFileInput = document.getElementById("receipt-file");

function summarizeItems(items) {
  // "정육, 음료 외 1건" 형태로 간소화
  const names = items.map((i) => i.name.replace(/\s*\(.*\)/, ""));
  if (names.length <= 2) return names.join(", ");
  return `${names.slice(0, 2).join(", ")} 외 ${names.length - 2}건`;
}

function receiptItemHtml(e, idx) {
  return `<li class="receipt-item">
        <div class="receipt-item-main">
          <span class="receipt-item-title">영수증 #${idx + 1}</span>
          <span class="receipt-item-sub">${summarizeItems(e.items)}</span>
        </div>
        <span class="receipt-item-carbon">${e.total.toFixed(1)} kg</span>
        <button class="receipt-del" data-idx="${idx}" aria-label="삭제">×</button>
      </li>`;
}

const RECEIPT_INLINE_LIMIT = 2; // 인라인 2장, 3장째부터 모달

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

  // 인라인: 2장까지만 노출
  list.innerHTML = receiptEntries.slice(0, RECEIPT_INLINE_LIMIT).map(receiptItemHtml).join("");
  // 모달: 전체
  modalList.innerHTML = receiptEntries.map(receiptItemHtml).join("");

  const hiddenCount = receiptEntries.length - RECEIPT_INLINE_LIMIT;
  if (hiddenCount > 0) {
    moreBtn.hidden = false;
    moreBtn.textContent = `+${hiddenCount}장 더 보기 (전체 ${receiptEntries.length}장)`;
  } else {
    moreBtn.hidden = true;
  }

  const total = receiptEntries.reduce((s, e) => s + e.total, 0);
  totalEl.textContent = `${total.toFixed(2)} kg CO₂`;

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
      addCarbon(total);       // 대시보드 오늘 발자국에 합산
      resetReceiptUpload();   // 다음 영수증 업로드 준비 (버튼은 비활성 유지)
      receiptAddBtn.classList.remove("loading");
      receiptAddBtn.textContent = original;
    }, 900);
  });
}

// 추가한 영수증 삭제 (인라인·모달 양쪽에서, 합계·대시보드도 갱신)
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
 * 하단 대시보드: 오늘 누적 요약 / 최근 7일 추이
 * - 측정할 때마다 addCarbon()으로 오늘 발자국에 합산
 * - 최근 7일 데이터는 localStorage에 저장 (과거 6일은 데모용 시드값)
 * =================================================================== */
const HISTORY_KEY = "terra.history.v1";
const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

function dateKey(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function saveHistory(h) {
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(h)); } catch (e) { /* 무시 */ }
}
function loadHistory() {
  let h = null;
  try { h = JSON.parse(localStorage.getItem(HISTORY_KEY)); } catch (e) { h = null; }
  if (!h || typeof h !== "object") {
    h = {};
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      h[dateKey(d)] = i === 0 ? 0 : +randNum(40, 160).toFixed(1); // 과거 6일 데모 데이터
    }
    saveHistory(h);
  }
  return h;
}

let carbonHistory = loadHistory();

function addCarbon(kg) {
  const k = dateKey(new Date());
  carbonHistory[k] = (carbonHistory[k] || 0) + kg;
  saveHistory(carbonHistory);
  renderDashboard();
}

function renderDashboard() {
  const today = new Date();
  const yest = new Date();
  yest.setDate(yest.getDate() - 1);

  const todayVal = carbonHistory[dateKey(today)] || 0;
  const yestVal = carbonHistory[dateKey(yest)] || 0;

  /* 오늘 발자국 (히어로 통계 + 요약 카드가 있으면 갱신) */
  const todayEl = document.getElementById("todayTotal");
  if (todayEl) todayEl.textContent = todayVal.toFixed(2);
  const statToday = document.getElementById("statToday");
  if (statToday) statToday.textContent = todayVal.toFixed(1);
  const trendEl = document.getElementById("summaryTrend");
  const hintEl = document.getElementById("summaryHint");
  if (trendEl && hintEl) {
    if (todayVal === 0) {
      trendEl.textContent = "";
      trendEl.className = "summary-trend";
      hintEl.textContent = "항목을 측정하면 오늘 발자국이 쌓여요.";
    } else if (yestVal > 0) {
      const diff = todayVal - yestVal;
      if (diff <= 0) {
        trendEl.textContent = `▼ ${Math.abs(diff).toFixed(1)}kg`;
        trendEl.className = "summary-trend down";
        hintEl.textContent = "어제보다 줄었어요. 지구가 고마워해요 🌱";
      } else {
        trendEl.textContent = `▲ ${diff.toFixed(1)}kg`;
        trendEl.className = "summary-trend up";
        hintEl.textContent = "어제보다 늘었어요. 내일은 줄여볼까요?";
      }
    } else {
      trendEl.textContent = "";
      trendEl.className = "summary-trend";
      hintEl.textContent = "오늘의 발자국을 기록 중이에요.";
    }
  }

  /* 5. 최근 7일 추이 */
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push(d);
  }
  const vals = days.map((d) => carbonHistory[dateKey(d)] || 0);
  const max = Math.max(...vals, 1);
  const statWeek = document.getElementById("statWeek");
  if (statWeek) statWeek.textContent = vals.reduce((s, v) => s + v, 0).toFixed(1);
  const chart = document.getElementById("weekChart");
  chart.innerHTML = days
    .map((d, i) => {
      const barH = Math.max(4, Math.round((vals[i] / max) * 92));
      const isToday = i === days.length - 1;
      const dateLabel = `${d.getMonth() + 1}/${d.getDate()}`;
      return `<div class="bar-wrap${isToday ? " today" : ""}">
        <div class="bar" style="height:${barH}px" data-date="${dateLabel}" data-val="${vals[i].toFixed(1)}"></div>
        <span class="bar-label">${WEEKDAYS[d.getDay()]}</span>
      </div>`;
    })
    .join("");
}

renderDashboard();

/* ===================================================================
 * 전기계량기: 매달 1일에만 업로드 가능
 * =================================================================== */
function applyPowerLock() {
  const isFirst = new Date().getDate() === 1;
  const box = document.getElementById("powerBox");
  const input = document.getElementById("power-file");
  const note = document.getElementById("powerLock");
  const nextEl = document.getElementById("powerNextDate");
  const analyzeBtn = document.querySelector('#screen-power .analyze-btn');

  if (isFirst) {
    // 1일이면 잠금 해제
    if (box) box.classList.remove("locked");
    if (input) input.disabled = false;
    if (note) note.hidden = true;
    return;
  }
  // 1일이 아니면 잠금
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

/* ===================================================================
 * 최근 7일 그래프: 막대에 마우스를 올리면 그날 배출량 툴팁 표시
 * =================================================================== */
(function setupChartTip() {
  const chart = document.getElementById("weekChart");
  const tip = document.getElementById("chartTip");
  if (!chart || !tip) return;
  const card = chart.closest(".week-card");

  function show(bar) {
    tip.textContent = `${bar.dataset.date} · ${bar.dataset.val} kg CO₂`;
    tip.hidden = false;
  }
  function place(clientX, clientY) {
    const rect = card.getBoundingClientRect();
    tip.style.left = `${clientX - rect.left}px`;
    tip.style.top = `${clientY - rect.top - 36}px`;
  }
  chart.addEventListener("mouseover", (e) => {
    const bar = e.target.closest(".bar");
    if (bar) { show(bar); place(e.clientX, e.clientY); }
  });
  chart.addEventListener("mousemove", (e) => {
    if (tip.hidden) return;
    place(e.clientX, e.clientY);
  });
  chart.addEventListener("mouseout", (e) => {
    if (e.target.closest(".bar")) tip.hidden = true;
  });
  // 터치(모바일): 탭하면 잠깐 표시
  chart.addEventListener("click", (e) => {
    const bar = e.target.closest(".bar");
    if (!bar) return;
    show(bar);
    const r = bar.getBoundingClientRect();
    place(r.left + r.width / 2, r.top);
    setTimeout(() => { tip.hidden = true; }, 1500);
  });
})();


/* ===================================================================
 * 하루가 지나면 모든 화면 초기화
 * - 영수증 목록, 업로드 사진/미리보기, 결과 카드, 분석 버튼 상태 초기화
 * - 대시보드 "오늘 발자국"은 날짜 기준이라 자동으로 0부터 시작
 * - 자정을 넘기며 앱을 켜둔 경우에도 30초마다 확인해 초기화
 * =================================================================== */
const LAST_DATE_KEY = "terra.lastDate";

function resetAllScreens() {
  // 영수증 초기화
  receiptEntries.length = 0;
  renderReceiptList();
  closeReceiptModal();

  // 업로드 박스 / 미리보기 초기화
  document.querySelectorAll(".upload-box").forEach((box) => {
    box.classList.remove("has-image");
    const pv = box.querySelector(".preview");
    if (pv) { pv.hidden = true; pv.removeAttribute("src"); }
    const ph = box.querySelector(".upload-placeholder");
    if (ph) ph.hidden = false;
    const input = box.querySelector('input[type="file"]');
    if (input) input.value = "";
  });

  // 결과 카드 초기화
  document.querySelectorAll(".result-card").forEach((card) => {
    card.hidden = true;
    const list = card.querySelector(".result-list");
    if (list) list.innerHTML = "";
    const cv = card.querySelector(".carbon-value");
    if (cv) cv.textContent = "- kg CO₂";
  });

  // 분석 버튼 비활성화 (스크린타임 버튼은 사진 없이도 쓰므로 유지)
  document.querySelectorAll(".analyze-btn").forEach((btn) => {
    if (!btn.classList.contains("screentime-btn")) btn.disabled = true;
  });

  // 전기계량기 잠금 재평가
  applyPowerLock();
}

function checkDayRollover() {
  const today = dateKey(new Date());
  const last = localStorage.getItem(LAST_DATE_KEY);
  if (last === today) return;
  localStorage.setItem(LAST_DATE_KEY, today);
  if (last !== null) {
    // 날짜가 바뀜 → 전체 초기화 + 대시보드 갱신
    resetAllScreens();
    renderDashboard();
  }
}

checkDayRollover();                       // 로드 시 1회 확인
setInterval(checkDayRollover, 30 * 1000); // 자정 넘김 대비 30초마다 확인
