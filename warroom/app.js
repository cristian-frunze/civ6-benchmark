// Civ 6 war room page. Polls state.json (written by tools/warroom/collect.py)
// every 2 s and renders the header, the god-view map, the standings and one
// pane per agent. No build step, no dependencies.
"use strict";
(() => {
  const POLL_MS = 2000;
  const SQ3 = Math.sqrt(3);
  const $ = (id) => document.getElementById(id);
  const app = $("app");

  let S = null; // last good state.json
  let fetchError = null;
  let polling = false;

  // ── helpers ────────────────────────────────────────────────
  const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ESC[c]);
  const nowS = () => (S && S.demo ? S.generated_at : Date.now() / 1000);
  const isNum = (v) => typeof v === "number" && isFinite(v);

  function ago(ts) {
    if (!isNum(ts)) return "";
    const d = Math.max(0, nowS() - ts);
    if (d < 60) return `${Math.floor(d)}s`;
    if (d < 3600) return `${Math.floor(d / 60)}m`;
    if (d < 86400) return `${Math.floor(d / 3600)}h`;
    return `${Math.floor(d / 86400)}d`;
  }
  function dur(s) {
    s = Math.max(0, Math.floor(s));
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = s % 60;
    if (h >= 48) return `${Math.floor(h / 24)}d ${h % 24}h`;
    return `${h}:${String(m).padStart(2, "0")}:${String(x).padStart(2, "0")}`;
  }
  function tok(n) {
    if (!isNum(n)) return "-";
    if (n >= 1e9) return (n / 1e9).toFixed(2) + "B";
    if (n >= 1e6) return (n / 1e6).toFixed(n >= 1e8 ? 0 : 1) + "M";
    if (n >= 1e3) return Math.round(n / 1e3) + "K";
    return String(n);
  }
  function usd(v) {
    if (!isNum(v)) return null;
    if (v >= 1000) return "$" + Math.round(v).toLocaleString("en-US");
    return "$" + (v >= 100 ? v.toFixed(0) : v.toFixed(2));
  }
  function num(v, signed) {
    if (!isNum(v)) return "-";
    const r = Math.abs(v) >= 100 || Number.isInteger(v) ? Math.round(v) : Math.round(v * 10) / 10;
    return (signed && r > 0 ? "+" : "") + r;
  }
  function setText(el, t) { t = String(t ?? ""); if (el.textContent !== t) el.textContent = t; }
  function setHTML(el, h) { if (el._h !== h) { el._h = h; el.innerHTML = h; } }
  function mix(color, pct) { return `color-mix(in srgb, ${color} ${pct}%, transparent)`; }
  function model(id) { // claude-opus-5-5 -> Opus 5.5
    const m = /^claude-([a-z]+)-(\d+)-(\d+)/.exec(id || "");
    return m ? `${m[1][0].toUpperCase()}${m[1].slice(1)} ${m[2]}.${m[3]}` : id || "model unknown";
  }

  function spark(turns, vals, color, w, h) {
    const pts = [];
    for (let i = 0; i < vals.length; i++) if (isNum(vals[i]) && isNum(turns[i])) pts.push([turns[i], vals[i]]);
    if (pts.length < 2) return `<svg width="${w}" height="${h}" aria-hidden="true"></svg>`;
    const t0 = pts[0][0], t1 = pts[pts.length - 1][0] || t0 + 1;
    let lo = Infinity, hi = -Infinity;
    for (const [, v] of pts) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
    const sx = (t) => 1 + ((t - t0) / (t1 - t0 || 1)) * (w - 4);
    const sy = (v) => h - 2 - ((v - lo) / (hi - lo || 1)) * (h - 4);
    const line = pts.map(([t, v]) => `${sx(t).toFixed(1)},${sy(v).toFixed(1)}`).join(" ");
    const [lt, lv] = pts[pts.length - 1];
    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true">` +
      `<polygon points="${sx(t0).toFixed(1)},${h} ${line} ${sx(lt).toFixed(1)},${h}" fill="${color}" fill-opacity=".13"/>` +
      `<polyline points="${line}" fill="none" stroke="${color}" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round"/>` +
      `<circle cx="${sx(lt).toFixed(1)}" cy="${sy(lv).toFixed(1)}" r="2.1" fill="${color}"/></svg>`;
  }

  // ── polling ────────────────────────────────────────────────
  async function poll() {
    if (polling) return;
    polling = true;
    try {
      const r = await fetch(`state.json?t=${Date.now()}`, { cache: "no-store" });
      if (!r.ok) throw new Error(r.status === 404 ? "no state.json yet" : `HTTP ${r.status}`);
      const next = await r.json();
      if (!next || typeof next !== "object") throw new Error("bad state.json");
      S = next;
      fetchError = null;
    } catch (e) {
      fetchError = e && e.message ? e.message : String(e);
    } finally {
      polling = false;
    }
    render();
  }

  // ── header ─────────────────────────────────────────────────
  function renderHeader() {
    const g = (S && S.game) || {};
    setText($("title"), S ? g.title || "Civ 6 war room" : "Waiting for data");
    document.title = S ? `T${g.turn ?? "-"} · ${g.title || "Civ 6 war room"}` : "Civ 6 war room";
    setText($("turn"), g.turn ?? "-");
    const end = isNum(g.ended_at) ? g.ended_at : nowS();
    setText($("elapsed"), isNum(g.started_at) ? dur(end - g.started_at) : "-");
    const c = (S && S.cost) || {};
    const money = S && S.priced ? usd(c.usd) : null;
    setText($("cost"), money ?? (isNum(c.total) ? tok(c.total) : "-"));
    let sub = isNum(c.total) ? `${tok(c.total)} tokens` : "";
    if (S && !S.priced) sub = "tokens, no prices.json";
    else if (c.unpriced_tokens > 0) sub += ` + ${tok(c.unpriced_tokens)} unpriced`;
    setText($("tokens"), sub);
    $("cost").parentElement.title = isNum(c.total)
      ? `input ${tok(c.input)} · output ${tok(c.output)} · cache read ${tok(c.cache_read)} · cache write ${tok((c.cache_write_5m || 0) + (c.cache_write_1h || 0))} · ${c.requests ?? 0} API calls`
      : "";
    $("demo").hidden = !(S && S.demo);

    const live = $("live");
    let cls = "", text = "connecting";
    if (S) {
      const age = Date.now() / 1000 - S.generated_at;
      if (fetchError) { cls = "dead"; text = "connection lost"; }
      else if (S.demo) { cls = "lag"; text = "snapshot " + new Date(S.generated_at * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); }
      else if (age < 12) { cls = "ok"; text = "live"; }
      else if (age < 90) { cls = "lag"; text = `updated ${Math.floor(age)}s ago`; }
      else { cls = "dead"; text = `stale ${ago(S.generated_at)}`; }
    } else if (fetchError) { cls = "dead"; text = fetchError; }
    if (live.className !== `live ${cls}`) live.className = `live ${cls}`;
    setText($("live-text"), text);

    const src = (S && S.source) || {};
    let warn = "";
    if (S && src.ok === false) warn = src.error || "game PC unreachable";
    else if (S && src.folder === false) warn = "no civ6-mcp folder on the game PC yet";
    else if (S && src.files === 0) warn = "no game files yet";
    else if (S && src.note) warn = src.note;
    $("warn").hidden = !warn;
    setText($("warn"), warn);
    const phase = g.mcp_phase && !warn && !((S.civs || []).length || S.map) ? `MCP ${g.mcp_phase}, waiting for the first turn` : "";
    $("phase").hidden = !phase;
    setText($("phase"), phase);

    const go = g.game_over;
    $("gameover").hidden = !go;
    if (go) {
      const who = go.winner_civ ? `${go.winner_civ}${go.winner_leader ? ` (${go.winner_leader})` : ""} wins` : "Game over";
      const how = go.victory_type ? ` · ${go.victory_type} victory` : "";
      const agent = isNum(go.winner_agent) && S.agents[go.winner_agent] ? ` · ${S.agents[go.winner_agent].name}` : "";
      setText($("gameover"), `Game over · ${who}${how}${agent} · turn ${go.turn ?? "-"}`);
    }
  }

  // ── layout ─────────────────────────────────────────────────
  function applyLayout() {
    const n = S ? (S.agents || []).length : 0;
    const L = n <= 2 ? "side" : "top";
    const ds = app.dataset;
    if (ds.layout !== L) ds.layout = L;
    if (ds.n !== String(n)) ds.n = String(n);
    const rows = n > 4 ? "2" : "1";
    if (ds.rows !== rows) ds.rows = rows;
    app.style.setProperty("--n", String(Math.max(1, n)));
    app.style.setProperty("--cols", String(n > 4 ? Math.ceil(n / 2) : Math.max(1, n)));
    // top layout: size the map column to the map's aspect ratio
    let want = "";
    if (L === "top" && S && S.map && innerWidth > 760) {
      const h = $("map-panel").clientHeight;
      const aspect = (SQ3 * (S.map.w + 0.5)) / (1.5 * (S.map.h - 1) + 2);
      want = Math.round(Math.min(h * aspect + 18, app.clientWidth * 0.62)) + "px";
    }
    if (app.style.getPropertyValue("--map-w") !== want) {
      if (want) app.style.setProperty("--map-w", want);
      else app.style.removeProperty("--map-w");
    }
  }

  // ── map ────────────────────────────────────────────────────
  // Civ 6 base-game terrain indexes: flat, hills, mountain per base type; 15 coast, 16 ocean.
  const TERRAIN = [
    "#34502f", "#3f5d37", "#8f918b", // grassland
    "#5f5a36", "#6c6740", "#8f918b", // plains
    "#8b7748", "#99834f", "#8f918b", // desert
    "#4a5751", "#56635c", "#8f918b", // tundra
    "#a3adb3", "#b4bcc1", "#c6cdd1", // snow
    "#12283b", "#0a1826",            // coast, ocean
  ];
  // feature byte = feature index + 1 (0 = none). 1 floodplains, 2 ice, 3 jungle, 4 forest, 5 oasis, 6 marsh, 7+ natural wonders
  const FEATURE = { 1: ["#9a9a5c", 0.3], 2: ["#a9c3d2", 0.24], 3: ["#173f27", 0.55], 4: ["#1f3a24", 0.5], 5: ["#2f9a94", 0.6], 6: ["#3b6158", 0.5] };
  const map = { key: null, cities: [], s: 0 };
  const canvas = $("map");

  function decode(b64) {
    const s = atob(b64 || "");
    const a = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
    return a;
  }
  function hexPath(p, cx, cy, r) {
    const hw = (SQ3 / 2) * r;
    p.moveTo(cx, cy - r); p.lineTo(cx + hw, cy - r / 2); p.lineTo(cx + hw, cy + r / 2);
    p.lineTo(cx, cy + r); p.lineTo(cx - hw, cy + r / 2); p.lineTo(cx - hw, cy - r / 2); p.closePath();
  }
  function hexVert(cx, cy, r, i) {
    const hw = (SQ3 / 2) * r;
    return [[cx, cy - r], [cx + hw, cy - r / 2], [cx + hw, cy + r / 2], [cx, cy + r], [cx - hw, cy + r / 2], [cx - hw, cy - r / 2]][i];
  }

  function owners() {
    const color = {}, agentPids = new Set(), name = {};
    for (const c of (S && S.civs) || []) { color[c.pid] = c.color; name[c.pid] = c.civ; if (isNum(c.agent)) agentPids.add(c.pid); }
    for (const c of (S && S.map && S.map.city_states) || []) { color[c.pid] = c.color; name[c.pid] = c.name; }
    return { color, agentPids, name };
  }

  function renderMap(force) {
    const m = S && S.map;
    $("map-empty").hidden = !!m;
    const box = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const own = owners();
    const key = m ? [m.rev, box.width, box.height, dpr, JSON.stringify(own.color), [...own.agentPids].join()].join("|") : "none";
    if (key === map.key && !force) return;
    map.key = key;
    canvas.width = Math.max(1, Math.round(box.width * dpr));
    canvas.height = Math.max(1, Math.round(box.height * dpr));
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, box.width, box.height);
    map.cities = [];
    if (!m || !m.w || !m.h) return;

    const W = m.w, H = m.h, N = W * H;
    const terr = decode(m.terrain), feat = decode(m.features), ownr = decode(m.owners);
    if (terr.length < N || ownr.length < N) return;

    // put the east-west wrap seam where it cuts the least territory and land
    let seam = 0, best = Infinity;
    for (let x = 0; x < W; x++) {
      let cost = 0;
      for (let y = 0; y < H; y++) cost += (ownr[y * W + x] ? 3 : 0) + (terr[y * W + x] < 15 ? 1 : 0);
      if (cost < best) { best = cost; seam = x; }
    }
    if (!m.wrap_x) seam = 0;

    const pad = 6;
    const s = Math.min((box.width - pad * 2) / (SQ3 * (W + 0.5)), (box.height - pad * 2) / (1.5 * (H - 1) + 2));
    map.s = s;
    const ox = (box.width - SQ3 * s * (W + 0.5)) / 2, oy = (box.height - (1.5 * (H - 1) + 2) * s) / 2;
    const cx = new Float32Array(N), cy = new Float32Array(N);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = y * W + x, col = (x - seam + W) % W, row = H - 1 - y;
      cx[i] = ox + SQ3 * s * (col + 0.5 * (y & 1)) + (SQ3 * s) / 2;
      cy[i] = oy + 1.5 * s * row + s;
    }

    // terrain, grouped by color
    const groups = new Map();
    for (let i = 0; i < N; i++) {
      const c = TERRAIN[terr[i]] || "#2a2d31";
      if (!groups.has(c)) groups.set(c, new Path2D());
      hexPath(groups.get(c), cx[i], cy[i], s + 0.35);
    }
    for (const [c, p] of groups) { ctx.fillStyle = c; ctx.fill(p); }
    const fgroups = new Map(), wonders = [];
    for (let i = 0; i < N; i++) {
      const f = feat[i];
      if (!f) continue;
      if (f >= 7) { wonders.push(i); continue; }
      if (!FEATURE[f]) continue;
      if (!fgroups.has(f)) fgroups.set(f, new Path2D());
      hexPath(fgroups.get(f), cx[i], cy[i], f === 2 ? s + 0.35 : s * 0.62);
    }
    for (const [f, p] of fgroups) { ctx.globalAlpha = FEATURE[f][1]; ctx.fillStyle = FEATURE[f][0]; ctx.fill(p); }
    ctx.globalAlpha = 1;

    // territory fill and inset borders, one path per owner
    const fills = new Map(), edges = new Map();
    const nb = (x, y, d) => { // screen directions: E, W, UR, UL, LR, LL (up = north = y + 1)
      const odd = y & 1;
      const D = [[1, 0], [-1, 0], [odd, 1], [odd - 1, 1], [odd, -1], [odd - 1, -1]][d];
      const ny = y + D[1];
      if (ny < 0 || ny >= H) return -1;
      return ny * W + ((x + D[0] + W) % W);
    };
    const EDGE = [[1, 2], [4, 5], [0, 1], [5, 0], [2, 3], [3, 4]];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = y * W + x, o = ownr[i];
      if (!o) continue;
      if (!fills.has(o)) { fills.set(o, new Path2D()); edges.set(o, new Path2D()); }
      hexPath(fills.get(o), cx[i], cy[i], s + 0.35);
      for (let d = 0; d < 6; d++) {
        const j = nb(x, y, d);
        if (j >= 0 && ownr[j] === o) continue;
        const [a, b] = EDGE[d];
        const p = edges.get(o), va = hexVert(cx[i], cy[i], s * 0.84, a), vb = hexVert(cx[i], cy[i], s * 0.84, b);
        p.moveTo(va[0], va[1]); p.lineTo(vb[0], vb[1]);
      }
    }
    for (const [o, p] of fills) {
      const pid = o - 1, isAgent = own.agentPids.has(pid);
      ctx.globalAlpha = isAgent ? 0.42 : 0.27;
      ctx.fillStyle = own.color[pid] || "#9aa0a6";
      ctx.fill(p);
    }
    ctx.globalAlpha = 1;
    ctx.lineCap = "round";
    for (const pass of [false, true]) { // AI first, agents on top with a glow
      for (const [o, p] of edges) {
        const pid = o - 1, isAgent = own.agentPids.has(pid);
        if (isAgent !== pass) continue;
        const c = own.color[pid] || "#9aa0a6";
        ctx.strokeStyle = c;
        ctx.lineWidth = isAgent ? Math.max(1.5, s * 0.34) : Math.max(0.9, s * 0.2);
        ctx.shadowColor = isAgent ? c : "transparent";
        ctx.shadowBlur = isAgent ? Math.max(4, s * 1.4) : 0;
        ctx.stroke(p);
      }
    }
    ctx.shadowBlur = 0;

    // natural wonders
    ctx.fillStyle = "#f3d27a";
    for (const i of wonders) {
      const r = Math.max(2.2, s * 0.6);
      ctx.beginPath();
      ctx.moveTo(cx[i], cy[i] - r); ctx.lineTo(cx[i] + r * 0.45, cy[i]); ctx.lineTo(cx[i], cy[i] + r); ctx.lineTo(cx[i] - r * 0.45, cy[i]);
      ctx.closePath(); ctx.fill();
    }

    // cities
    const cities = (m.cities || []).filter((c) => isNum(c.x) && isNum(c.y) && c.x >= 0 && c.x < W && c.y >= 0 && c.y < H);
    for (const c of cities) {
      const i = c.y * W + c.x, pop = isNum(c.pop) ? c.pop : 1;
      const r = Math.max(2, s * 0.5 + Math.sqrt(pop) * s * 0.13);
      const agent = own.agentPids.has(c.pid), cs = !(S.civs || []).some((v) => v.pid === c.pid);
      const col = own.color[c.pid] || "#9aa0a6";
      map.cities.push({ x: cx[i], y: cy[i], r, name: c.name, pop, pid: c.pid, agent, cs, col });
    }
    for (const c of map.cities) {
      ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
      ctx.fillStyle = c.col; ctx.fill();
      ctx.lineWidth = Math.max(1, s * 0.18); ctx.strokeStyle = "#05080c"; ctx.stroke();
      if (c.agent) { ctx.beginPath(); ctx.arc(c.x, c.y, c.r + Math.max(1.4, s * 0.25), 0, Math.PI * 2); ctx.lineWidth = 1.1; ctx.strokeStyle = "rgba(255,255,255,.85)"; ctx.stroke(); }
      if (c.r >= 5.6) {
        ctx.fillStyle = "#05080c"; ctx.font = `700 ${Math.round(c.r * 1.25)}px "Barlow Condensed", sans-serif`;
        ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(String(c.pop), c.x, c.y + 0.5);
      }
    }

    // labels, highest priority first, skipping collisions
    const fs = Math.max(10, Math.min(13.5, s * 2.1));
    const placed = map.cities.map((c) => [c.x - c.r, c.y - c.r, c.x + c.r, c.y + c.r]);
    const hit = (b) => placed.some((p) => b[0] < p[2] && b[2] > p[0] && b[1] < p[3] && b[3] > p[1]);
    const order = [...map.cities].sort((a, b) => (b.agent - a.agent) || (a.cs - b.cs) || (b.pop - a.pop));
    ctx.textBaseline = "middle"; ctx.textAlign = "left"; ctx.lineJoin = "round";
    for (const c of order) {
      const size = c.cs ? fs - 1.5 : fs;
      ctx.font = `${c.cs ? "500 italic" : c.agent ? "700" : "600"} ${size}px "Barlow Condensed", sans-serif`;
      const w = ctx.measureText(c.name).width;
      const hy = size / 2, gap = c.r + 3;
      const spots = [
        [c.x + gap, c.y - hy, c.x + gap + w, c.y + hy], // right
        [c.x - gap - w, c.y - hy, c.x - gap, c.y + hy], // left
        [c.x - w / 2, c.y - gap - size, c.x + w / 2, c.y - gap], // above
        [c.x - w / 2, c.y + gap, c.x + w / 2, c.y + gap + size], // below
      ];
      const inside = (b) => b[0] >= 2 && b[2] <= box.width - 2 && b[1] >= 2 && b[3] <= box.height - 2;
      const b = spots.find((bb) => inside(bb) && !hit(bb));
      if (!b) continue;
      placed.push(b);
      const ty = (b[1] + b[3]) / 2 + 0.5;
      ctx.lineWidth = 3; ctx.strokeStyle = "rgba(5,8,12,.88)"; ctx.strokeText(c.name, b[0], ty);
      ctx.fillStyle = c.agent ? "#ffffff" : c.cs ? "rgba(214,208,192,.7)" : "rgba(226,221,207,.9)";
      ctx.fillText(c.name, b[0], ty);
    }
  }

  function mapHover(ev) {
    const tip = $("tip");
    const rect = canvas.getBoundingClientRect();
    const x = ev.clientX - rect.left, y = ev.clientY - rect.top;
    let best = null, bd = Infinity;
    for (const c of map.cities) {
      const d = Math.hypot(c.x - x, c.y - y);
      if (d < Math.max(9, c.r + 4) && d < bd) { bd = d; best = c; }
    }
    if (!best) { tip.hidden = true; return; }
    const own = owners();
    setHTML(tip, `${esc(best.name)}<small>${esc(own.name[best.pid] || "")} · pop ${best.pop}</small>`);
    tip.style.left = `${best.x}px`;
    tip.style.top = `${best.y - best.r}px`;
    tip.hidden = false;
  }

  // ── standings ──────────────────────────────────────────────
  function renderBoard() {
    const civs = (S && S.civs) || [];
    $("board-empty").hidden = civs.length > 0;
    if (!civs.length) { setHTML($("board"), ""); return; }
    const agents = (S && S.agents) || [];
    let h = `<thead><tr><th class="l"></th><th class="l">Civilization</th><th>Score</th><th>Cities</th><th>Sci</th><th>Cul</th><th>Gold</th><th class="h-mil">Mil</th></tr></thead><tbody>`;
    for (const c of civs) {
      const a = isNum(c.agent) ? agents[c.agent] : null;
      const style = a ? ` style="--rowc:${mix(c.color, 16)};--rowc2:${mix(c.color, 55)}"` : "";
      const tag = a ? ` <span class="tag" style="color:${c.color}">${esc(a.name)}</span>` : "";
      const out = isNum(c.out);
      h += `<tr class="${a ? "is-agent" : ""}${out ? " is-out" : ""}"${style}>` +
        `<td class="rank">${out ? "-" : c.rank}</td>` +
        `<td class="l civcell"><div class="civ"><span class="chip" style="background:${c.color}"></span><span class="nm">${esc(c.civ)}</span>` +
        `<span class="ldr">${esc(c.leader || "")}</span>${tag}</div></td>` +
        `<td class="score">${spark(c.history.turn, c.history.score, c.color, 46, 14)}${num(c.score)}</td>` +
        `<td${out ? ` title="Out of the game on turn ${c.out}"` : ""}>${out ? `out T${c.out}` : num(c.cities)}</td><td class="dim">${num(c.science)}</td><td class="dim">${num(c.culture)}</td>` +
        `<td class="${isNum(c.gold_per_turn) && c.gold_per_turn < 0 ? "neg" : "dim"}">${num(c.gold_per_turn, true)}</td>` +
        `<td class="dim h-mil">${num(c.military)}</td></tr>`;
    }
    setHTML($("board"), h + "</tbody>");
  }

  // ── agent panes ────────────────────────────────────────────
  const STATUS = { thinking: "Thinking", acting: "Acting", waiting: "Waiting for turn", done: "Done", starting: "Not started" };
  const panes = [];

  function paneEl() {
    const el = document.createElement("article");
    el.className = "pane";
    el.innerHTML =
      `<div class="p-head"><div class="p-who"></div><div class="p-side"><div class="goal"></div><div class="status"></div></div><div class="p-civ"></div></div>` +
      `<div class="sec think"><div class="sec-h"><span class="lbl"></span><span class="when"></span></div><p></p><ol class="earlier"></ol></div>` +
      `<div class="sec refl"><div class="sec-h"><span class="lbl"></span><span class="when"></span></div><div class="body"></div></div>` +
      `<div class="sec tools"><div class="sec-h"><span class="lbl">Recent actions</span><span class="when"></span></div><ol></ol></div>` +
      `<div class="p-foot"></div>`;
    const q = (s) => el.querySelector(s);
    return {
      el, who: q(".p-who"), goal: q(".goal"), status: q(".status"), civ: q(".p-civ"),
      think: q(".think"), thinkLbl: q(".think .lbl"), thinkWhen: q(".think .when"), thinkP: q(".think p"), earlier: q(".earlier"),
      reflLbl: q(".refl .lbl"), reflWhen: q(".refl .when"), refl: q(".refl .body"),
      toolsWhen: q(".tools .when"), tools: q(".tools ol"), foot: q(".p-foot"),
    };
  }

  function renderAgents() {
    const agents = (S && S.agents) || [];
    const box = $("agents");
    while (panes.length < agents.length) { const p = paneEl(); panes.push(p); box.appendChild(p.el); }
    while (panes.length > agents.length) panes.pop().el.remove();
    const civs = {};
    for (const c of (S && S.civs) || []) civs[c.pid] = c;
    const nCivs = ((S && S.civs) || []).length;
    agents.forEach((a, i) => {
      const p = panes[i], civ = isNum(a.pid) ? civs[a.pid] : null, color = a.color || "#888";
      if (p.el.style.getPropertyValue("--c") !== color) p.el.style.setProperty("--c", color);
      setHTML(p.who, `<b>${esc(a.name)}</b> · ${esc(model(a.model))}${isNum(a.rank) ? ` · rank ${a.rank} of ${nCivs}` : ""}`);
      setHTML(p.civ, civ || a.civ ? `${esc(a.civ)}${a.leader ? `<span>${esc(a.leader)}</span>` : ""}` : `<span style="margin:0">Seat not in the diary yet</span>`);
      p.goal.hidden = !a.goal;
      setHTML(p.goal, a.goal ? `Goal <b>${esc(a.goal)}</b>` : "");
      const st = a.stale ? "stale" : a.status || "starting";
      const label = a.stale ? "No activity" : STATUS[a.status] || a.status || "Unknown";
      const cls = `status s-${st}`;
      if (p.status.className !== cls) p.status.className = cls;
      setHTML(p.status, `<i></i>${esc(label)}${isNum(a.last_activity) ? `<small>${ago(a.last_activity)}</small>` : ""}`);

      const r = a.reasoning;
      const tcls = `sec think k-${r ? r.kind : "none"}`;
      if (p.think.className !== tcls) p.think.className = tcls;
      setText(p.thinkLbl, r && r.kind === "thinking" ? "Thinking" : "Latest message");
      setText(p.thinkWhen, r ? ago(r.ts) + " ago" : "");
      setText(p.thinkP, r ? r.text : "No reasoning yet.");
      p.thinkP.classList.toggle("none", !r);
      setHTML(p.earlier, (a.earlier || []).map((e) => `<li><span>${ago(e.ts)} ago</span>${esc(e.text)}</li>`).join(""));
      p.thinkP.classList.toggle("clip", p.thinkP.scrollHeight > p.thinkP.clientHeight + 2);

      const f = a.reflections;
      setText(p.reflLbl, f ? `Diary · turn ${f.turn}` : "Diary");
      setText(p.reflWhen, "");
      if (f && (f.tactical || f.strategic || f.planning)) {
        setHTML(p.refl, `<dl>${["tactical", "strategic", "planning"].filter((k) => f[k]).map((k) => `<dt>${k}</dt><dd>${esc(f[k])}</dd>`).join("")}</dl>`);
      } else setHTML(p.refl, `<p class="none" style="margin:0">No end_turn reflections yet.</p>`);

      const tools = a.tools || [];
      setText(p.toolsWhen, isNum(a.sessions) && a.sessions > 1 ? `${a.sessions} sessions` : "");
      setHTML(p.tools, tools.length
        ? tools.map((t, k) => {
          const mark = t.ok === true ? `<span class="ok">✓</span>` : t.ok === false ? `<span class="bad">✕</span>`
            : a.status === "done" ? `<span class="t">-</span>` : `<span class="run">●</span>`;
          return `<li class="${k === 0 ? "first" : ""}"><span class="t">${ago(t.ts)}</span>${mark}<span class="n">${esc(t.name)}</span><span class="a">${esc(t.args || "")}</span></li>`;
        }).join("")
        : `<li><span></span><span></span><span class="a" style="grid-column:3/-1">No tool calls yet.</span></li>`);

      const hist = civ ? civ.history : { turn: [], score: [], science: [], culture: [] };
      const sp = (lbl, key, v) => `<div class="spark"><span class="lbl">${lbl}</span>${spark(hist.turn, hist[key], color, 54, 18)}<b>${num(v)}</b></div>`;
      const u = a.usage || {};
      const money = S.priced ? usd(u.usd) : null;
      const title = `input ${tok(u.input)} · output ${tok(u.output)} · cache read ${tok(u.cache_read)} · cache write ${tok((u.cache_write_5m || 0) + (u.cache_write_1h || 0))} · ${u.requests ?? 0} API calls`;
      setHTML(p.foot,
        (civ ? sp("Score", "score", civ.score) + sp("Science", "science", civ.science) + sp("Culture", "culture", civ.culture) : "") +
        `<div class="money" title="${esc(title)}"><b>${money ?? tok(u.total)}</b><small>${money ? `${tok(u.total)} tokens` : "tokens"}</small></div>`);
    });
  }

  // ── main loop ──────────────────────────────────────────────
  function render() {
    try {
      renderHeader();
      applyLayout();
      renderBoard();
      renderAgents();
      renderMap(false);
    } catch (e) {
      console.error(e);
    }
  }

  canvas.addEventListener("mousemove", mapHover);
  canvas.addEventListener("mouseleave", () => { $("tip").hidden = true; });
  window.addEventListener("resize", () => { applyLayout(); renderMap(true); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => renderMap(true));
  poll();
  setInterval(poll, POLL_MS);
  setInterval(() => { if (S) { renderHeader(); renderAgents(); } }, 1000);
})();
