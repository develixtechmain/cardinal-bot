const KEY_STORAGE = "trace_ui_api_key";

function apiKey() {
  return sessionStorage.getItem(KEY_STORAGE) || "";
}

function headers() {
  const k = apiKey();
  const h = { Accept: "application/json" };
  if (k) h["X-Trace-API-Key"] = k;
  return h;
}

function showError(msg) {
  const el = document.getElementById("err");
  el.textContent = msg;
  el.hidden = !msg;
}

async function fetchJson(url) {
  const r = await fetch(url, { headers: headers() });
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
    throw new Error(msg || `HTTP ${r.status}`);
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

document.getElementById("saveKey").addEventListener("click", () => {
  const v = document.getElementById("apiKey").value.trim();
  if (v) sessionStorage.setItem(KEY_STORAGE, v);
  else sessionStorage.removeItem(KEY_STORAGE);
  document.getElementById("keyStatus").textContent = v ? "Ключ сохранён в sessionStorage." : "Ключ очищен.";
});

document.getElementById("btnSearch").addEventListener("click", runSearch);

document.getElementById("searchQ").addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSearch();
});

document.getElementById("btnBack").addEventListener("click", () => {
  document.getElementById("detailSection").hidden = true;
  document.getElementById("listSection").hidden = false;
});

(function init() {
  const saved = apiKey();
  if (saved) document.getElementById("apiKey").value = saved;
})();

async function runSearch() {
  showError("");
  if (!apiKey()) {
    showError("Сохраните X-Trace-API-Key.");
    return;
  }
  const q = document.getElementById("searchQ").value.trim();
  const params = new URLSearchParams({ limit: "50", offset: "0" });
  if (q) params.set("q", q);
  try {
    const data = await fetchJson(`/internal/traces?${params}`);
    renderList(data);
    document.getElementById("listSection").hidden = false;
    document.getElementById("detailSection").hidden = true;
  } catch (e) {
    showError(e.message);
  }
}

function renderList(data) {
  const tb = document.querySelector("#resultsTable tbody");
  tb.innerHTML = "";
  for (const it of data.items || []) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="mono">${it.correlation_id}</td>
      <td>${it.source_chat_id || "—"}${it.source_message_id != null ? ` : ${it.source_message_id}` : ""}</td>
      <td>${it.event_count}</td>
      <td>${fmtTime(it.last_event_at)}</td>
      <td>${escapeHtml(it.last_summary || "")}</td>
    `;
    tr.addEventListener("click", () => openDetail(it.correlation_id));
    tb.appendChild(tr);
  }
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

async function openDetail(correlationId) {
  showError("");
  if (!apiKey()) {
    showError("Сохраните X-Trace-API-Key.");
    return;
  }
  try {
    const data = await fetchJson(`/internal/traces/${correlationId}`);
    document.getElementById("listSection").hidden = true;
    document.getElementById("detailSection").hidden = false;
    document.getElementById("detailSummary").textContent = data.summary || "";
    const r = data.root;
    document.getElementById("detailMeta").textContent = `Корень: ${r.correlation_id} · чат ${r.source_chat_id || "—"} · msg ${r.source_message_id ?? "—"}`;
    const tl = document.getElementById("timeline");
    tl.innerHTML = "";
    let prevTs = null;
    for (const ev of data.events || []) {
      const ts = new Date(ev.occurred_at).getTime();
      const delta = prevTs != null ? `+${ts - prevTs} ms` : "";
      prevTs = ts;
      const div = document.createElement("div");
      div.className = `timeline-item ${statusClass(ev.status)}`;
      const detailStr = ev.detail && Object.keys(ev.detail).length ? JSON.stringify(ev.detail, null, 2) : "";
      div.innerHTML = `
        <div class="ev-title">${escapeHtml(ev.service)} · ${escapeHtml(ev.stage)}</div>
        <div class="ev-meta">${escapeHtml(ev.status)} · ${fmtTime(ev.occurred_at)} ${delta ? " · " + delta : ""}</div>
        ${detailStr ? `<div class="ev-detail">${escapeHtml(detailStr)}</div>` : ""}
      `;
      tl.appendChild(div);
    }
    document.getElementById("rawJson").textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    showError(e.message);
  }
}
