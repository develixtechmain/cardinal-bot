/* ═══════════════════════════════════════════════════════════════
   Cardinal Admin SPA
   ═══════════════════════════════════════════════════════════════ */

const TOKEN_KEY = "admin_token";

function getToken() { return sessionStorage.getItem(TOKEN_KEY) || ""; }
function setToken(t) { t ? sessionStorage.setItem(TOKEN_KEY, t) : sessionStorage.removeItem(TOKEN_KEY); }

function hdrs() {
  const h = { Accept: "application/json", "Content-Type": "application/json" };
  const t = getToken();
  if (t) h["Authorization"] = "Bearer " + t;
  return h;
}

function showError(id, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.hidden = !msg;
}

async function fetchJson(url, opts = {}) {
  const r = await fetch(url, { headers: hdrs(), ...opts });
  if (r.status === 401) { setToken(""); showApp(false); showError("loginErr", "Сессия истекла, войдите снова."); throw new Error("Unauthorized"); }
  const text = await r.text();
  let body;
  try { body = text ? JSON.parse(text) : {}; } catch { body = { detail: text }; }
  if (!r.ok) {
    const d = body.detail;
    const msg = typeof d === "string" ? d : Array.isArray(d) ? d.map(x => x.msg || x).join(", ") : r.statusText;
    throw new Error(msg || "HTTP " + r.status);
  }
  return body;
}

function fmtTime(iso) { if (!iso) return ""; const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleString(); }
function fmtDate(iso) { if (!iso) return ""; const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleDateString(); }
function statusClass(s) { if (s === "error") return "status-error"; if (s === "filtered" || s === "skipped") return "status-filtered"; return "status-ok"; }
function escapeHtml(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

/* ── Auth ──────────────────────────────────────────────────── */

function showApp(loggedIn) {
  document.getElementById("loginSection").hidden = loggedIn;
  document.getElementById("appSection").hidden = !loggedIn;
  if (loggedIn) route();
}

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("loginErr", "");
  const login = document.getElementById("loginInput").value.trim();
  const password = document.getElementById("passInput").value;
  if (!login || !password) { showError("loginErr", "Введите логин и пароль."); return; }
  try {
    const data = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ login, password }) });
    const body = await data.json();
    if (!data.ok) { showError("loginErr", body.detail || "Ошибка авторизации"); return; }
    setToken(body.token);
    showApp(true);
  } catch (err) { showError("loginErr", err.message); }
});

document.getElementById("btnLogout").addEventListener("click", async () => {
  try { await fetch("/api/auth/logout", { method: "POST", headers: hdrs() }); } catch {}
  setToken("");
  showApp(false);
});

/* ── SPA Router ───────────────────────────────────────────── */

const pages = ["page-traces", "page-users", "page-user-detail"];

function hidePage(id) { const el = document.getElementById(id); if (el) el.hidden = true; }
function showPage(id) { const el = document.getElementById(id); if (el) el.hidden = false; }

function setActiveLink(routeName) {
  document.querySelectorAll(".sidebar-link").forEach(a => {
    a.classList.toggle("active", a.dataset.route === routeName);
  });
}

function route() {
  const path = location.pathname;
  pages.forEach(hidePage);
  showError("err", "");

  if (path.startsWith("/users/") && path.split("/").filter(Boolean).length >= 2) {
    const parts = path.split("/").filter(Boolean);
    const uid = parts[1];
    const sub = parts[2] || "card";
    setActiveLink("users");
    showPage("page-user-detail");
    document.getElementById("pageTitle").textContent = "Пользователь";
    document.getElementById("pageSubtitle").textContent = "";
    loadUserDetail(uid, sub);
  } else if (path.startsWith("/users")) {
    setActiveLink("users");
    showPage("page-users");
    document.getElementById("pageTitle").textContent = "Пользователи";
    document.getElementById("pageSubtitle").textContent = "Управление пользователями";
    loadUsers();
  } else {
    setActiveLink("traces");
    showPage("page-traces");
    document.getElementById("pageTitle").textContent = "Трейсинг";
    document.getElementById("pageSubtitle").textContent = "Трассировка сообщений";
  }
}

function navigate(url) {
  history.pushState(null, "", url);
  route();
}

