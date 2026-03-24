const API_BASE = "/api";

function getToken() {
  return localStorage.getItem("token");
}

function setToken(t) {
  localStorage.setItem("token", t);
}

function removeToken() {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
}

function authHeaders() {
  const t = getToken();
  const h = { "Content-Type": "application/json" };
  if (t) h.Authorization = `Bearer ${t}`;
  return h;
}

function checkAuth() {
  if (!getToken()) {
    window.location.href = "/index.html";
  }
}

async function login(username, password) {
  const r = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, data };
}

async function deployContainer(image, containerPort, name) {
  const body = { image, container_port: containerPort };
  if (name) body.name = name;
  const r = await fetch(`${API_BASE}/deploy`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, data };
}

async function listContainers() {
  const r = await fetch(`${API_BASE}/containers`, { headers: authHeaders() });
  const data = await r.json().catch(() => []);
  return { ok: r.ok, status: r.status, data };
}

async function stopContainer(id) {
  const r = await fetch(`${API_BASE}/stop`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ container_id: id }),
  });
  const data = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, data };
}

async function restartContainer(id) {
  const r = await fetch(`${API_BASE}/restart`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ container_id: id }),
  });
  const data = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, data };
}

async function removeContainer(id) {
  const r = await fetch(`${API_BASE}/remove`, {
    method: "DELETE",
    headers: authHeaders(),
    body: JSON.stringify({ container_id: id }),
  });
  const data = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, data };
}

async function getStats() {
  const r = await fetch(`${API_BASE}/stats`, { headers: { Accept: "application/json" } });
  const data = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, data };
}

function statusBadge(status) {
  const s = (status || "").toLowerCase();
  const cls = s === "running" ? "badge-running" : "badge-stopped";
  return `<span class="badge ${cls}">${escapeHtml(status || "unknown")}</span>`;
}

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function showToast(message, type = "info") {
  const root = document.getElementById("toast-root");
  if (!root) return;
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  root.appendChild(el);
  setTimeout(() => {
    el.remove();
  }, 3000);
}

function renderStats(data) {
  const row = document.getElementById("stats-row");
  if (!row || !data) return;
  const cpu = Number(data.cpu_percent || 0);
  row.innerHTML = `
    <div class="card stat-card">
      <div class="stat-label">📦 Total Deployments</div>
      <div class="stat-value">${escapeHtml(String(data.total_deployments ?? 0))}</div>
    </div>
    <div class="card stat-card">
      <div class="stat-label">✅ Running</div>
      <div class="stat-value running">${escapeHtml(String(data.running ?? 0))}</div>
    </div>
    <div class="card stat-card">
      <div class="stat-label">🔴 Stopped</div>
      <div class="stat-value stopped">${escapeHtml(String(data.stopped ?? 0))}</div>
    </div>
    <div class="card stat-card">
      <div class="stat-label">💻 CPU %</div>
      <div class="stat-value">${escapeHtml(cpu.toFixed(1))}</div>
      <div class="mini-bar"><span style="width:${Math.min(100, Math.max(0, cpu))}%"></span></div>
    </div>
  `;
}

function renderMetrics(data) {
  const el = document.getElementById("metrics-bars");
  if (!el || !data) return;
  const cpu = Number(data.cpu_percent || 0);
  const mem = Number(data.memory_percent || 0);
  const disk = Number(data.disk_percent || 0);
  const bar = (label, v) => `
    <div class="metric-row">
      <div class="metric-top"><span>${label}</span><span>${v.toFixed(0)}%</span></div>
      <div class="progress"><span style="width:${Math.min(100, Math.max(0, v))}%"></span></div>
    </div>
  `;
  el.innerHTML = bar("CPU", cpu) + bar("Memory", mem) + bar("Disk", disk);
}

