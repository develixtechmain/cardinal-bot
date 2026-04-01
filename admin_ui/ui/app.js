const TOKEN_KEY = "admin_token";

function getToken() {
  return sessionStorage.getItem(TOKEN_KEY) || "";
}

function setToken(t) {
  if (t) sessionStorage.setItem(TOKEN_KEY, t);
  else sessionStorage.removeItem(TOKEN_KEY);
}

function headers() {
  const h = { Accept: "application/json", "Content-Type": "application/json" };
  const t = getToken();
  if (t) h["Authorization"] = "Bearer " + t;
  return h;
}

function showError(id, msg) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.hidden = !msg;
}

async function fetchJson(url, opts = {}) {
  const r = await fetch(url, { headers: headers(), ...opts });
  if (r.status === 401) {
    setToken("");
    showApp(false);
    showError("loginErr", "Сессия истекла, войдите снова.");
    throw new Error("Unauthorized");
  }
  const text = await r.text();
  let body;
  try {
    body = text ? JSON.parse(text) : {};
  } catch {
    body = { detail: text };
  }
  if (!r.ok) {
    const d = body.detail;
    const msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((x) => x.msg || x).join(", ") : r.statusText;
    throw new Error(msg || "HTTP " + r.status);
  }
  return body;
}

function fmtTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d) ? iso : d.toLocaleString();
}

function statusClass(status) {
  if (status === "error") return "status-error";
  if (status === "filtered" || status === "skipped") return "status-filtered";
  return "status-ok";
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

// ── Auth ────────────────────────────────────────────────────────────────────

function showApp(loggedIn) {
  document.getElementById("loginSection").hidden = loggedIn;
  document.getElementById("appSection").hidden = !loggedIn;
}

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("loginErr", "");
  const login = document.getElementById("loginInput").value.trim();
  const password = document.getElementById("passInput").value;
  if (!login || !password) {
    showError("loginErr", "Введите логин и пароль.");
    return;
  }
  try {
    const data = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ login, password }),
    });
    const body = await data.json();
    if (!data.ok) {
      showError("loginErr", body.detail || "Ошибка авторизации");
      return;
    }
    setToken(body.token);
    showApp(true);
  } catch (err) {
    showError("loginErr", err.message);
  }
});

document.getElementById("btnLogout").addEventListener("click", async () => {
  try {
    await fetch("/api/auth/logout", { method: "POST", headers: headers() });
  } catch {}
  setToken("");
  showApp(false);
});

// ── Search ──────────────────────────────────────────────────────────────────

document.getElementById("btnSearch").addEventListener("click", runSearch);
document.getElementById("searchQ").addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSearch();
});
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
    renderList(data);
    document.getElementById("listSection").hidden = false;
    document.getElementById("detailSection").hidden = true;
  } catch (e) {
    if (e.message !== "Unauthorized") showError("err", e.message);
  }
}

function renderList(data) {
  const tb = document.querySelector("#resultsTable tbody");
  tb.innerHTML = "";
  for (const it of data.items || []) {
    const tr = document.createElement("tr");
    const textSnippet = it.source_text ? it.source_text.slice(0, 120) + (it.source_text.length > 120 ? "\u2026" : "") : "\u2014";
    tr.innerHTML =
      '<td class="mono">' + escapeHtml(it.correlation_id) + "</td>" +
      "<td>" + escapeHtml(it.source_chat_id || "\u2014") + (it.source_message_id != null ? " : " + it.source_message_id : "") + "</td>" +
      "<td>" + it.event_count + "</td>" +
      "<td>" + fmtTime(it.last_event_at) + "</td>" +
      "<td>" + escapeHtml(it.last_summary || "") + "</td>" +
      '<td class="source-text">' + escapeHtml(textSnippet) + "</td>";
    tr.addEventListener("click", () => openDetail(it.correlation_id));
    tb.appendChild(tr);
  }
}

// ── Detail ──────────────────────────────────────────────────────────────────

async function openDetail(correlationId) {
  showError("err", "");
  try {
    const data = await fetchJson("/api/traces/" + correlationId);
    document.getElementById("listSection").hidden = true;
    document.getElementById("detailSection").hidden = false;
    document.getElementById("detailSummary").textContent = data.summary || "";
    const r = data.root;
    document.getElementById("detailMeta").textContent =
      "Корень: " + r.correlation_id + " \u00b7 чат " + (r.source_chat_id || "\u2014") + " \u00b7 msg " + (r.source_message_id ?? "\u2014");
    const textEl = document.getElementById("detailSourceText");
    if (textEl) {
      textEl.textContent = r.source_text || "";
      textEl.hidden = !r.source_text;
    }
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
  } catch (e) {
    if (e.message !== "Unauthorized") showError("err", e.message);
  }
}

// ── Init ────────────────────────────────────────────────────────────────────

(async function init() {
  if (!getToken()) {
    showApp(false);
    return;
  }
  try {
    await fetchJson("/api/auth/me");
    showApp(true);
  } catch {
    showApp(false);
  }
})();