window.addEventListener("popstate", () => { if (getToken()) route(); });

document.querySelectorAll(".sidebar-link").forEach(a => {
  a.addEventListener("click", (e) => { e.preventDefault(); navigate(a.href); });
});

/* ── Traces ───────────────────────────────────────────────── */

document.getElementById("btnSearch").addEventListener("click", runSearch);
document.getElementById("searchQ").addEventListener("keydown", (e) => { if (e.key === "Enter") runSearch(); });
document.getElementById("btnBack").addEventListener("click", () => {
  document.getElementById("detailSection").hidden = true;
  document.getElementById("listSection").hidden = false;
});

async function runSearch() {
  showError("err", "");
  const q = document.getElementById("searchQ").value.trim();
  const params = new URLSearchParams({ limit: "50", offset: "0" });
  if (q) params.set("q", q);
  try {
    const data = await fetchJson("/api/traces?" + params);
    renderTraceList(data);
    document.getElementById("listSection").hidden = false;
    document.getElementById("detailSection").hidden = true;
  } catch (e) { if (e.message !== "Unauthorized") showError("err", e.message); }
}

function renderTraceList(data) {
  const tb = document.querySelector("#resultsTable tbody");
  tb.innerHTML = "";
  for (const it of data.items || []) {
    const tr = document.createElement("tr");
    const fullText = it.source_text || "";
    const textSnippet = fullText ? fullText.slice(0, 120) + (fullText.length > 120 ? "\u2026" : "") : "\u2014";
    tr.innerHTML =
      '<td class="mono">' + escapeHtml(it.correlation_id) + "</td>" +
      "<td>" + escapeHtml(it.source_chat_id || "\u2014") + (it.source_message_id != null ? " : " + it.source_message_id : "") + "</td>" +
      "<td>" + it.event_count + "</td>" +
      "<td>" + fmtTime(it.last_event_at) + "</td>" +
      "<td>" + escapeHtml(it.last_summary || "") + "</td>" +
      '<td class="source-text has-tooltip">' + escapeHtml(textSnippet) +
        (fullText ? '<span class="tooltip-text">' + escapeHtml(fullText) + '</span>' : '') + "</td>";
    tr.addEventListener("click", () => openDetail(it.correlation_id));
    tb.appendChild(tr);
  }
}

async function openDetail(correlationId) {
  showError("err", "");
  try {
    const data = await fetchJson("/api/traces/" + correlationId);
    document.getElementById("listSection").hidden = true;
    document.getElementById("detailSection").hidden = false;
    document.getElementById("detailSummary").textContent = data.summary || "";
    const r = data.root;
    document.getElementById("detailMeta").textContent = "Корень: " + r.correlation_id + " \u00b7 чат " + (r.source_chat_id || "\u2014") + " \u00b7 msg " + (r.source_message_id ?? "\u2014");
    const textEl = document.getElementById("detailSourceText");
    if (textEl) { textEl.textContent = r.source_text || ""; textEl.hidden = !r.source_text; }
    const tl = document.getElementById("timeline");
    tl.innerHTML = "";
    let prevTs = null;
    for (const ev of data.events || []) {
      const ts = new Date(ev.occurred_at).getTime();
      const delta = prevTs != null ? "+" + (ts - prevTs) + " ms" : "";
      prevTs = ts;
      const div = document.createElement("div");
      div.className = "timeline-item " + statusClass(ev.status);
      const detailStr = ev.detail && Object.keys(ev.detail).length ? JSON.stringify(ev.detail, null, 2) : "";
      div.innerHTML =
        '<div class="ev-title">' + escapeHtml(ev.service) + " \u00b7 " + escapeHtml(ev.stage) + "</div>" +
        '<div class="ev-meta">' + escapeHtml(ev.status) + " \u00b7 " + fmtTime(ev.occurred_at) + (delta ? " \u00b7 " + delta : "") + "</div>" +
        (detailStr ? '<div class="ev-detail">' + escapeHtml(detailStr) + "</div>" : "");
      tl.appendChild(div);
    }
    document.getElementById("rawJson").textContent = JSON.stringify(data, null, 2);
  } catch (e) { if (e.message !== "Unauthorized") showError("err", e.message); }
}