function renderContainers(list, stateEl, errorMsg) {
  if (!stateEl) return;
  if (errorMsg) {
    stateEl.innerHTML = `<p class="form-error">${escapeHtml(errorMsg)}</p>`;
    return;
  }
  if (!Array.isArray(list)) {
    stateEl.innerHTML = `<p class="form-error">Unexpected response</p>`;
    return;
  }
  if (list.length === 0) {
    stateEl.innerHTML = `<p class="muted">No containers deployed yet</p>`;
    return;
  }
  const rows = list
    .map(
      (c, i) => `
      <tr>
        <td>${i + 1}</td>
        <td>${escapeHtml(c.name || c.image || "")}<div class="muted" style="font-size:0.8rem">${escapeHtml(
        c.image || ""
      )}</div></td>
        <td>${escapeHtml(String(c.host_port ?? ""))}</td>
        <td>${statusBadge(c.status)}</td>
        <td>${escapeHtml(formatDate(c.created_at))}</td>
        <td class="actions">
          <button type="button" class="btn btn-secondary btn-open" data-url="${escapeHtml(c.url || "")}">Open</button>
          <button type="button" class="btn btn-secondary btn-stop" data-id="${escapeHtml(c.container_id)}">Stop</button>
          <button type="button" class="btn btn-secondary btn-restart" data-id="${escapeHtml(
            c.container_id
          )}">Restart</button>
          <button type="button" class="btn btn-secondary btn-remove" data-id="${escapeHtml(
            c.container_id
          )}">Remove</button>
        </td>
      </tr>
    `
    )
    .join("");
  stateEl.innerHTML = `
    <table>
      <thead>
        <tr><th>#</th><th>Name / Image</th><th>Port</th><th>Status</th><th>Created</th><th>Actions</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;

  stateEl.querySelectorAll(".btn-open").forEach((btn) => {
    btn.addEventListener("click", () => {
      const u = btn.getAttribute("data-url");
      if (u) window.open(u, "_blank", "noopener");
    });
  });
  stateEl.querySelectorAll(".btn-stop").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-id");
      const res = await stopContainer(id);
      if (res.ok) showToast("Stopped", "success");
      else showToast(res.data.detail || "Stop failed", "error");
      refreshDashboardData();
    });
  });
  stateEl.querySelectorAll(".btn-restart").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-id");
      const res = await restartContainer(id);
      if (res.ok) showToast("Restarted", "success");
      else showToast(res.data.detail || "Restart failed", "error");
      refreshDashboardData();
    });
  });
  stateEl.querySelectorAll(".btn-remove").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-id");
      if (!confirm("Remove this container from the system?")) return;
      const res = await removeContainer(id);
      if (res.ok) showToast("Removed", "success");
      else showToast(res.data.detail || "Remove failed", "error");
      refreshDashboardData();
    });
  });
}

async function refreshDashboardData() {
  const stateEl = document.getElementById("containers-state");
  const [statsRes, listRes] = await Promise.all([getStats(), listContainers()]);
  if (statsRes.ok) {
    renderStats(statsRes.data);
    renderMetrics(statsRes.data);
  }
  if (listRes.ok) {
    renderContainers(listRes.data, stateEl, null);
  } else if (listRes.status === 401) {
    removeToken();
    window.location.href = "/index.html";
  } else {
    const msg =
      (listRes.data && listRes.data.detail) || `Error loading containers (${listRes.status})`;
    renderContainers([], stateEl, typeof msg === "string" ? msg : JSON.stringify(msg));
  }
}

function initLoginPage() {
  const form = document.getElementById("login-form");
  const err = document.getElementById("login-error");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    err.classList.add("hidden");
    const fd = new FormData(form);
    const username = String(fd.get("username") || "").trim();
    const password = String(fd.get("password") || "");
    const res = await login(username, password);
    if (res.ok && res.data.access_token) {
      setToken(res.data.access_token);
      localStorage.setItem("username", res.data.username || username);
      window.location.href = "/dashboard.html";
    } else {
      err.textContent =
        (res.data && res.data.detail) || "Login failed. Check your username and password.";
      err.classList.remove("hidden");
    }
  });
}

function initDashboardPage() {
  checkAuth();
  const user = localStorage.getItem("username") || "user";
  const w = document.getElementById("welcome-user");
  if (w) w.textContent = `Welcome, ${user}`;

  document.getElementById("btn-logout")?.addEventListener("click", () => {
    removeToken();
    window.location.href = "/index.html";
  });

  document.getElementById("btn-refresh")?.addEventListener("click", () => {
    refreshDashboardData();
  });

  const deployForm = document.getElementById("deploy-form");
  const deployBtn = document.getElementById("btn-deploy");
  const deployResult = document.getElementById("deploy-result");
  deployForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!deployResult) return;
    deployResult.classList.add("hidden");
    const fd = new FormData(deployForm);
    const image = String(fd.get("image") || "").trim();
    const port = parseInt(String(fd.get("container_port") || "80"), 10) || 80;
    const name = String(fd.get("name") || "").trim();
    deployBtn.classList.add("loading");
    deployBtn.disabled = true;
    const res = await deployContainer(image, port, name);
    deployBtn.classList.remove("loading");
    deployBtn.disabled = false;
    deployResult.classList.remove("hidden", "ok", "err");
    if (res.ok) {
      deployResult.classList.add("ok");
      deployResult.textContent = `Deployed: ${res.data.url || ""} (status: ${res.data.status || ""})`;
      showToast("Deployment successful", "success");
      deployForm.reset();
    } else {
      deployResult.classList.add("err");
      const d = res.data && res.data.detail;
      deployResult.textContent =
        typeof d === "string" ? d : d && d.message ? `${d.message}: ${d.logs || ""}` : "Deploy failed";
      showToast("Deployment failed", "error");
    }
    refreshDashboardData();
  });

  refreshDashboardData();
  setInterval(refreshDashboardData, 10000);
}

document.addEventListener("DOMContentLoaded", () => {
  const path = window.location.pathname || "";
  if (path.endsWith("index.html") || path === "/" || path === "") {
    initLoginPage();
  } else if (path.endsWith("dashboard.html")) {
    initDashboardPage();
  }
});
