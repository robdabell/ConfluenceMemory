import {
  CLOSES,
  TICKER_FACTS,
  formatDateLabel,
  formatFullDate,
  formatMoney,
  formatPct,
  formatSigned,
} from "./data.js";
import { seriesColor } from "./charts.js";

function windowRows(n) {
  // CLOSES is newest-first; take last N sessions, return oldest-first for charting
  return CLOSES.slice(0, n).slice().reverse();
}

function indexed(rows, key) {
  const base = rows[0][key];
  return rows.map((r) => (r[key] / base) * 100);
}

function dayChange(rows, key) {
  const last = rows[rows.length - 1][key];
  const prev = rows[rows.length - 2][key];
  return { last, prev, abs: last - prev, pct: ((last - prev) / prev) * 100 };
}

function windowChange(rows, key) {
  const first = rows[0][key];
  const last = rows[rows.length - 1][key];
  return { abs: last - first, pct: ((last - first) / first) * 100 };
}

function extremes(rows, key) {
  let hi = rows[0];
  let lo = rows[0];
  let best = { date: rows[1]?.date, chg: -Infinity };
  let worst = { date: rows[1]?.date, chg: Infinity };
  for (let i = 0; i < rows.length; i++) {
    if (rows[i][key] > hi[key]) hi = rows[i];
    if (rows[i][key] < lo[key]) lo = rows[i];
    if (i > 0) {
      const chg = ((rows[i][key] - rows[i - 1][key]) / rows[i - 1][key]) * 100;
      if (chg > best.chg) best = { date: rows[i].date, chg };
      if (chg < worst.chg) worst = { date: rows[i].date, chg };
    }
  }
  return { hi, lo, best, worst };
}

function chgClass(n) {
  if (n > 0) return "chg-up";
  if (n < 0) return "chg-down";
  return "chg-flat";
}

function chgArrow(n) {
  if (n > 0) return "↑";
  if (n < 0) return "↓";
  return "→";
}

function renderTile(el, key, rows) {
  const facts = TICKER_FACTS[key];
  const color = seriesColor(facts.series === "tesla" ? "cursor" : "sites");
  const day = dayChange(rows, key);
  const win = windowChange(rows, key);
  const ex = extremes(rows, key);
  const ipo =
    facts.ipo != null
      ? (() => {
          const vs = ((day.last - facts.ipo.price) / facts.ipo.price) * 100;
          return `<li><span class="k">IPO / vs IPO</span><span>${formatMoney(facts.ipo.price)} (${facts.ipo.date}) · <span class="${chgClass(vs)}">${formatPct(vs)}</span></span></li>`;
        })()
      : "";

  el.innerHTML = `
    <div class="stat-tile-head">
      <span class="color-dot" style="background:${color}"></span>
      <span class="name">${facts.name}</span>
      <span class="ticker">${facts.ticker}</span>
    </div>
    <div class="stat-price">${formatMoney(day.last)}</div>
    <div class="stat-changes">
      <span class="${chgClass(day.abs)}">${chgArrow(day.abs)} ${formatSigned(day.abs)} (${formatPct(day.pct)}) day</span>
      <span class="${chgClass(win.abs)}">${chgArrow(win.abs)} ${formatSigned(win.abs)} (${formatPct(win.pct)}) window</span>
    </div>
    <ul class="facts">
      <li><span class="k">52-week range</span><span>${facts.range52}</span></li>
      <li><span class="k">Market cap</span><span>${facts.marketCap}</span></li>
      <li><span class="k">Window high</span><span>${formatMoney(ex.hi[key])} · ${formatDateLabel(ex.hi.date)}</span></li>
      <li><span class="k">Window low</span><span>${formatMoney(ex.lo[key])} · ${formatDateLabel(ex.lo.date)}</span></li>
      <li><span class="k">Best day</span><span class="${chgClass(ex.best.chg)}">${formatDateLabel(ex.best.date)} · ${formatPct(ex.best.chg)}</span></li>
      <li><span class="k">Worst day</span><span class="${chgClass(ex.worst.chg)}">${formatDateLabel(ex.worst.date)} · ${formatPct(ex.worst.chg)}</span></li>
      ${ipo}
    </ul>
  `;
}