/* ── Users list ───────────────────────────────────────────── */

let usersPage = 0;
const USERS_LIMIT = 50;

document.getElementById("btnUserSearch").addEventListener("click", () => { usersPage = 0; loadUsers(); });
document.getElementById("userSearchQ").addEventListener("keydown", (e) => { if (e.key === "Enter") { usersPage = 0; loadUsers(); } });

async function loadUsers() {
  showError("err", "");
  const q = document.getElementById("userSearchQ").value.trim();
  const params = new URLSearchParams({ limit: String(USERS_LIMIT), offset: String(usersPage * USERS_LIMIT) });
  if (q) params.set("q", q);
  try {
    const data = await fetchJson("/api/users?" + params);
    renderUsersList(data);
    document.getElementById("usersListSection").hidden = false;
  } catch (e) { if (e.message !== "Unauthorized") showError("err", e.message); }
}

function subscriptionBadge(endsAt, trialEndsAt) {
  const now = new Date();
  // Active subscription
  if (endsAt) {
    const d = new Date(endsAt);
    if (d > now) return '<span class="badge badge-active">\u2714 до ' + fmtDate(endsAt) + '</span>';
  }
  // Active trial (no subscription or subscription expired, but trial still running)
  if (trialEndsAt) {
    const t = new Date(trialEndsAt);
    if (t > now) return '<span class="badge badge-active">\u2714 триал до ' + fmtDate(trialEndsAt) + '</span>';
  }
  // Had subscription but it expired
  if (endsAt) return '<span class="badge badge-expired">\u2718 истекла ' + fmtDate(endsAt) + '</span>';
  // Had trial but it expired
  if (trialEndsAt) return '<span class="badge badge-expired">\u2718 триал истёк ' + fmtDate(trialEndsAt) + '</span>';
  // Never activated
  return '<span class="badge badge-none">Не активирован</span>';
}

function renderUsersList(data) {
  const tb = document.querySelector("#usersTable tbody");
  tb.innerHTML = "";
  for (const u of data.items || []) {
    const tr = document.createElement("tr");
    const name = [u.first_name, u.last_name].filter(Boolean).join(" ") || "\u2014";
    tr.innerHTML =
      "<td>" + escapeHtml(u.username || "\u2014") + "</td>" +
      "<td>" + escapeHtml(name) + "</td>" +
      "<td>" + fmtDate(u.created_at) + "</td>" +
      "<td>" + subscriptionBadge(u.subscription_ends_at, u.trial_ends_at) + "</td>" +
      "<td>" + u.leads_today + "</td>" +
      "<td>" + u.leads_month + "</td>";
    tr.addEventListener("click", () => navigate("/users/" + u.id));
    tb.appendChild(tr);
  }
  renderPagination("usersPagination", data.total, USERS_LIMIT, usersPage, (p) => { usersPage = p; loadUsers(); });
}

/* ── Pagination helper ────────────────────────────────────── */

function renderPagination(containerId, total, limit, currentPage, onChange) {
  const cont = document.getElementById(containerId);
  if (!cont) return;
  cont.innerHTML = "";
  const totalPages = Math.ceil(total / limit);
  if (totalPages <= 1) return;

  const addBtn = (label, page, disabled, active) => {
    const btn = document.createElement("button");
    btn.textContent = label;
    btn.disabled = disabled;
    if (active) btn.className = "active";
    if (!disabled && !active) btn.addEventListener("click", () => onChange(page));
    cont.appendChild(btn);
  };

  addBtn("\u2190", currentPage - 1, currentPage === 0, false);

  let start = Math.max(0, currentPage - 3);
  let end = Math.min(totalPages, start + 7);
  if (end - start < 7) start = Math.max(0, end - 7);

  for (let i = start; i < end; i++) {
    addBtn(String(i + 1), i, false, i === currentPage);
  }

  addBtn("\u2192", currentPage + 1, currentPage >= totalPages - 1, false);
}

/* ── User detail ──────────────────────────────────────────── */

let currentUserId = null;
let currentUserData = null;

document.getElementById("btnBackToUsers").addEventListener("click", () => navigate("/users/"));

