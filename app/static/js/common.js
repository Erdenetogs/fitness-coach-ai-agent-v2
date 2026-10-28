// Бүх хуудсанд хэрэглэгдэх туслах функцууд

/** Орчуулга: t("js.wo_n", { n: 2, all: 4 }). Текстүүд app/i18n.py-д ("js." -ээр эхэлсэн түлхүүр). */
function t(key, vars = {}) {
  let s = (window.T && window.T[key]) || key;
  for (const [k, v] of Object.entries(vars)) s = s.split(`{${k}}`).join(String(v));
  return s;
}

/** JSON илгээж, JSON хүлээн авах. Алдаа гарвал Error шиднэ. */
async function api(url, options = {}) {
  const opts = { method: "POST", ...options };
  if (opts.json !== undefined) {
    opts.headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
    opts.body = JSON.stringify(opts.json);
    delete opts.json;
  }
  const res = await fetch(url, opts);
  let data = {};
  try { data = await res.json(); } catch (_) {}
  if (!res.ok) throw new Error(data.error || (typeof data.detail === "string" && data.detail) || t("js.net", { status: res.status }));
  return data;
}

let toastTimer;
function toast(text) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = text;
  el.style.opacity = "1";
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.style.opacity = "0"), 2400);
}

/** Агентын алхмуудыг HTML болгох (чат, хоол хуудас хоёулаа ашиглана) */
function renderSteps(steps) {
  if (!steps || !steps.length) return "";
  return `<div class="space-y-1 mb-2">${steps
    .map((s) => `<div class="step"><span class="msr">${escapeHtml(s.icon)}</span>${escapeHtml(s.text)}</div>`)
    .join("")}</div>`;
}

function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/** Серверээс ирсэн XP мэдээллийг toast-оор харуулах. xp = null бол юу ч хийхгүй. */
function showXp(xp) {
  if (!xp) return;
  toast(xp.leveled_up
    ? t("js.levelup", { level: xp.level, stage: xp.stage })
    : t("js.xp", { gained: xp.gained, reason: xp.reason }));
}
