/* 越词通 · VietDaily · © 2026 安得半日闲 · v1.2.2 */
(() => {
  "use strict";

  const WORDS = Array.isArray(window.VOCAB) ? window.VOCAB : [];
  const PHONETIC_DATA = window.PHONETICS || { vowels: [], consonants: [], tones: [] };
  const APP_VERSION = "1.2.2";
  const APP_NAME = "越词通";
  const APP_AUTHOR = "安得半日闲";
  const BY_ID = new Map(WORDS.map((word) => [word.id, word]));
  const STORAGE_KEY = "vietdaily.v1";
  const DAY_MS = 86400000;
  const DEFAULT_SETTINGS = { dailyTarget: 5, speed: 1, showHomophone: true, uiSize: "standard" };
  const INTERVALS = [3, 7, 15, 30, 60, 120, 240];
  const VN_WEEKDAYS = ["CHỦ NHẬT", "THỨ HAI", "THỨ BA", "THỨ TƯ", "THỨ NĂM", "THỨ SÁU", "THỨ BẢY"];
  const TOPICS = [...new Set(WORDS.map((word) => word.topic))];
  const TEXTBOOK_WORDS = WORDS.filter((word) => !word.source.startsWith("通用"));
  const GENERAL_WORDS = WORDS.filter((word) => word.source.startsWith("通用"));
  const NEW_WORD_ORDER = [];
  for (let index = 0; index < Math.max(TEXTBOOK_WORDS.length, GENERAL_WORDS.length); index += 1) {
    if (TEXTBOOK_WORDS[index]) NEW_WORD_ORDER.push(TEXTBOOK_WORDS[index]);
    if (GENERAL_WORDS[index]) NEW_WORD_ORDER.push(GENERAL_WORDS[index]);
  }

  const ICONS = {
    volume:
      '<path d="M11 5 6 9H3v6h3l5 4V5Z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18.5 5.5a9 9 0 0 1 0 13"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    x: '<path d="m6 6 12 12M18 6 6 18"/>',
    refresh: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    arrowRight: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    book:
      '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
    download: '<path d="M12 3v12M7 10l5 5 5-5"/><path d="M5 21h14"/>',
    trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/><path d="M10 11v5M14 11v5"/>',
    sparkles:
      '<path d="m12 3 1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3Z"/><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    flame:
      '<path d="M12 2c1.7 4.4 6 5.5 6 10a6 6 0 0 1-12 0c0-2.5 1.2-4.3 3-6 .2 2 1.2 3 2.5 3.5C11.4 7.5 11 4.5 12 2Z"/>',
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const icon = (name, extra = "") =>
    `<svg class="icon ${extra}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ""}</svg>`;

  const pad2 = (value) => String(value).padStart(2, "0");

  function dateKey(date = new Date()) {
    return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
  }

  function parseDate(key) {
    const [year, month, day] = key.split("-").map(Number);
    return new Date(year, month - 1, day);
  }

  function addDays(key, amount) {
    const date = parseDate(key);
    date.setDate(date.getDate() + amount);
    return dateKey(date);
  }

  function diffDays(fromKey, toKey) {
    const [ay, am, ad] = fromKey.split("-").map(Number);
    const [by, bm, bd] = toKey.split("-").map(Number);
    return Math.round((Date.UTC(by, bm - 1, bd) - Date.UTC(ay, am - 1, ad)) / DAY_MS);
  }

  function formatDateZh(key) {
    const [, month, day] = key.split("-").map(Number);
    return `${month}月${day}日`;
  }

  function scheduleText(key) {
    const days = diffDays(dateKey(), key);
    if (days <= 0) return "今天";
    if (days === 1) return "明天";
    return `${days} 天后`;
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => {
      const entities = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
      return entities[character];
    });
  }

  function normalize(value) {
    return String(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d")
      .replace(/Đ/g, "D")
      .toLowerCase();
  }

  function highlightExample(example, word) {
    const source = String(example);
    const target = String(word);
    const index = source.toLocaleLowerCase("vi").indexOf(target.toLocaleLowerCase("vi"));
    if (index < 0) return escapeHtml(source);
    return (
      escapeHtml(source.slice(0, index)) +
      "<mark>" +
      escapeHtml(source.slice(index, index + target.length)) +
      "</mark>" +
      escapeHtml(source.slice(index + target.length))
    );
  }

  function createStore() {
    return {
      version: 1,
      settings: { ...DEFAULT_SETTINGS },
      progress: {},
      plans: {},
      history: {},
    };
  }

  let storageWarned = false;

  function loadStore() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      if (!raw || typeof raw !== "object") return createStore();
      const result = {
        ...createStore(),
        ...raw,
        settings: { ...DEFAULT_SETTINGS, ...(raw.settings || {}) },
        progress: raw.progress && typeof raw.progress === "object" ? raw.progress : {},
        plans: raw.plans && typeof raw.plans === "object" ? raw.plans : {},
        history: raw.history && typeof raw.history === "object" ? raw.history : {},
      };
      if (![3, 5, 8].includes(result.settings.dailyTarget)) result.settings.dailyTarget = 5;
      if (![0.75, 1, 1.25].includes(Number(result.settings.speed))) result.settings.speed = 1;
      if (result.settings.uiSize === "xlarge") result.settings.uiSize = "large";
      if (!["compact", "standard", "large"].includes(result.settings.uiSize)) {
        result.settings.uiSize = "standard";
      }
      result.settings.showHomophone = result.settings.showHomophone !== false;
      return result;
    } catch (error) {
      return createStore();
    }
  }

  let store = loadStore();

  const state = {
    view: "today",
    todayKey: null,
    plan: null,
    index: 0,
    autoIndex: true,
    libraryFilter: "all",
    libraryQuery: "",
    libraryLimit: 60,
    libraryAnchorId: null,
    autoplay: null,
    sheetWordId: null,
    sheetTimer: null,
    lastFocus: null,
    player: null,
    toastTimer: null,
    deferredPrompt: null,
    installing: false,
    confirmLastFocus: null,
  };

  function saveStore() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
      return true;
    } catch (error) {
      if (!storageWarned) {
        storageWarned = true;
        showToast("浏览器未允许本地存储，本次学习进度将无法保存");
      }
      return false;
    }
  }

  function todayKey() {
    return dateKey();
  }

  function progressFor(id) {
    return store.progress[id] || null;
  }

  function statusFor(word) {
    const progress = progressFor(word.id);
    if (!progress) return { key: "new", label: "未学" };
    if ((progress.stage || 0) === 0 && progress.seen > 0) return { key: "again", label: "不熟" };
    if (progress.due && progress.due <= todayKey()) return { key: "due", label: "待复习" };
    if ((progress.stage || 0) >= 3) return { key: "mastered", label: "已掌握" };
    return { key: "learned", label: "已学" };
  }

  function computeStreak() {
    let cursor = todayKey();
    if (!isComplete(cursor)) cursor = addDays(cursor, -1);
    let streak = 0;
    while (isComplete(cursor) && streak < 3650) {
      streak += 1;
      cursor = addDays(cursor, -1);
    }
    return streak;
  }

  function isComplete(key) {
    const entry = store.history[key];
    return Boolean(entry && entry.completed && entry.total > 0);
  }

  function dueCount() {
    const today = todayKey();
    return Object.values(store.progress).filter((progress) => progress.due && progress.due <= today).length;
  }

  function learnedCount() {
    return Object.keys(store.progress).length;
  }

  function masteredCount() {
    return Object.values(store.progress).filter((progress) => (progress.stage || 0) >= 3).length;
  }

  function studyDaysCount() {
    return Object.values(store.history).filter((entry) => entry && entry.studied > 0).length;
  }

  function buildPlan(key) {
    const target = store.settings.dailyTarget;
    const due = WORDS.filter((word) => {
      const progress = progressFor(word.id);
      return Boolean(progress && progress.due && progress.due <= key);
    }).sort((a, b) => {
      const pa = progressFor(a.id);
      const pb = progressFor(b.id);
      return (
        String(pa.due).localeCompare(String(pb.due)) ||
        (pa.stage || 0) - (pb.stage || 0) ||
        a.lesson - b.lesson
      );
    });

    const reviewQuota = target <= 5 ? 2 : 3;
    const ids = [];
    const chosen = new Set();

    for (const word of due) {
      if (ids.length >= reviewQuota) break;
      ids.push(word.id);
      chosen.add(word.id);
    }

    for (const word of NEW_WORD_ORDER) {
      if (ids.length >= target) break;
      if (chosen.has(word.id) || progressFor(word.id)) continue;
      ids.push(word.id);
      chosen.add(word.id);
    }

    for (const word of due) {
      if (ids.length >= target) break;
      if (chosen.has(word.id)) continue;
      ids.push(word.id);
      chosen.add(word.id);
    }

    if (ids.length < target) {
      const oldest = WORDS.filter((word) => progressFor(word.id) && !chosen.has(word.id)).sort((a, b) => {
        const pa = progressFor(a.id);
        const pb = progressFor(b.id);
        return (
          String(pa.last || "").localeCompare(String(pb.last || "")) ||
          (pa.stage || 0) - (pb.stage || 0)
        );
      });
      for (const word of oldest) {
        if (ids.length >= target) break;
        ids.push(word.id);
        chosen.add(word.id);
      }
    }

    return { ids, results: {}, target, createdAt: Date.now() };
  }

  function syncHistory(key) {
    const record = store.plans[key];
    if (!record) return;
    const total = record.ids.length;
    const done = record.ids.filter((id) => record.results && record.results[id]).length;
    const previous = store.history[key] || { studied: 0, total: 0, completed: false };
    store.history[key] = {
      ...previous,
      studied: done,
      total,
      completed: Boolean(previous.completed || (total > 0 && done === total)),
    };
  }

  function ensureTodayPlan() {
    const key = todayKey();
    if (key !== state.todayKey) {
      state.todayKey = key;
      state.index = 0;
      state.autoIndex = true;
    }

    let record = store.plans[key];
    if (!record || !Array.isArray(record.ids)) {
      record = buildPlan(key);
      store.plans[key] = record;
      state.autoIndex = true;
      saveStore();
    }

    record.ids = record.ids.filter((id) => BY_ID.has(id));
    if (!record.results || typeof record.results !== "object") record.results = {};
    state.plan = record;
    syncHistory(key);

    if (state.autoIndex) {
      const first = findNextUngraded(record, 0);
      if (first >= 0) state.index = first;
      state.autoIndex = false;
    }

    if (!record.ids.length) state.index = 0;
    else if (state.index >= record.ids.length || state.index < 0) state.index = 0;
    saveStore();
  }

  function findNextUngraded(record, start = 0) {
    if (!record || !record.ids.length) return -1;
    const length = record.ids.length;
    for (let offset = 0; offset < length; offset += 1) {
      const index = (start + offset) % length;
      if (!record.results[record.ids[index]]) return index;
    }
    return -1;
  }

  function planDoneCount(record = state.plan) {
    if (!record) return 0;
    return record.ids.filter((id) => record.results[id]).length;
  }

  function renderChrome() {
    const streak = computeStreak();
    const streakText = $("#streak-text");
    const streakPill = $("#streak-pill");
    if (streakText) streakText.textContent = streak > 0 ? `${streak} 天` : "0 天";
    if (streakPill) {
      streakPill.setAttribute(
        "aria-label",
        streak > 0 ? `连续学习 ${streak} 天，查看学习记录` : "查看学习记录",
      );
    }
  }

  function renderToday() {
    ensureTodayPlan();
    const view = $("#view-today");
    if (!view) return;

    if (!WORDS.length) {
      view.innerHTML = `
        <div class="empty-state" style="margin-top:30px">
          <div class="empty-icon">!</div>
          <h3>词库没有加载成功</h3>
          <p>请确认 data/words.js 和 index.html 在同一个文件夹中。</p>
          <button class="clear-inline" type="button" data-action="reload">重新加载</button>
        </div>`;
      return;
    }

    const record = state.plan;
    const total = record.ids.length;
    const done = planDoneCount(record);
    const complete = total > 0 && done >= total;
    const percent = total ? Math.round((done / total) * 100) : 0;
    const circumference = 188.5;
    const offset = circumference * (1 - percent / 100);
    const streak = computeStreak();
    const now = new Date();
    const topicNames = [...new Set(record.ids.map((id) => (BY_ID.get(id) || {}).topic).filter(Boolean))];
    const topicText = topicNames.length > 2 ? "综合复习" : topicNames.join(" · ");
    const dateLine = `${VN_WEEKDAYS[now.getDay()]} · ${now.getDate()} THÁNG ${now.getMonth() + 1}`;

    const hero = `
      <section class="hero">
        <div class="hero-copy">
          <p class="eyebrow">${dateLine}</p>
          <h1>${complete ? "今天，<span class=\"hero-number\">学完了</span>。" : `今天，学 <span class="hero-number">${total}</span> 个词`}</h1>
          <p class="hero-sub">${complete ? `已连续 ${streak} 天 · 今天完成 ${total} 个词` : `${done}/${total} 已完成 · 今日主题：${topicText || "入门词汇"}`}</p>
        </div>
        <div class="progress-ring" role="img" aria-label="今日完成 ${percent}%">
          <svg viewBox="0 0 72 72" aria-hidden="true">
            <circle class="ring-track" cx="36" cy="36" r="30"></circle>
            <circle class="ring-fill" cx="36" cy="36" r="30" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"></circle>
          </svg>
          <span class="ring-label"><strong>${done}/${total}</strong><small>完成</small></span>
        </div>
      </section>`;

    const rail = renderPlanRail(record, complete);
    const lower = complete
      ? renderCompletion(record, streak)
      : renderActiveWord(record) + `
        <div class="info-strip">
          <span class="info-dot">i</span>
          <span>谐音只帮助记忆；通用词使用自动拼音近似。越南语有 6 个声调，请以 IPA 和音频为准。</span>
        </div>`;

    view.innerHTML = hero + rail + lower;
    renderGradeDock(record, complete);
  }

  function renderGradeDock(record, complete) {
    const dock = $("#grade-dock");
    if (!dock) return;
    const show =
      state.view === "today" &&
      !complete &&
      record &&
      record.ids.length > 0 &&
      window.scrollY > 80;
    dock.hidden = !show;
    document.body.classList.toggle("grade-dock-visible", show);
    if (!show) return;
    const id = record.ids[state.index] || record.ids[0];
    const result = record.results[id];
    $$("button", dock).forEach((button) => {
      const active = button.dataset.result === result;
      button.classList.toggle("is-selected", active);
      button.setAttribute("aria-pressed", String(active));
    });
  }

  function updateGradeDock() {
    if (!state.plan) return;
    const done = planDoneCount(state.plan);
    renderGradeDock(state.plan, done >= state.plan.ids.length);
  }

  function renderPlanRail(record, complete) {
    const dots = record.ids
      .map((id, index) => {
        const word = BY_ID.get(id);
        if (!word) return "";
        const result = record.results[id];
        const classes = [
          "plan-dot",
          result ? "is-done" : "",
          !complete && index === state.index ? "is-current" : "",
        ]
          .filter(Boolean)
          .join(" ");
        return `<button class="${classes}" type="button" data-action="jump-word" data-index="${index}" aria-label="${escapeHtml(
          word.word,
        )}${result ? "，已学" : "，未学"}" title="${escapeHtml(word.word)}">${
          result ? icon("check") : index + 1
        }</button>`;
      })
      .join("");
    return `<div class="plan-rail" aria-label="今日单词进度">${dots}</div>`;
  }

  function renderActiveWord(record) {
    if (!record.ids.length) {
      return `
        <div class="empty-state">
          <div class="empty-icon">◌</div>
          <h3>今天没有待学单词</h3>
          <p>词库暂时没有可推荐的词，去词库自由复习吧。</p>
        </div>`;
    }

    const id = record.ids[state.index] || record.ids[0];
    const word = BY_ID.get(id);
    if (!word) return "";
    const result = record.results[id];
    const wordClass = `word${isLongWord(word.word) ? " is-long" : ""}${
      isVeryLongWord(word.word) ? " is-very-long" : ""
    }`;

    return `
      <article class="word-card" aria-label="${escapeHtml(word.word)}">
        <div class="card-head">
          <span class="source-chip">${escapeHtml(word.source)}</span>
          <span class="pos-chip">${escapeHtml(word.pos)}</span>
        </div>
        <div class="word-main">
          <div class="word-text">
            <h2 class="${wordClass}">${escapeHtml(word.word)}</h2>
            <p class="ipa"><span>IPA</span>/${escapeHtml(word.ipa)}/</p>
          </div>
          <div class="audio-stack">
            <button class="audio-main" type="button" data-action="play-word" data-id="${word.id}" aria-label="播放 ${escapeHtml(
              word.word,
            )} 的标准发音">${icon("volume")}</button>
            <button class="slow-btn" type="button" data-action="play-slow" data-id="${word.id}">0.7× 慢速</button>
          </div>
        </div>
        ${
          store.settings.showHomophone
            ? `<div class="homophone"><span class="label">${
                word.source.startsWith("通用") ? "拼音近似" : "中文谐音"
              }</span><span class="value">${escapeHtml(
                word.homophone,
              )}</span></div>`
            : ""
        }
        <p class="meaning">${escapeHtml(word.meaning)}</p>
        <div class="example">
          <div class="example-head">
            <span class="example-label">例句 · VÍ DỤ</span>
            <button class="audio-round" type="button" data-action="play-example" data-id="${word.id}" aria-label="播放例句">${icon(
              "volume",
            )}</button>
          </div>
          <p class="example-vi">${highlightExample(word.example, word.word)}</p>
          <p class="example-zh">${escapeHtml(word.exampleZh)}</p>
        </div>
        <div class="card-foot"><span>出处 · ${escapeHtml(word.source)}</span><span>河内音</span></div>
      </article>
      <div class="grade-row" aria-label="学习反馈">
        <button class="btn btn-again ${result === "again" ? "is-selected" : ""}" type="button" data-action="grade" data-result="again" aria-pressed="${
          result === "again"
        }">${icon("refresh")} 还不熟</button>
        <button class="btn btn-known ${result === "known" ? "is-selected" : ""}" type="button" data-action="grade" data-result="known" aria-pressed="${
          result === "known"
        }">${icon("check")} 记住了</button>
      </div>
      <p class="grade-hint">${
        result
          ? `已记录：${result === "known" ? "3 天后复习" : "明天再练"}，可以重新选择。`
          : "不熟 → 明天再练 · 记住 → 按间隔安排复习"
      }</p>
      ${
        word.tip
          ? `<div class="pron-tip"><strong>发音提示</strong> · ${escapeHtml(word.tip)}</div>`
          : ""
      }`;
  }

  function isLongWord(word) {
    return word.length > 8 || word.includes(" ");
  }

  function isVeryLongWord(word) {
    return word.length > 12;
  }

  function renderCompletion(record, streak) {
    const known = record.ids.filter((id) => record.results[id] === "known").length;
    const again = record.ids.filter((id) => record.results[id] === "again").length;
    const total = record.ids.length;
    const inPlan = new Set(record.ids);
    const unseen = WORDS.filter((word) => !progressFor(word.id) && !inPlan.has(word.id)).length;
    const remaining = WORDS.filter((word) => !inPlan.has(word.id)).length;
    const moreLabel = unseen > 0 ? `再学 ${Math.min(store.settings.dailyTarget, unseen)} 个新词` : remaining > 0 ? "再复习几个词" : "";
    const recap = record.ids
      .map((id) => {
        const word = BY_ID.get(id);
        const result = record.results[id];
        if (!word) return "";
        return `
          <div class="recap-row">
            <button class="recap-main" type="button" data-action="open-word" data-id="${word.id}">
              <div class="recap-word">
                <strong>${escapeHtml(word.word)}</strong>
                <span class="result-badge ${result === "known" ? "known" : "again"}">${
                  result === "known" ? "记住了" : "再练"
                }</span>
              </div>
              <p>${escapeHtml(word.meaning)}</p>
            </button>
            <button class="audio-round" type="button" data-action="play-word" data-id="${word.id}" aria-label="播放 ${escapeHtml(
              word.word,
            )} 的发音">${icon("volume")}</button>
          </div>`;
      })
      .join("");

    return `
      <section class="complete-card">
        <div class="complete-badge">${icon("check")}</div>
        <p class="eyebrow">HOÀN THÀNH</p>
        <h2 class="complete-title">今天的词，学完了。</h2>
        <p class="complete-sub">${streak > 0 ? `已连续学习 ${streak} 天。` : ""}复习时间已经按你的反馈安排好。</p>
        <div class="complete-stats">
          <div class="complete-stat"><strong>${known}</strong><span>记住了</span></div>
          <div class="complete-stat"><strong>${again}</strong><span>明天再练</span></div>
        </div>
        <div class="complete-actions">
          ${
            moreLabel
              ? `<button class="btn btn-primary" type="button" data-action="learn-more">${icon(
                  "arrowRight",
                )} ${moreLabel}</button>`
              : ""
          }
          <button class="text-link" type="button" data-action="go-library">${icon("book")} 去词库自由复习</button>
        </div>
        <p class="grade-hint">今日共 ${total} 个词 · 数据只保存在本机</p>
      </section>
      <section class="recap" aria-label="今日单词回顾">
        <div class="section-heading"><h2>今日单词</h2><p>点击查看详情</p></div>
        <div class="recap-list">${recap}</div>
      </section>`;
  }

  function renderLibrary() {
    const view = $("#view-library");
    if (!view) return;
    const filters = [
      ["all", "全部", WORDS.length],
      ["textbook", "教材", WORDS.filter((word) => !word.source.startsWith("通用")).length],
      ["general", "通用", WORDS.filter((word) => word.source.startsWith("通用")).length],
      ["again", "不熟", WORDS.filter(isAgain).length],
      ["learned", "已学会", WORDS.filter(isLearned).length],
    ];
    const chips = filters
      .map(
        ([key, label, count]) =>
          `<button class="chip ${state.libraryFilter === key ? "is-active" : ""}" type="button" data-action="filter-library" data-filter="${key}">${label} <small>${count}</small></button>`,
      )
      .join("");

    view.innerHTML = `
      <div class="page-head">
        <p class="eyebrow">TỪ VỰNG</p>
        <h1>词库</h1>
        <p>教材词按课次归类，通用词按首字母归类；不熟和已学会的词单独集中。</p>
      </div>
      <div class="search-box">
        ${icon("search")}
        <input id="library-search" type="search" inputmode="search" autocomplete="off" placeholder="搜索越南语、中文或拼音" value="${escapeHtml(
          state.libraryQuery,
        )}" aria-label="搜索词库">
        <button class="clear-search" id="clear-search" type="button" data-action="clear-search" aria-label="清空搜索" ${
          state.libraryQuery ? "" : "hidden"
        }>${icon("x")}</button>
      </div>
      <div class="filter-scroller" id="filter-chips" aria-label="按类别筛选">${chips}</div>
      <div class="library-meta">
        <span id="library-count"></span>
        <div class="library-tools">
          <span class="library-hint">IPA · 河内音</span>
          <button class="autoplay-btn" id="autoplay-btn" type="button" data-action="toggle-autoplay">▶ 自动播放</button>
        </div>
      </div>
      <div class="library-list" id="library-list"></div>`;
    renderLibraryList();
  }

  function isAgain(word) {
    const progress = progressFor(word.id);
    return Boolean(progress && progress.seen > 0 && (progress.stage || 0) === 0);
  }

  function isLearned(word) {
    const progress = progressFor(word.id);
    return Boolean(progress && progress.seen > 0 && (progress.stage || 0) >= 1);
  }

  function filteredLibraryWords() {
    const query = normalize(state.libraryQuery.trim());
    return WORDS.filter((word) => {
      const general = word.source.startsWith("通用");
      if (state.libraryFilter === "textbook" && general) return false;
      if (state.libraryFilter === "general" && !general) return false;
      if (state.libraryFilter === "again" && !isAgain(word)) return false;
      if (state.libraryFilter === "learned" && !isLearned(word)) return false;
      if (!query) return true;
      return normalize(
        [
          word.word,
          word.ipa,
          word.homophone,
          word.meaning,
          word.example,
          word.exampleZh,
          word.topic,
          word.source,
        ].join(" "),
      ).includes(query);
    });
  }

  function libraryGroups(words) {
    const filter = state.libraryFilter;
    if (filter === "again") {
      const groups = [];
      for (const [general, title] of [
        [false, "教材词 · 需要加强"],
        [true, "通用词 · 需要加强"],
      ]) {
        const items = words.filter((word) => word.source.startsWith("通用") === general);
        if (items.length) groups.push({ key: `${general}-again`, title, words: items });
      }
      return groups;
    }

    const textbook = words.filter((word) => !word.source.startsWith("通用"));
    const general = words.filter((word) => word.source.startsWith("通用"));
    const groups = [];
    const textbookPrefix = filter === "all" ? "教材词 · " : filter === "learned" ? "已学会 · " : "";
    const generalPrefix = filter === "learned" ? "已学会 · " : "";

    if (filter !== "general" && textbook.length) {
      const byLesson = new Map();
      for (const word of textbook) {
        if (!byLesson.has(word.lesson)) byLesson.set(word.lesson, []);
        byLesson.get(word.lesson).push(word);
      }
      for (const [lesson, items] of [...byLesson.entries()].sort((a, b) => a[0] - b[0])) {
        groups.push({
          key: `lesson-${lesson}`,
          title: `${textbookPrefix}第 ${lesson} 课 · ${items[0].topic}`,
          words: items,
        });
      }
    }

    if (filter !== "textbook" && general.length) {
      const byLetter = new Map();
      for (const word of general) {
        const letter = (word.word[0] || "#").toUpperCase();
        if (!byLetter.has(letter)) byLetter.set(letter, []);
        byLetter.get(letter).push(word);
      }
      for (const [letter, items] of [...byLetter.entries()].sort((a, b) => a[0].localeCompare(b[0], "vi"))) {
        groups.push({ key: `letter-${letter}`, title: `${generalPrefix}通用词 · ${letter}`, words: items });
      }
    }
    return groups;
  }

  function renderLibraryRow(word, autoplayId = null) {
    const status = statusFor(word);
    const shortSource = word.source.startsWith("通用") ? "通用" : word.source.replace("《越南语123》", "");
    return `
      <article class="lib-row ${autoplayId === word.id ? "is-autoplay" : ""}" data-id="${word.id}">
        <button class="lib-main" type="button" data-action="open-word" data-id="${word.id}" aria-label="查看 ${escapeHtml(
          word.word,
        )}">
          <div class="lib-word-line">
            <span class="lib-word">${escapeHtml(word.word)}</span>
            <span class="lib-ipa">/${escapeHtml(word.ipa)}/</span>
          </div>
          <p class="lib-meaning">${escapeHtml(word.meaning)} · ${escapeHtml(shortSource)}</p>
        </button>
        <div class="lib-side">
          <span class="status-badge is-${status.key}">${status.label}</span>
          <button class="audio-round" type="button" data-action="play-word" data-id="${word.id}" aria-label="播放 ${escapeHtml(
            word.word,
          )} 的发音">${icon("volume")}</button>
        </div>
      </article>`;
  }

  function renderLibraryList() {
    const list = $("#library-list");
    if (!list) return;
    const filtered = filteredLibraryWords();
    const count = $("#library-count");
    if (count) {
      count.innerHTML = `<strong>${filtered.length}</strong> 个词 · 已学会 ${WORDS.filter(isLearned).length} · 不熟 ${WORDS.filter(isAgain).length}`;
    }
    const clearButton = $("#clear-search");
    if (clearButton) clearButton.hidden = !state.libraryQuery;

    if (!filtered.length) {
      const emptyTitle =
        state.libraryFilter === "again"
          ? "还没有不熟的词"
          : state.libraryFilter === "learned"
            ? "还没有已学会的词"
            : "没有找到这个词";
      const emptyText =
        state.libraryFilter === "again"
          ? "在今日学习里点“还不熟”，这些词会集中到这里，方便自动播放加强。"
          : state.libraryFilter === "learned"
            ? "在今日学习里点“记住了”，这些词会集中到这里，也可以自动播放复习。"
            : "试试中文释义、越南语拼写，或者换一个类别。";
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">⌕</div>
          <h3>${emptyTitle}</h3>
          <p>${emptyText}</p>
          <button class="clear-inline" type="button" data-action="clear-search">清空搜索</button>
        </div>`;
      updateAutoplayButton();
      return;
    }

    const groups = libraryGroups(filtered);
    const currentId = state.autoplay
      ? (state.autoplay.list[state.autoplay.index] || {}).id
      : null;
    list.innerHTML = groups
      .map(
        (group) => `
          <section class="lib-group">
            <div class="lib-group-head"><span>${escapeHtml(group.title)}</span><small>${group.words.length} 词</small></div>
            <div class="lib-group-rows">${group.words.map((word) => renderLibraryRow(word, currentId)).join("")}</div>
          </section>`,
      )
      .join("");
    updateAutoplayButton();
  }

  function updateAutoplayButton() {
    const button = $("#autoplay-btn");
    if (!button) return;
    if (state.autoplay) {
      const position = Math.min(state.autoplay.index + 1, state.autoplay.list.length);
      button.textContent = `■ 停止 ${position}/${state.autoplay.list.length}`;
      button.classList.add("is-active");
    } else {
      button.textContent = "▶ 自动播放";
      button.classList.remove("is-active");
    }
  }

  function autoplayQueue() {
    return libraryGroups(filteredLibraryWords()).flatMap((group) => group.words);
  }

  function startAutoplay(startId = null) {
    const words = autoplayQueue();
    if (!words.length) {
      showToast("当前分类没有可播放的词");
      return;
    }
    stopAutoplay(false);
    if (state.player) state.player.pause();
    const anchorId = startId || state.libraryAnchorId;
    let index = anchorId ? words.findIndex((word) => word.id === anchorId) : 0;
    if (index < 0) index = 0;
    state.libraryAnchorId = words[index].id;
    state.autoplay = { list: words, index, timer: null };
    renderLibraryList();
    playAutoplayCurrent();
  }

  function playAutoplayCurrent() {
    const autoplay = state.autoplay;
    if (!autoplay) return;
    if (autoplay.index >= autoplay.list.length) {
      state.libraryAnchorId = null;
      stopAutoplay(false);
      updateAutoplayButton();
      showToast("自动播放完成");
      return;
    }
    const word = autoplay.list[autoplay.index];
    state.libraryAnchorId = word.id;
    $$(".lib-row.is-autoplay").forEach((row) => row.classList.remove("is-autoplay"));
    const row = document.querySelector(`.lib-row[data-id="${word.id}"]`);
    if (row) {
      row.classList.add("is-autoplay");
      row.scrollIntoView({ block: "center", behavior: "smooth" });
    }
    updateAutoplayButton();
    playAudio(word.id, "word", null, () => {
      if (state.autoplay !== autoplay) return;
      autoplay.timer = setTimeout(() => {
        if (state.autoplay !== autoplay) return;
        autoplay.index += 1;
        playAutoplayCurrent();
      }, 550);
    });
  }

  function stopAutoplay(showMessage = true) {
    if (!state.autoplay) return;
    clearTimeout(state.autoplay.timer);
    state.autoplay = null;
    if (state.player) state.player.pause();
    clearPlayingState();
    $$(".lib-row.is-autoplay").forEach((row) => row.classList.remove("is-autoplay"));
    updateAutoplayButton();
    if (showMessage) showToast("已停止自动播放");
  }

  function toggleAutoplay() {
    if (state.autoplay) stopAutoplay();
    else startAutoplay();
  }

  function renderPhonetics() {
    const view = $("#view-phonetics");
    if (!view) return;

    const vowelCards = PHONETIC_DATA.vowels
      .map(
        (item) => `
          <article class="phonetic-card">
            <div class="phonetic-top">
              <span class="phonetic-symbol">${escapeHtml(item.symbol)}</span>
              <button class="audio-round" type="button" data-action="play-phonetic" data-id="${item.id}" aria-label="播放 ${escapeHtml(
                item.symbol,
              )} 的发音">${icon("volume")}</button>
            </div>
            <div class="phonetic-ipa">/${escapeHtml(item.ipa)}/</div>
            <div class="phonetic-example">${escapeHtml(item.example)} <span>${escapeHtml(item.meaning)}</span></div>
            <p class="phonetic-tip">${escapeHtml(item.tip)}</p>
          </article>`,
      )
      .join("");

    const consonantCards = PHONETIC_DATA.consonants
      .map(
        (item) => `
          <article class="phonetic-card">
            <div class="phonetic-top">
              <span class="phonetic-symbol phonetic-symbol-text">${escapeHtml(item.symbol)}</span>
              <button class="audio-round" type="button" data-action="play-phonetic" data-id="${item.id}" aria-label="播放 ${escapeHtml(
                item.symbol,
              )} 的发音">${icon("volume")}</button>
            </div>
            <div class="phonetic-ipa">/${escapeHtml(item.ipa)}/</div>
            <div class="phonetic-example">${escapeHtml(item.example)} <span>${escapeHtml(item.meaning)}</span></div>
            <p class="phonetic-tip">${escapeHtml(item.tip)}</p>
          </article>`,
      )
      .join("");

    const toneCards = PHONETIC_DATA.tones
      .map(
        (item) => `
          <article class="tone-card">
            <div class="tone-head">
              <span class="tone-mark">${escapeHtml(item.mark)}</span>
              <div><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.mark)}</small></div>
              <button class="audio-round" type="button" data-action="play-phonetic" data-id="${item.id}" aria-label="播放 ${escapeHtml(
                item.symbol,
              )} 的发音">${icon("volume")}</button>
            </div>
            <div class="tone-example">${escapeHtml(item.example)} <span>${escapeHtml(item.meaning)}</span></div>
            <p class="phonetic-tip">${escapeHtml(item.tip)}</p>
          </article>`,
      )
      .join("");

    view.innerHTML = `
      <div class="page-head">
        <p class="eyebrow">PHÁT ÂM · 发音</p>
        <h1>语音基础</h1>
        <p>元音、辅音和 6 个声调。按钮播放的是字母音，不是示例词。</p>
      </div>
      <div class="phonetic-note">
        <span class="info-dot">i</span>
        <span>元音播放字母音；辅音播放“辅音 + ơ”的读法（如 bờ、cờ），不是例词。声调仍以 ma 系列示范。</span>
      </div>
      <section class="phonetic-section">
        <div class="section-heading"><h2>元音</h2><p>${PHONETIC_DATA.vowels.length} 个</p></div>
        <div class="phonetic-grid">${vowelCards}</div>
      </section>
      <section class="phonetic-section">
        <div class="section-heading"><h2>辅音</h2><p>${PHONETIC_DATA.consonants.length} 个</p></div>
        <div class="phonetic-grid">${consonantCards}</div>
      </section>
      <section class="phonetic-section">
        <div class="section-heading"><h2>声调</h2><p>以 ma 为例</p></div>
        <div class="tone-list">${toneCards}</div>
      </section>
      <p class="footnote">© 2026 ${APP_AUTHOR} · v${APP_VERSION} · 保留所有权利</p>`;
  }

  function findPhonetic(id) {
    return [...PHONETIC_DATA.vowels, ...PHONETIC_DATA.consonants, ...PHONETIC_DATA.tones].find(
      (item) => item.id === id,
    );
  }

  function playPhonetic(id) {
    const item = findPhonetic(id);
    if (!item) return;
    const player = state.player || $("#player");
    if (!player) return;
    state.player = player;
    const source = `audio/phonetics/${id}.mp3`;
    player.pause();
    player.onended = null;
    player.onerror = null;
    player.src = source;
    player.currentTime = 0;
    player.playbackRate = Number(store.settings.speed) || 1;
    player.onended = clearPlayingState;
    player.onerror = () => {
      clearPlayingState();
      speakFallback(item.example, Number(store.settings.speed) || 1);
    };
    clearPlayingState();
    $$(`[data-action="play-phonetic"][data-id="${id}"]`).forEach((button) =>
      button.classList.add("is-playing"),
    );
    const promise = player.play();
    if (promise && typeof promise.catch === "function") {
      promise.catch((error) => {
        if (error && error.name === "AbortError") return;
        clearPlayingState();
        speakFallback(item.example, Number(store.settings.speed) || 1);
      });
    }
  }

  function renderMe() {
    const view = $("#view-me");
    if (!view) return;
    const streak = computeStreak();
    const days = studyDaysCount();
    const learned = learnedCount();
    const mastered = masteredCount();
    const due = dueCount();

    const last7 = Array.from({ length: 7 }, (_, index) => addDays(todayKey(), index - 6));
    const counts = last7.map((key) => (store.history[key] && store.history[key].studied) || 0);
    const max = Math.max(5, ...counts);
    const dayLabels = ["日", "一", "二", "三", "四", "五", "六"];
    const bars = last7
      .map((key, index) => {
        const count = counts[index];
        const height = Math.max(3, Math.round((count / max) * 74));
        const isToday = key === todayKey();
        return `
          <div class="activity-day ${isToday ? "is-today" : ""}">
            <span class="activity-count">${count || ""}</span>
            <div class="activity-track"><span class="activity-fill" style="height:${height}px"></span></div>
            <span class="activity-label">${dayLabels[parseDate(key).getDay()]}</span>
          </div>`;
      })
      .join("");

    const targetButtons = [3, 5, 8]
      .map(
        (value) =>
          `<button class="${store.settings.dailyTarget === value ? "is-active" : ""}" type="button" data-action="set-target" data-value="${value}">${value}</button>`,
      )
      .join("");

    const speedButtons = [
      [0.75, "0.75×"],
      [1, "1×"],
      [1.25, "1.25×"],
    ]
      .map(
        ([value, label]) =>
          `<button class="${Number(store.settings.speed) === value ? "is-active" : ""}" type="button" data-action="set-speed" data-value="${value}">${label}</button>`,
      )
      .join("");

    const uiSizeButtons = [
      ["compact", "紧凑"],
      ["standard", "标准"],
      ["large", "宽屏"],
    ]
      .map(
        ([value, label]) =>
          `<button class="${store.settings.uiSize === value ? "is-active" : ""}" type="button" data-action="set-ui-size" data-value="${value}">${label}</button>`,
      )
      .join("");

    const caption =
      streak > 0
        ? `保持节奏，明天继续。共学习 ${days} 天。`
        : days > 0
          ? `已经学习 ${days} 天，继续加油。`
          : "完成今天的学习，开启第一天。";

    view.innerHTML = `
      <div class="page-head">
        <p class="eyebrow">HỒ SƠ HỌC TẬP</p>
        <h1>我的学习</h1>
        <p>把每天的 ${store.settings.dailyTarget} 个词，慢慢变成自己的。</p>
      </div>
      <section class="streak-hero">
        <div class="streak-hero-top">
          <div>
            <p class="eyebrow">CHUỖI NGÀY HỌC</p>
            <p class="streak-value">${streak}<span>天连续学习</span></p>
            <p class="streak-caption">${caption}</p>
          </div>
          <div class="streak-star" aria-hidden="true">★</div>
        </div>
        <div class="profile-stats">
          <div class="profile-stat"><strong>${learned}</strong><span>已学单词</span></div>
          <div class="profile-stat"><strong>${mastered}</strong><span>已掌握</span></div>
          <div class="profile-stat"><strong>${due}</strong><span>待复习</span></div>
        </div>
      </section>

      <div class="section-heading"><h2>最近 7 天</h2><p>每日学习词数</p></div>
      <div class="panel activity"><div class="activity-bars">${bars}</div></div>

      <div class="section-heading"><h2>学习设置</h2><p>按自己的节奏来</p></div>
      <div class="panel settings-panel">
        <div class="setting-row">
          <div class="setting-copy"><strong>每日词数</strong><span>明天起按新数量推荐</span></div>
          <div class="segmented" aria-label="每日词数">${targetButtons}</div>
        </div>
        <div class="setting-row">
          <div class="setting-copy"><strong>播放速度</strong><span>例句音频也会一起调整</span></div>
          <div class="segmented" aria-label="播放速度">${speedButtons}</div>
        </div>
        <div class="setting-row">
          <div class="setting-copy"><strong>显示大小</strong><span>紧凑适合小屏；宽屏用于平板/桌面</span></div>
          <div class="segmented" aria-label="显示大小">${uiSizeButtons}</div>
        </div>
        <div class="setting-row">
          <div class="setting-copy"><strong>显示中文谐音</strong><span>谐音只作辅助，建议以 IPA 为准</span></div>
          <button class="switch ${store.settings.showHomophone ? "is-on" : ""}" type="button" role="switch" aria-checked="${
            store.settings.showHomophone
          }" aria-label="显示中文谐音" data-action="toggle-homophone"></button>
        </div>
      </div>

      <div class="section-heading"><h2>安装到手机</h2><p>像 App 一样打开</p></div>
      ${renderInstallCard()}

      <div class="section-heading"><h2>关于</h2><p>词表与发音说明</p></div>
      <details class="panel about-card">
        <summary>词表、音标、隐私与版权</summary>
        <div class="about-body">
          <p><strong>词表：</strong>${WORDS.filter((word) => !word.source.startsWith("通用")).length} 个《越南语123》入门词（第 1、2、3、4、5、10、12、13、14 课主题）+ ${WORDS.filter((word) => word.source.startsWith("通用")).length} 个通用高频词（1000mostcommonwords.com 常用词去重，并补充日常词）。通用词不是教材原词表。</p>
          <p><strong>通用词释义：</strong>中文释义由开放词典与机器翻译整理；IPA 来自 dict.minhqnd.com（CC BY-SA 4.0），部分为自动生成；通用词的中文谐音是自动拼音近似，教材词为人工标注。</p>
          <p><strong>发音：</strong>标注河内音 IPA 和近似读音。谐音无法准确表达越南语声调，请以音频和 IPA 为准。</p>
          <p><strong>IPA 调符：</strong>˧ 平声 · ˨˩ 玄声 · ˧˥ 锐声 · ˧˩˧ 问声 · ˧ˀ˥ 跌声 · ˧ˀ˩ 重声。</p>
          <p><strong>例句：</strong>教材词为教材/公开页面例句；通用词大部分来自 Tatoeba 真实例句（中文为机器翻译），少数为按词性生成的简单句，不是教材原句。</p>
          <p><strong>音频：</strong>由 Microsoft Edge 神经网络语音 vi-VN-HoaiMyNeural 预生成；1016 个单词和 1016 条例句都有离线音频，共约 20 MB。</p>
          <p><strong>版权：</strong>© 2026 ${APP_AUTHOR}。保留所有权利。第三方词表、例句和语音服务的许可见仓库 THIRD_PARTY_NOTICES.md。</p>
          <p><strong>版本：</strong>v${APP_VERSION} · 作者：${APP_AUTHOR}</p>
          <p><strong>隐私：</strong>学习进度只保存在本机浏览器，不上传服务器，也不需要登录。<a href="./privacy.html">查看隐私政策</a></p>
        </div>
      </details>

      <div class="panel danger-zone">
        <div class="danger-row">
          <div><strong>清除学习记录</strong><span>重新开始，设置会保留</span></div>
          <button class="danger-btn" type="button" data-action="reset-progress">清除</button>
        </div>
      </div>
      <p class="footnote">© 2026 ${APP_AUTHOR} · ${APP_NAME} Việt Từ v${APP_VERSION} · 保留所有权利</p>`;
  }

  function renderInstallCard() {
    if (isStandalone()) {
      return `
        <div class="install-card">
          <div class="install-icon">${icon("check")}</div>
          <div class="install-copy"><strong>已安装到桌面</strong><p>可以离线打开，随时复习。</p></div>
        </div>`;
    }
    if (state.deferredPrompt) {
      return `
        <div class="install-card">
          <div class="install-icon">${icon("download")}</div>
          <div class="install-copy"><strong>把越词通装到手机</strong><p>添加到主屏幕，像普通 App 一样使用。</p></div>
          <button class="install-btn" type="button" data-action="install-app" ${
            state.installing ? "disabled" : ""
          }>${state.installing ? "安装中" : "安装"}</button>
        </div>`;
    }
    return `
      <div class="install-card">
        <div class="install-icon">${icon("download")}</div>
        <div class="install-copy"><strong>添加到主屏幕</strong><p>用 Chrome 打开后，点右上角菜单 → “添加到主屏幕”。</p></div>
      </div>`;
  }

  function isStandalone() {
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.matchMedia("(display-mode: minimal-ui)").matches ||
      window.navigator.standalone === true
    );
  }

  function openSheet(id) {
    const word = BY_ID.get(id);
    if (!word) return;
    if (state.sheetTimer) clearTimeout(state.sheetTimer);
    state.lastFocus = document.activeElement;
    state.sheetWordId = id;
    renderSheet();
    const sheet = $("#sheet");
    if (!sheet) return;
    sheet.hidden = false;
    requestAnimationFrame(() => {
      sheet.classList.add("is-open");
      document.body.classList.add("sheet-open");
      const close = $(".sheet-close", sheet);
      if (close) close.focus({ preventScroll: true });
    });
  }

  function closeSheet() {
    const sheet = $("#sheet");
    if (!sheet || sheet.hidden) return;
    sheet.classList.remove("is-open");
    document.body.classList.remove("sheet-open");
    state.sheetWordId = null;
    if (state.sheetTimer) clearTimeout(state.sheetTimer);
    state.sheetTimer = setTimeout(() => {
      sheet.hidden = true;
      sheet.innerHTML = "";
    }, 290);
    if (state.lastFocus && typeof state.lastFocus.focus === "function") {
      state.lastFocus.focus({ preventScroll: true });
    }
  }

  function renderSheet() {
    const sheet = $("#sheet");
    const word = state.sheetWordId ? BY_ID.get(state.sheetWordId) : null;
    if (!sheet || !word) return;
    const progress = progressFor(word.id);
    const result = state.plan && state.plan.ids.includes(word.id) ? state.plan.results[word.id] : null;
    const status = sheetStatus(word, progress, result);
    const wordClass = `sheet-word${isLongWord(word.word) ? " is-long" : ""}${
      isVeryLongWord(word.word) ? " is-very-long" : ""
    }`;

    sheet.innerHTML = `
      <div class="sheet-backdrop" data-action="close-sheet"></div>
      <div class="sheet-panel" role="dialog" aria-modal="true" aria-labelledby="sheet-word">
        <div class="sheet-grabber" aria-hidden="true"></div>
        <div class="sheet-head">
          <span class="source-chip">${escapeHtml(word.source)}</span>
          <button class="sheet-close" type="button" data-action="close-sheet" aria-label="关闭">${icon("x")}</button>
        </div>
        <h2 class="${wordClass}" id="sheet-word">${escapeHtml(word.word)}</h2>
        <p class="sheet-ipa">/${escapeHtml(word.ipa)}/</p>
        <div class="sheet-audio-row">
          <button class="sheet-audio-btn is-main" type="button" data-action="play-word" data-id="${word.id}">${icon(
            "volume",
          )} 单词发音</button>
          <button class="sheet-audio-btn" type="button" data-action="play-slow" data-id="${word.id}">0.7× 慢速</button>
          <button class="sheet-audio-btn" type="button" data-action="play-example" data-id="${word.id}">${icon(
            "volume",
          )} 例句</button>
        </div>
        ${
          store.settings.showHomophone
            ? `<div class="sheet-homophone"><strong>${
                word.source.startsWith("通用") ? "拼音近似 · 自动生成" : "中文谐音 · 仅辅助"
              }</strong>${escapeHtml(word.homophone)}</div>`
            : ""
        }
        <p class="sheet-meaning">${escapeHtml(word.meaning)}</p>
        ${
          word.tip
            ? `<div class="pron-tip"><strong>发音提示</strong> · ${escapeHtml(word.tip)}</div>`
            : ""
        }
        <div class="sheet-example">
          <div class="example-head"><span class="example-label">例句 · VÍ DỤ</span></div>
          <p class="example-vi">${highlightExample(word.example, word.word)}</p>
          <p class="example-zh">${escapeHtml(word.exampleZh)}</p>
        </div>
        <div class="sheet-status ${status.className}"><span class="status-dot"></span>${status.text}</div>
        <div class="sheet-actions">
          <button class="btn btn-again ${result === "again" ? "is-selected" : ""}" type="button" data-action="sheet-grade" data-id="${
            word.id
          }" data-result="again">${icon("refresh")} 明天再练</button>
          <button class="btn btn-known ${result === "known" ? "is-selected" : ""}" type="button" data-action="sheet-grade" data-id="${
            word.id
          }" data-result="known">${icon("check")} 记住了</button>
        </div>
        <p class="sheet-source">出处：${escapeHtml(word.source)} · 河内音 · 音标与谐音仅作学习辅助</p>
      </div>`;
  }

  function sheetStatus(word, progress, result) {
    if (result === "known") {
      return {
        className: "",
        text: `今日已记录为“记住了” · ${scheduleText((progress && progress.due) || todayKey())}复习`,
      };
    }
    if (result === "again") {
      return { className: "", text: "今日已记录为“还不熟” · 明天再练" };
    }
    if (!progress) {
      return { className: "is-new", text: "还没学过 · 建议先听两遍发音，再读例句" };
    }
    if (progress.due && progress.due <= todayKey()) {
      return { className: "", text: "今天该复习了" };
    }
    return {
      className: "",
      text: `已学 · 下次复习：${formatDateZh(progress.due)}（${scheduleText(progress.due)}）`,
    };
  }

  function applyGrade(id, result, { advance = false, announce = true } = {}) {
    const word = BY_ID.get(id);
    if (!word) return;
    const today = todayKey();
    const progress = {
      stage: 0,
      seen: 0,
      due: null,
      last: null,
      known: false,
      ...(progressFor(id) || {}),
    };
    progress.seen = (progress.seen || 0) + 1;
    progress.last = today;

    if (result === "known") {
      progress.stage = Math.min((progress.stage || 0) + 1, INTERVALS.length);
      progress.due = addDays(today, INTERVALS[progress.stage - 1] || 3);
      progress.known = progress.stage >= 3;
    } else {
      progress.stage = 0;
      progress.due = addDays(today, 1);
      progress.known = false;
    }

    store.progress[id] = progress;
    if (state.plan && state.plan.ids.includes(id)) {
      state.plan.results[id] = result;
      syncHistory(today);
    }
    saveStore();
    vibrate(12);

    if (advance && state.plan) {
      const next = findNextUngraded(state.plan, (state.index + 1) % state.plan.ids.length);
      if (next >= 0) state.index = next;
    }

    renderChrome();
    renderToday();
    if (state.sheetWordId === id) renderSheet();
    if (state.view === "me") renderMe();
    if (state.view === "library") renderLibraryList();

    if (announce) {
      showToast(
        result === "known"
          ? `记住了 · ${scheduleText(progress.due)}复习`
          : "没关系 · 明天再练一次",
      );
    }
  }

  function learnMore() {
    const record = state.plan;
    if (!record) return;
    const inPlan = new Set(record.ids);
    let candidates = NEW_WORD_ORDER.filter((word) => !progressFor(word.id) && !inPlan.has(word.id));
    if (!candidates.length) {
      candidates = NEW_WORD_ORDER.filter((word) => !inPlan.has(word.id)).sort((a, b) => {
        const pa = progressFor(a.id) || {};
        const pb = progressFor(b.id) || {};
        return (
          (pa.stage || 0) - (pb.stage || 0) ||
          String(pa.last || "").localeCompare(String(pb.last || ""))
        );
      });
    }
    const additions = candidates.slice(0, store.settings.dailyTarget).map((word) => word.id);
    if (!additions.length) {
      showToast("词库里的词都在今天计划里了，去词库自由复习吧");
      return;
    }
    record.ids.push(...additions);
    record.target = record.ids.length;
    syncHistory(todayKey());
    saveStore();
    const firstNew = record.ids.findIndex((id) => !record.results[id]);
    state.index = firstNew >= 0 ? firstNew : 0;
    renderChrome();
    renderToday();
    showToast(`已加入 ${additions.length} 个词，继续加油`);
  }

  function setTarget(value) {
    if (![3, 5, 8].includes(value)) return;
    store.settings.dailyTarget = value;
    saveStore();
    renderMe();
    renderChrome();
    showToast(`已设置为每天 ${value} 个词，明天起生效`);
  }

  function setSpeed(value) {
    if (![0.75, 1, 1.25].includes(value)) return;
    store.settings.speed = value;
    saveStore();
    renderMe();
    showToast(`播放速度：${value}×`);
  }

  function applyUiSize() {
    const value = ["compact", "standard", "large"].includes(store.settings.uiSize)
      ? store.settings.uiSize
      : "standard";
    document.documentElement.dataset.uiSize = value;
  }

  function setUiSize(value) {
    if (!["compact", "standard", "large"].includes(value)) return;
    store.settings.uiSize = value;
    saveStore();
    applyUiSize();
    renderMe();
    if (state.view === "today") renderToday();
    if (state.sheetWordId) renderSheet();
    const labels = { compact: "紧凑", standard: "标准", large: "宽屏" };
    showToast(`显示大小：${labels[value]}`);
  }

  function toggleHomophone() {
    store.settings.showHomophone = !store.settings.showHomophone;
    saveStore();
    renderMe();
    if (state.view === "today") renderToday();
    if (state.sheetWordId) renderSheet();
    showToast(store.settings.showHomophone ? "已显示中文谐音" : "已隐藏中文谐音");
  }

  function resetProgress() {
    const settings = { ...store.settings };
    store = createStore();
    store.settings = settings;
    state.plan = null;
    state.index = 0;
    state.todayKey = null;
    state.autoIndex = true;
    saveStore();
    closeConfirm();
    applyUiSize();
    ensureTodayPlan();
    renderChrome();
    if (state.view === "today") renderToday();
    if (state.view === "library") renderLibrary();
    if (state.view === "me") renderMe();
    showToast("学习记录已清除，今天重新开始");
  }

  function showConfirm() {
    const modal = $("#confirm");
    if (!modal) return;
    state.confirmLastFocus = document.activeElement;
    modal.hidden = false;
    const cancel = $(".btn-ghost", modal);
    if (cancel) cancel.focus({ preventScroll: true });
  }

  function closeConfirm() {
    const modal = $("#confirm");
    if (!modal || modal.hidden) return;
    modal.hidden = true;
    if (state.confirmLastFocus && typeof state.confirmLastFocus.focus === "function") {
      state.confirmLastFocus.focus({ preventScroll: true });
    }
  }

  function vibrate(duration) {
    if (navigator.vibrate) {
      try {
        navigator.vibrate(duration);
      } catch (error) {
        /* haptics are optional */
      }
    }
  }

  function showToast(message, duration = 2400) {
    const toast = $("#toast");
    if (!toast) return;
    if (state.toastTimer) clearTimeout(state.toastTimer);
    toast.textContent = message;
    toast.hidden = false;
    state.toastTimer = setTimeout(() => {
      toast.hidden = true;
    }, duration);
  }

  function speakFallback(text, rate = 1) {
    if (!("speechSynthesis" in window)) {
      showToast("发音文件没有加载成功，请检查 audio 文件夹");
      return;
    }
    try {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "vi-VN";
      utterance.rate = Math.min(1.4, Math.max(0.5, Number(rate) || 1));
      const voices = window.speechSynthesis.getVoices();
      const vietnamese = voices.find((voice) => (voice.lang || "").toLowerCase().startsWith("vi"));
      if (vietnamese) utterance.voice = vietnamese;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
      showToast(vietnamese ? "正在使用手机自带越南语语音" : "手机没有越南语语音，已尝试系统朗读");
    } catch (error) {
      showToast("无法播放发音，请检查手机媒体音量");
    }
  }

  function playAudio(id, type = "word", rate = null, onEnded = null) {
    const word = BY_ID.get(id);
    if (!word) return;
    const player = state.player || $("#player");
    if (!player) return;
    state.player = player;

    const source = type === "example" ? `audio/examples/${id}.mp3` : `audio/words/${id}.mp3`;
    const text = type === "example" ? word.example : word.word;
    const speed = rate == null ? Number(store.settings.speed) || 1 : rate;

    player.pause();
    player.onended = null;
    player.onerror = null;
    player.src = source;
    player.currentTime = 0;
    player.playbackRate = speed;
    player.onended = () => {
      clearPlayingState();
      if (onEnded) onEnded();
    };
    player.onerror = () => {
      clearPlayingState();
      speakFallback(text, speed);
      if (onEnded) setTimeout(onEnded, 1200);
    };

    markPlaying(id, type);
    const promise = player.play();
    if (promise && typeof promise.catch === "function") {
      promise.catch((error) => {
        if (error && error.name === "AbortError") return;
        clearPlayingState();
        speakFallback(text, speed);
        if (onEnded) setTimeout(onEnded, 1200);
      });
    }
  }

  function markPlaying(id, type) {
    clearPlayingState();
    const selectors =
      type === "example"
        ? `[data-action="play-example"][data-id="${id}"]`
        : `[data-action="play-word"][data-id="${id}"], [data-action="play-slow"][data-id="${id}"]`;
    $$(selectors).forEach((button) => button.classList.add("is-playing"));
    state.activeAudio = { id, type };
  }

  function clearPlayingState() {
    $$(".is-playing").forEach((button) => button.classList.remove("is-playing"));
    state.activeAudio = null;
  }

  function switchView(name, { scroll = true } = {}) {
    if (!["today", "library", "phonetics", "me"].includes(name)) name = "today";
    state.view = name;
    $$(".view").forEach((view) => {
      view.hidden = view.dataset.view !== name;
    });
    $$(".nav-btn").forEach((button) => {
      const active = button.dataset.view === name;
      button.classList.toggle("is-active", active);
      if (active) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    });

    if (name === "today") renderToday();
    if (name === "library") renderLibrary();
    if (name === "phonetics") renderPhonetics();
    if (name === "me") renderMe();
    renderChrome();
    if (name !== "library") {
      stopAutoplay(false);
      state.libraryAnchorId = null;
    }
    if (name !== "today") {
      const dock = $("#grade-dock");
      if (dock) dock.hidden = true;
      document.body.classList.remove("grade-dock-visible");
    }

    if (scroll) {
      const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
    }
  }

  async function installApp() {
    if (state.installing) return;
    if (!state.deferredPrompt) {
      showToast("请用 Chrome 菜单选择“添加到主屏幕”");
      return;
    }
    state.installing = true;
    if (state.view === "me") renderMe();
    try {
      state.deferredPrompt.prompt();
      const choice = await state.deferredPrompt.userChoice;
      if (choice && choice.outcome === "accepted") showToast("正在安装到手机…");
      else showToast("已取消安装");
    } catch (error) {
      showToast("安装没有完成，请从浏览器菜单添加");
    } finally {
      state.deferredPrompt = null;
      state.installing = false;
      if (state.view === "me") renderMe();
    }
  }

  function onDocumentClick(event) {
    const actionElement = event.target.closest("[data-action]");
    if (!actionElement) return;
    const action = actionElement.dataset.action;
    if (actionElement.tagName === "A" || actionElement.tagName === "BUTTON") {
      if (actionElement.getAttribute("href") === "#") event.preventDefault();
    }

    switch (action) {
      case "nav":
        switchView(actionElement.dataset.view || "today");
        break;
      case "jump-word": {
        const index = Number(actionElement.dataset.index);
        if (!Number.isInteger(index) || !state.plan) break;
        if (isComplete(todayKey())) {
          const id = state.plan.ids[index];
          if (id) openSheet(id);
        } else {
          state.index = index;
          renderToday();
        }
        break;
      }
      case "play-word":
        event.preventDefault();
        if (state.view === "library" && actionElement.closest(".lib-row")) {
          startAutoplay(actionElement.dataset.id);
          break;
        }
        if (state.autoplay) stopAutoplay(false);
        playAudio(actionElement.dataset.id, "word");
        break;
      case "play-slow":
        event.preventDefault();
        playAudio(actionElement.dataset.id, "word", 0.7);
        break;
      case "play-example":
        event.preventDefault();
        playAudio(actionElement.dataset.id, "example");
        break;
      case "play-phonetic":
        event.preventDefault();
        playPhonetic(actionElement.dataset.id);
        break;
      case "grade":
        event.preventDefault();
        applyGrade(actionElement.dataset.id || (state.plan && state.plan.ids[state.index]), actionElement.dataset.result, {
          advance: true,
        });
        break;
      case "learn-more":
        learnMore();
        break;
      case "go-library":
        switchView("library");
        break;
      case "open-word":
        event.preventDefault();
        if (state.view === "library") state.libraryAnchorId = actionElement.dataset.id;
        if (state.autoplay) stopAutoplay(false);
        openSheet(actionElement.dataset.id);
        break;
      case "close-sheet":
        closeSheet();
        break;
      case "filter-library": {
        const filter = actionElement.dataset.filter || "all";
        stopAutoplay(false);
        state.libraryAnchorId = null;
        state.libraryFilter = filter;
        $$("#filter-chips .chip").forEach((chip) => {
          chip.classList.toggle("is-active", chip.dataset.filter === filter);
        });
        renderLibraryList();
        window.scrollTo({ top: 0, behavior: "smooth" });
        break;
      }
      case "toggle-autoplay":
        toggleAutoplay();
        break;
      case "clear-search": {
        stopAutoplay(false);
        state.libraryAnchorId = null;
        state.libraryQuery = "";
        const input = $("#library-search");
        if (input) {
          input.value = "";
          input.focus();
        }
        renderLibraryList();
        break;
      }
      case "set-target":
        setTarget(Number(actionElement.dataset.value));
        break;
      case "set-speed":
        setSpeed(Number(actionElement.dataset.value));
        break;
      case "set-ui-size":
        setUiSize(actionElement.dataset.value);
        break;
      case "toggle-homophone":
        toggleHomophone();
        break;
      case "sheet-grade":
        applyGrade(actionElement.dataset.id, actionElement.dataset.result, { advance: false });
        break;
      case "reset-progress":
        showConfirm();
        break;
      case "cancel-reset":
        closeConfirm();
        break;
      case "confirm-reset":
        resetProgress();
        break;
      case "install-app":
        installApp();
        break;
      case "reload":
        window.location.reload();
        break;
      default:
        break;
    }
  }

  function onDocumentInput(event) {
    if (event.target && event.target.id === "library-search") {
      stopAutoplay(false);
      state.libraryAnchorId = null;
      state.libraryQuery = event.target.value;
      renderLibraryList();
    }
  }

  function onDocumentKeydown(event) {
    if (event.key === "Escape") {
      const confirm = $("#confirm");
      if (confirm && !confirm.hidden) {
        closeConfirm();
        return;
      }
      if (state.sheetWordId) {
        closeSheet();
        return;
      }
    }

    if (
      (event.key === "Enter" || event.key === " ") &&
      event.target &&
      event.target.matches &&
      event.target.matches('[data-action="open-word"][role="button"]')
    ) {
      event.preventDefault();
      openSheet(event.target.dataset.id);
      return;
    }

    if (event.key === "Tab" && state.sheetWordId) {
      const sheet = $("#sheet");
      if (!sheet) return;
      const focusable = $$(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        sheet,
      ).filter((element) => !element.disabled && element.offsetParent !== null);
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  }

  function init() {
    if (!WORDS.length) {
      renderToday();
      return;
    }
    applyUiSize();
    ensureTodayPlan();

    const params = new URLSearchParams(window.location.search);
    const requested = params.get("view");
    const initialView = ["today", "library", "phonetics", "me"].includes(requested) ? requested : "today";
    state.view = initialView;
    $$(".view").forEach((view) => {
      view.hidden = view.dataset.view !== initialView;
    });
    $$(".nav-btn").forEach((button) => {
      const active = button.dataset.view === initialView;
      button.classList.toggle("is-active", active);
      if (active) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    });

    if (initialView === "today") renderToday();
    if (initialView === "library") renderLibrary();
    if (initialView === "phonetics") renderPhonetics();
    if (initialView === "me") renderMe();
    renderChrome();

    document.addEventListener("click", onDocumentClick);
    document.addEventListener("input", onDocumentInput);
    document.addEventListener("keydown", onDocumentKeydown);

    let dockTicking = false;
    window.addEventListener(
      "scroll",
      () => {
        if (dockTicking) return;
        dockTicking = true;
        requestAnimationFrame(() => {
          updateGradeDock();
          dockTicking = false;
        });
      },
      { passive: true },
    );

    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) {
        const current = todayKey();
        if (current !== state.todayKey) {
          ensureTodayPlan();
          renderChrome();
          if (state.view === "today") renderToday();
          if (state.view === "me") renderMe();
        }
      }
    });

    window.addEventListener("beforeinstallprompt", (event) => {
      event.preventDefault();
      state.deferredPrompt = event;
      if (state.view === "me") renderMe();
    });

    window.addEventListener("appinstalled", () => {
      state.deferredPrompt = null;
      showToast("已安装到手机桌面");
      if (state.view === "me") renderMe();
    });

    if ("serviceWorker" in navigator && window.location.protocol !== "file:") {
      window.addEventListener("load", () => {
        navigator.serviceWorker.register("./sw.js").catch(() => {
          /* offline cache is an enhancement; the app still works */
        });
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