// Tab switching
document.querySelectorAll("#userTabs .tab").forEach(btn => {
  btn.addEventListener("click", () => {
    const tab = btn.dataset.tab;
    navigate("/users/" + currentUserId + (tab === "card" ? "" : "/" + tab));
  });
});

function activateTab(tab) {
  document.querySelectorAll("#userTabs .tab").forEach(b => b.classList.toggle("active", b.dataset.tab === tab));
  ["card", "leads", "payments"].forEach(t => {
    const el = document.getElementById("tab-" + t);
    if (el) el.hidden = (t !== tab);
  });
}

async function loadUserDetail(uid, tab) {
  if (currentUserId !== uid) {
    leadsPage = 0;
    paymentsPage = 0;
    _taskOptionsLoadedFor = null;
  }
  currentUserId = uid;
  activateTab(tab);

  if (!currentUserData || String(currentUserData.id) !== uid) {
    try {
      currentUserData = await fetchJson("/api/users/" + uid);
      renderUserCard(currentUserData);
      document.getElementById("pageSubtitle").textContent = currentUserData.username ? "@" + currentUserData.username : "ID: " + currentUserData.user_id;
    } catch (e) {
      if (e.message !== "Unauthorized") showError("err", e.message);
      return;
    }
  }

  if (tab === "leads") loadLeads(uid);
  else if (tab === "payments") loadPayments(uid);
}

function renderUserCard(u) {
  const panel = document.getElementById("userCardPanel");
  const subBadge = subscriptionBadge(u.subscription_ends_at, u.trial_ends_at);
  const trialInfo = u.trial_ends_at ? "Триал до: " + fmtDate(u.trial_ends_at) : "";

  let html = '<div class="user-card-grid">';
  html += cardField("Баланс", u.balance + " \u20bd");
  html += cardField("Telegram ID", u.user_id);
  html += cardField("UUID", u.id);
  html += cardField("Юзернейм", u.username || "\u2014");
  html += cardField("Имя", [u.first_name, u.last_name].filter(Boolean).join(" ") || "\u2014");
  html += cardField("Регистрация", fmtDate(u.created_at));
  html += cardField("Подписка", subBadge, true);
  if (trialInfo) html += cardField("Триал", trialInfo);
  html += "</div>";

  // Subscription & trial management
  html += '<div class="panel" style="margin-top:1rem;padding:1rem 1.25rem">';
  html += '<h3 style="margin:0 0 0.75rem;font-size:1rem">Управление подпиской</h3>';
  html += '<div style="display:flex;gap:1rem;flex-wrap:wrap">';

  html += '<div style="flex:1;min-width:200px">';
  html += '<label>Продлить подписку</label>';
  html += '<div class="row" style="gap:0.5rem">';
  html += '<input type="number" id="extSubDays" min="1" max="365" placeholder="Дни" style="width:80px;flex:0 0 auto" />';
  html += '<button type="button" id="btnExtSub">Продлить</button>';
  html += '</div>';
  html += '</div>';

  html += '<div style="flex:1;min-width:200px">';
  html += '<label>Продлить / выдать триал</label>';
  html += '<div class="row" style="gap:0.5rem">';
  html += '<input type="number" id="extTrialDays" min="1" max="365" placeholder="Дни" style="width:80px;flex:0 0 auto" />';
  html += '<button type="button" id="btnExtTrial">Продлить</button>';
  html += '</div>';
  html += '</div>';

  html += '</div>';
  html += '<div id="extResult" class="muted" style="margin-top:0.5rem" hidden></div>';
  html += '</div>';

  // Tasks
  if (u.tasks && u.tasks.length) {
    html += '<div class="task-list"><h3 style="margin:0 0 0.5rem">Задачи (' + u.tasks.length + ')</h3>';
    for (const t of u.tasks) {
      const tags = Array.isArray(t.tags) ? t.tags : (typeof t.tags === "string" ? JSON.parse(t.tags) : []);
      const dotClass = t.active ? "active" : "inactive";
      html += '<div class="task-item">';
      html += '<div class="task-header" onclick="this.nextElementSibling.hidden=!this.nextElementSibling.hidden">';
      html += '<span class="task-title"><span class="task-active-dot ' + dotClass + '"></span>' + escapeHtml(t.title) + '</span>';
      html += '<span class="muted">' + fmtDate(t.created_at) + '</span>';
      html += '</div>';
      html += '<div class="task-body" hidden>';
      html += '<div><strong>Статус:</strong> ' + (t.active ? "Активна" : "Неактивна") + '</div>';
      html += '<div><strong>Создана:</strong> ' + fmtTime(t.created_at) + '</div>';
      if (tags.length) {
        html += '<div class="task-tags">';
        for (const tag of tags) html += '<span class="task-tag">' + escapeHtml(String(tag)) + '</span>';
        html += '</div>';
      }
      html += '</div></div>';
    }
    html += '</div>';
  }

  panel.innerHTML = html;

  // Bind extend subscription button
  document.getElementById("btnExtSub").addEventListener("click", async () => {
    const days = parseInt(document.getElementById("extSubDays").value, 10);
    if (!days || days <= 0) return;
    if (!confirm("Продлить подписку на " + days + " дн.?")) return;
    const resultEl = document.getElementById("extResult");
    try {
      const res = await fetchJson("/api/users/" + currentUserId + "/subscription", {
        method: "POST", body: JSON.stringify({ days }),
      });
      resultEl.textContent = "\u2714 " + res.message + (res.subscription_ends_at ? " (до " + fmtDate(res.subscription_ends_at) + ")" : "");
      resultEl.hidden = false;
      currentUserData = null;
      loadUserDetail(currentUserId, "card");
    } catch (e) { resultEl.textContent = "\u2718 Ошибка: " + e.message; resultEl.hidden = false; }
  });

  // Bind extend trial button
  document.getElementById("btnExtTrial").addEventListener("click", async () => {
    const days = parseInt(document.getElementById("extTrialDays").value, 10);
    if (!days || days <= 0) return;
    if (!confirm("Продлить триал на " + days + " дн.?")) return;
    const resultEl = document.getElementById("extResult");
    try {
      const res = await fetchJson("/api/users/" + currentUserId + "/trial", {
        method: "POST", body: JSON.stringify({ days }),
      });
      resultEl.textContent = "\u2714 " + res.message + (res.trial_ends_at ? " (до " + fmtDate(res.trial_ends_at) + ")" : "");
      resultEl.hidden = false;
      currentUserData = null;
      loadUserDetail(currentUserId, "card");
    } catch (e) { resultEl.textContent = "\u2718 Ошибка: " + e.message; resultEl.hidden = false; }
  });
}