function renderTable(el, rows) {
  const newestFirst = rows.slice().reverse();
  const tslaBase = rows[0].tsla;
  const spcxBase = rows[0].spcx;
  el.innerHTML = `
    <table class="price-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>TSLA close</th>
          <th>Index</th>
          <th>SPCX close</th>
          <th>Index</th>
        </tr>
      </thead>
      <tbody>
        ${newestFirst
          .map((r) => {
            const ti = ((r.tsla / tslaBase) * 100).toFixed(1);
            const si = ((r.spcx / spcxBase) * 100).toFixed(1);
            return `<tr>
              <td>${formatFullDate(r.date)}</td>
              <td>${r.tsla.toFixed(2)}</td>
              <td>${ti}</td>
              <td>${r.spcx.toFixed(2)}</td>
              <td>${si}</td>
            </tr>`;
          })
          .join("")}
      </tbody>
    </table>
  `;
}

function niceYTicks(min, max, count = 5) {
  const span = max - min || 1;
  const step = span / (count - 1);
  return Array.from({ length: count }, (_, i) => min + step * i);
}

function renderChart(wrap, rows) {
  const svgHost = wrap.querySelector("[data-price-svg]");
  const tooltip = wrap.querySelector("[data-tooltip]");
  const caption = wrap.querySelector("[data-caption]");
  const cTsla = seriesColor("cursor");
  const cSpcx = seriesColor("sites");

  const w = 900;
  const h = 340;
  const pad = { t: 24, r: 88, b: 36, l: 44 };
  const iw = w - pad.l - pad.r;
  const ih = h - pad.t - pad.b;

  const tslaIdx = indexed(rows, "tsla");
  const spcxIdx = indexed(rows, "spcx");
  const all = [...tslaIdx, ...spcxIdx, 100];
  let ymin = Math.min(...all);
  let ymax = Math.max(...all);
  const padY = (ymax - ymin) * 0.08 || 2;
  ymin -= padY;
  ymax += padY;

  const xAt = (i) => pad.l + (i / (rows.length - 1)) * iw;
  const yAt = (v) => pad.t + ((ymax - v) / (ymax - ymin)) * ih;

  const line = (arr) =>
    arr
      .map((v, i) => `${i === 0 ? "M" : "L"}${xAt(i).toFixed(1)},${yAt(v).toFixed(1)}`)
      .join(" ");

  const yTicks = niceYTicks(ymin, ymax, 5);
  const grid = yTicks
    .map((v) => {
      const y = yAt(v);
      return `<line x1="${pad.l}" y1="${y.toFixed(1)}" x2="${w - pad.r}" y2="${y.toFixed(1)}" stroke="var(--hairline)" stroke-width="1" />
        <text x="${pad.l - 8}" y="${y.toFixed(1)}" text-anchor="end" dominant-baseline="middle"
          font-family="var(--font-mono)" font-size="11" fill="var(--muted)">${v.toFixed(0)}</text>`;
    })
    .join("");

  const baseline = yAt(100);
  const baseLine = `<line x1="${pad.l}" y1="${baseline.toFixed(1)}" x2="${w - pad.r}" y2="${baseline.toFixed(1)}"
    stroke="var(--line)" stroke-width="1.25" stroke-dasharray="4 4" />`;

  // X labels: first, middle-ish, last + a couple more
  const xIdxs = Array.from(
    new Set([
      0,
      Math.floor((rows.length - 1) / 3),
      Math.floor(((rows.length - 1) * 2) / 3),
      rows.length - 1,
    ])
  );
  const xLabels = xIdxs
    .map((i) => {
      const x = xAt(i);
      return `<text x="${x.toFixed(1)}" y="${h - 10}" text-anchor="middle"
        font-family="var(--font-mono)" font-size="11" fill="var(--muted)">${formatDateLabel(rows[i].date)}</text>`;
    })
    .join("");

  const endT = { x: xAt(rows.length - 1), y: yAt(tslaIdx[tslaIdx.length - 1]) };
  const endS = { x: xAt(rows.length - 1), y: yAt(spcxIdx[spcxIdx.length - 1]) };
  let labelTY = endT.y;
  let labelSY = endS.y;
  if (Math.abs(labelTY - labelSY) < 14) {
    if (labelTY <= labelSY) {
      labelTY -= 8;
      labelSY += 8;
    } else {
      labelSY -= 8;
      labelTY += 8;
    }
  }

  const endLabels = `
    <circle cx="${endT.x.toFixed(1)}" cy="${endT.y.toFixed(1)}" r="4" fill="${cTsla}" />
    <circle cx="${endS.x.toFixed(1)}" cy="${endS.y.toFixed(1)}" r="4" fill="${cSpcx}" />
    <text x="${(endT.x + 8).toFixed(1)}" y="${labelTY.toFixed(1)}" dominant-baseline="middle"
      font-family="var(--font-mono)" font-size="12" fill="${cTsla}">TSLA ${tslaIdx[tslaIdx.length - 1].toFixed(1)}</text>
    <text x="${(endS.x + 8).toFixed(1)}" y="${labelSY.toFixed(1)}" dominant-baseline="middle"
      font-family="var(--font-mono)" font-size="12" fill="${cSpcx}">SPCX ${spcxIdx[spcxIdx.length - 1].toFixed(1)}</text>
  `;

  svgHost.innerHTML = `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Indexed closing prices for Tesla and SpaceX">
    ${grid}
    ${baseLine}
    <path d="${line(tslaIdx)}" fill="none" stroke="${cTsla}" stroke-width="2.25" />
    <path d="${line(spcxIdx)}" fill="none" stroke="${cSpcx}" stroke-width="2.25" />
    ${endLabels}
    ${xLabels}
    <line data-crosshair x1="0" y1="${pad.t}" x2="0" y2="${h - pad.b}" stroke="var(--line)" stroke-width="1" opacity="0" />
    <rect data-plot x="${pad.l}" y="${pad.t}" width="${iw}" height="${ih}" fill="transparent" style="cursor:crosshair" />
  </svg>`;

  caption.textContent = `Indexed to 100 at the close on ${formatFullDate(rows[0].date)}. Hover or drag across the chart for each day's closes.`;

  const svg = svgHost.querySelector("svg");
  const cross = svg.querySelector("[data-crosshair]");
  const plot = svg.querySelector("[data-plot]");

  function showAt(clientX) {
    const rect = svg.getBoundingClientRect();
    const sx = ((clientX - rect.left) / rect.width) * w;
    const t = Math.max(0, Math.min(1, (sx - pad.l) / iw));
    const i = Math.round(t * (rows.length - 1));
    const x = xAt(i);
    cross.setAttribute("x1", x.toFixed(1));
    cross.setAttribute("x2", x.toFixed(1));
    cross.setAttribute("opacity", "1");

    const r = rows[i];
    tooltip.classList.add("visible");
    tooltip.innerHTML = `
      <div>${formatFullDate(r.date)}</div>
      <div style="color:${cTsla}">TSLA ${formatMoney(r.tsla)} · idx ${tslaIdx[i].toFixed(1)}</div>
      <div style="color:${cSpcx}">SPCX ${formatMoney(r.spcx)} · idx ${spcxIdx[i].toFixed(1)}</div>
    `;
    const leftPct = (x / w) * 100;
    tooltip.style.left = `${Math.min(72, Math.max(2, leftPct))}%`;
    tooltip.style.top = "12px";
  }

  function hide() {
    cross.setAttribute("opacity", "0");
    tooltip.classList.remove("visible");
  }

  let dragging = false;
  plot.addEventListener("pointerdown", (e) => {
    dragging = true;
    plot.setPointerCapture?.(e.pointerId);
    showAt(e.clientX);
  });
  plot.addEventListener("pointermove", (e) => {
    if (e.pointerType === "mouse" || dragging) showAt(e.clientX);
  });
  plot.addEventListener("pointerup", () => {
    dragging = false;
  });
  plot.addEventListener("pointerleave", () => {
    if (!dragging) hide();
  });
}