function cardField(label, value, isHtml) {
  const safeValue = isHtml ? value : escapeHtml(String(value));
  return '<div class="card-field"><span class="card-field-label">' + escapeHtml(label) + '</span><span class="card-field-value">' + safeValue + '</span></div>';
}

/* ── Leads ────────────────────────────────────────────────── */

let leadsPage = 0;
const LEADS_LIMIT = 50;
let selectedTaskIds = [];

// Date presets
document.querySelectorAll(".preset-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".preset-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const today = new Date();
    const fmt = d => d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
    const preset = btn.dataset.preset;
    if (preset === "today") {
      document.getElementById("leadDateFrom").value = fmt(today);
      document.getElementById("leadDateTo").value = fmt(new Date(today.getTime() + 86400000));
    } else if (preset === "yesterday") {
      const y = new Date(today.getTime() - 86400000);
      document.getElementById("leadDateFrom").value = fmt(y);
      document.getElementById("leadDateTo").value = fmt(today);
    } else if (preset === "week") {
      document.getElementById("leadDateFrom").value = fmt(new Date(today.getTime() - 7 * 86400000));
      document.getElementById("leadDateTo").value = fmt(new Date(today.getTime() + 86400000));
    } else if (preset === "month") {
      document.getElementById("leadDateFrom").value = fmt(new Date(today.getFullYear(), today.getMonth(), 1));
      document.getElementById("leadDateTo").value = fmt(new Date(today.getTime() + 86400000));
    }
  });
});

// Multi-select for tasks
const taskTrigger = document.getElementById("taskSelectTrigger");
const taskDropdown = document.getElementById("taskSelectDropdown");

taskTrigger.addEventListener("click", () => { taskDropdown.hidden = !taskDropdown.hidden; });
document.addEventListener("click", (e) => {
  if (!e.target.closest("#taskMultiSelect")) taskDropdown.hidden = true;
});

async function loadTaskOptions(uid) {
  try {
    const tasks = await fetchJson("/api/users/" + uid + "/tasks");
    const cont = document.getElementById("taskSelectOptions");
    cont.innerHTML = "";
    selectedTaskIds = [];
    for (const t of tasks) {
      const div = document.createElement("div");
      div.className = "multi-select-option";
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.value = t.id;
      cb.addEventListener("change", () => {
        if (cb.checked) selectedTaskIds.push(t.id);
        else selectedTaskIds = selectedTaskIds.filter(x => x !== t.id);
        document.getElementById("taskSelectLabel").textContent = selectedTaskIds.length ? selectedTaskIds.length + " выбрано" : "Все задачи";
      });
      const span = document.createElement("span");
      span.textContent = t.title;
      div.appendChild(cb);
      div.appendChild(span);
      cont.appendChild(div);
    }
  } catch {}
}

document.getElementById("btnLeadSearch").addEventListener("click", () => { leadsPage = 0; loadLeads(currentUserId); });

let _taskOptionsLoadedFor = null;

async function loadLeads(uid) {
  if (_taskOptionsLoadedFor !== uid) {
    await loadTaskOptions(uid);
    _taskOptionsLoadedFor = uid;
  }
  showError("err", "");
  const params = new URLSearchParams({ limit: String(LEADS_LIMIT), offset: String(leadsPage * LEADS_LIMIT) });
  const df = document.getElementById("leadDateFrom").value;
  const dt = document.getElementById("leadDateTo").value;
  if (df) params.set("date_from", df);
  if (dt) params.set("date_to", dt);
  if (selectedTaskIds.length) params.set("task_ids", selectedTaskIds.join(","));

  // Sync URL
  history.replaceState(null, "", "/users/" + uid + "/leads?" + params);

  try {
    const data = await fetchJson("/api/users/" + uid + "/leads?" + params);
    renderLeads(data, uid);
    document.getElementById("leadsListSection").hidden = false;
  } catch (e) { if (e.message !== "Unauthorized") showError("err", e.message); }
}

function leadStatusIcon(accepted) {
  if (accepted === true) return '<span class="lead-status lead-accepted">\u2714</span>';
  if (accepted === false) return '<span class="lead-status lead-declined">\u2718</span>';
  return '<span class="lead-status lead-pending">\u2753</span>';
}

function getLeadText(rec) {
  if (!rec) return "";
  if (typeof rec === "string") return rec;
  return rec.text || rec.message || rec.content || JSON.stringify(rec);
}

function renderLeads(data, uid) {
  const tb = document.querySelector("#leadsTable tbody");
  tb.innerHTML = "";
  for (const lead of data.items || []) {
    const tr = document.createElement("tr");
    const fullText = getLeadText(lead.recommendation);
    const snippet = fullText.length > 80 ? fullText.slice(0, 80) + "\u2026" : fullText;
    const notes = lead.accepted === false ? "Отклонён" : (lead.accepted === true ? "Принят" : "");
    tr.innerHTML =
      "<td>" + fmtTime(lead.created_at) + "</td>" +
      '<td class="has-tooltip">' + escapeHtml(snippet) + '<span class="tooltip-text">' + escapeHtml(fullText) + '</span></td>' +
      "<td>" + leadStatusIcon(lead.accepted) + "</td>" +
      "<td class='muted'>" + escapeHtml(notes) + "</td>";
    tr.addEventListener("click", () => openLeadModal(lead));
    tb.appendChild(tr);
  }
  renderPagination("leadsPagination", data.total, LEADS_LIMIT, leadsPage, (p) => { leadsPage = p; loadLeads(uid); });
}

// Lead modal
function openLeadModal(lead) {
  const body = document.getElementById("leadModalBody");
  const fullText = getLeadText(lead.recommendation);
  let html = "";
  html += modalField("Дата", fmtTime(lead.created_at));
  html += modalField("Задача", lead.task_title || "\u2014");
  html += modalField("Статус", lead.accepted === true ? "\u2714 Принят" : (lead.accepted === false ? "\u2718 Отклонён" : "\u2753 Без ответа"));
  html += modalField("Текст лида", fullText);

  // Show all recommendation fields
  if (lead.recommendation && typeof lead.recommendation === "object") {
    for (const [k, v] of Object.entries(lead.recommendation)) {
      if (k === "text" || k === "message" || k === "content") continue;
      html += modalField(k, typeof v === "object" ? JSON.stringify(v, null, 2) : String(v));
    }
  }

  body.innerHTML = html;
  document.getElementById("leadModal").hidden = false;
}