export function mountDashboard(root) {
  let windowSize = 50;
  let view = "chart";

  const tileTsla = root.querySelector("[data-tile-tsla]");
  const tileSpcx = root.querySelector("[data-tile-spcx]");
  const chartWrap = root.querySelector("[data-chart-view]");
  const tableWrap = root.querySelector("[data-table-view]");
  const windowSeg = root.querySelector("[data-window]");
  const viewSeg = root.querySelector("[data-view]");

  function sync() {
    const rows = windowRows(windowSize);
    renderTile(tileTsla, "tsla", rows);
    renderTile(tileSpcx, "spcx", rows);
    renderTable(tableWrap, rows);
    renderChart(chartWrap, rows);

    chartWrap.classList.toggle("hidden", view !== "chart");
    tableWrap.classList.toggle("hidden", view !== "table");

    windowSeg.querySelectorAll("button").forEach((b) => {
      b.setAttribute("aria-pressed", String(Number(b.dataset.n) === windowSize));
    });
    viewSeg.querySelectorAll("button").forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.view === view));
    });
  }

  windowSeg.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-n]");
    if (!btn) return;
    windowSize = Number(btn.dataset.n);
    sync();
  });

  viewSeg.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-view]");
    if (!btn) return;
    view = btn.dataset.view;
    sync();
  });

  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener?.("change", sync);

  sync();
  return { sync };
}