document.getElementById("btnCloseModal").addEventListener("click", () => { document.getElementById("leadModal").hidden = true; });
document.getElementById("leadModal").addEventListener("click", (e) => { if (e.target === e.currentTarget) document.getElementById("leadModal").hidden = true; });

function modalField(label, value) {
  return '<div class="modal-field"><label>' + escapeHtml(label) + '</label><div class="modal-field-value">' + escapeHtml(String(value || "")) + '</div></div>';
}

/* ── Payments ─────────────────────────────────────────────── */

let paymentsPage = 0;
const PAYMENTS_LIMIT = 50;

document.getElementById("btnTopUp").addEventListener("click", async () => {
  const input = document.getElementById("topUpAmount");
  const amount = parseInt(input.value, 10);
  if (!amount || amount <= 0) return;
  if (!confirm("Начислить " + amount + " ₽ на баланс пользователя?")) return;
  const resultEl = document.getElementById("topUpResult");
  try {
    const res = await fetchJson("/api/users/" + currentUserId + "/balance", {
      method: "POST",
      body: JSON.stringify({ amount }),
    });
    const notifStatus = res.notification_sent ? " (уведомление отправлено)" : " (уведомление не отправлено)";
    resultEl.textContent = "\u2714 " + res.message + ". Баланс: " + res.new_balance + " \u20bd" + notifStatus;
    resultEl.hidden = false;
    input.value = "";
    // Reload user data to refresh balance
    currentUserData = null;
    loadUserDetail(currentUserId, "payments");
  } catch (e) {
    resultEl.textContent = "\u2718 Ошибка: " + e.message;
    resultEl.hidden = false;
  }
});

async function loadPayments(uid) {
  showError("err", "");
  const params = new URLSearchParams({ limit: String(PAYMENTS_LIMIT), offset: String(paymentsPage * PAYMENTS_LIMIT) });
  try {
    const data = await fetchJson("/api/users/" + uid + "/payments?" + params);
    renderPayments(data, uid);
    document.getElementById("paymentsListSection").hidden = false;
  } catch (e) { if (e.message !== "Unauthorized") showError("err", e.message); }
}

function payStatusText(status) {
  const map = { completed: "Оплачено", pending: "Ожидание", failed: "Ошибка", timeout: "Таймаут", template: "Шаблон" };
  return map[status] || status;
}

function payStatusClass(status) {
  const map = { completed: "pay-completed", pending: "pay-pending", failed: "pay-failed", timeout: "pay-timeout" };
  return map[status] || "";
}

function payMethodText(p) {
  const map = { lava: "Lava", alpha: "Alpha", robokassa: "Robokassa", balance: "Баланс" };
  return map[p] || p;
}

function renderPayments(data, uid) {
  const tb = document.querySelector("#paymentsTable tbody");
  tb.innerHTML = "";
  for (const p of data.items || []) {
    const tr = document.createElement("tr");
    tr.style.cursor = "default";
    tr.innerHTML =
      "<td>" + fmtTime(p.created_at) + "</td>" +
      "<td>" + p.amount + " \u20bd</td>" +
      '<td class="' + payStatusClass(p.status) + '">' + payStatusText(p.status) + "</td>" +
      "<td>" + payMethodText(p.payment) + "</td>" +
      "<td>" + (p.recurrent ? "Да" : "Нет") + "</td>";
    tb.appendChild(tr);
  }
  renderPagination("paymentsPagination", data.total, PAYMENTS_LIMIT, paymentsPage, (p) => { paymentsPage = p; loadPayments(uid); });
}

/* ── Init ─────────────────────────────────────────────────── */

(async function init() {
  if (!getToken()) { showApp(false); return; }
  try { await fetchJson("/api/auth/me"); showApp(true); }
  catch { showApp(false); }
})();
