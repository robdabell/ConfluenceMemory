import { CAPABILITIES, PRODUCTS, productTotal } from "./data.js";

const SERIES_VARS = {
  cursor: "--c1",
  sites: "--c2",
  claude: "--c3",
  gemini: "--c4",
};

export function seriesColor(id, el = document.documentElement) {
  return getComputedStyle(el).getPropertyValue(SERIES_VARS[id]).trim();
}

function polar(cx, cy, r, angle) {
  return {
    x: cx + r * Math.cos(angle),
    y: cy + r * Math.sin(angle),
  };
}

function spokeAngles(n) {
  // Start at top (−π/2), go clockwise
  return Array.from({ length: n }, (_, i) => -Math.PI / 2 + (i * 2 * Math.PI) / n);
}

function scoreRadius(score, maxR, maxScore = 5) {
  return (Math.max(0, score) / maxScore) * maxR;
}

function polygonPoints(scores, cx, cy, maxR, angles) {
  return scores
    .map((s, i) => {
      const p = polar(cx, cy, scoreRadius(s, maxR), angles[i]);
      return `${p.x.toFixed(2)},${p.y.toFixed(2)}`;
    })
    .join(" ");
}

function markerPath(kind, x, y, size = 4.5) {
  if (kind === "circle") {
    return `<circle cx="${x}" cy="${y}" r="${size}" />`;
  }
  if (kind === "square") {
    const h = size;
    return `<rect x="${(x - h).toFixed(2)}" y="${(y - h).toFixed(2)}" width="${(h * 2).toFixed(2)}" height="${(h * 2).toFixed(2)}" />`;
  }
  if (kind === "triangle") {
    const h = size * 1.2;
    const a = `${x},${(y - h).toFixed(2)}`;
    const b = `${(x - h).toFixed(2)},${(y + h * 0.7).toFixed(2)}`;
    const c = `${(x + h).toFixed(2)},${(y + h * 0.7).toFixed(2)}`;
    return `<polygon points="${a} ${b} ${c}" />`;
  }
  // diamond
  const h = size * 1.15;
  return `<polygon points="${x},${(y - h).toFixed(2)} ${(x + h).toFixed(2)},${y} ${x},${(y + h).toFixed(2)} ${(x - h).toFixed(2)},${y}" />`;
}

function legendSwatchSvg(product, color) {
  const dash = product.lineDash ? `stroke-dasharray="${product.lineDash.join(" ")}"` : "";
  return `<svg class="swatch" viewBox="0 0 28 14" aria-hidden="true">
    <line x1="2" y1="7" x2="26" y2="7" stroke="${color}" stroke-width="2.5" ${dash} />
    <g fill="${color}" stroke="none">${markerPath(product.marker, 14, 7, 3.2)}</g>
  </svg>`;
}

export function mountOverlayChart(root) {
  const legendEl = root.querySelector("[data-legend]");
  const chartEl = root.querySelector("[data-chart]");
  const readoutEl = root.querySelector("[data-readout]");
  let isolated = null;
  let hoverSpoke = null;

  const size = 560;
  const cx = size / 2;
  const cy = size / 2;
  const maxR = 170;
  const angles = spokeAngles(CAPABILITIES.length);

  // Draw highest total first so smaller sit on top
  const ordered = [...PRODUCTS].sort((a, b) => productTotal(b) - productTotal(a));

  function render() {
    const colors = Object.fromEntries(
      PRODUCTS.map((p) => [p.id, seriesColor(p.id)])
    );

    legendEl.innerHTML = PRODUCTS.map((p) => {
      const pressed = isolated === p.id;
      return `<button type="button" class="legend-btn" data-id="${p.id}" aria-pressed="${pressed}">
        ${legendSwatchSvg(p, colors[p.id])}
        <span>${p.short}</span>
      </button>`;
    }).join("");

    const rings = [1, 2, 3, 4, 5]
      .map((lvl) => {
        const r = scoreRadius(lvl, maxR);
        const pts = angles
          .map((a) => {
            const p = polar(cx, cy, r, a);
            return `${p.x.toFixed(2)},${p.y.toFixed(2)}`;
          })
          .join(" ");
        return `<polygon points="${pts}" fill="none" stroke="var(--hairline)" stroke-width="1" />`;
      })
      .join("");

    const axes = angles
      .map((a, i) => {
        const tip = polar(cx, cy, maxR, a);
        const labelR = maxR + 28;
        const lp = polar(cx, cy, labelR, a);
        const active = hoverSpoke === i;
        return `
          <line x1="${cx}" y1="${cy}" x2="${tip.x.toFixed(2)}" y2="${tip.y.toFixed(2)}"
            stroke="${active ? "var(--line)" : "var(--hairline)"}" stroke-width="${active ? 2 : 1}" />
          <text x="${lp.x.toFixed(2)}" y="${lp.y.toFixed(2)}" text-anchor="middle" dominant-baseline="middle"
            font-family="var(--font-mono)" font-size="12" fill="${active ? "var(--ink)" : "var(--muted)"}"
            pointer-events="none">${CAPABILITIES[i].label}</text>
        `;
      })
      .join("");

    const spokeHits = angles
      .map((a, i) => {
        const hitOuter = polar(cx, cy, maxR + 42, a);
        const hitInner = polar(cx, cy, 28, a);
        const perp = a + Math.PI / 2;
        const half = 18;
        const ox = Math.cos(perp) * half;
        const oy = Math.sin(perp) * half;
        const hitPts = [
          `${(hitInner.x - ox).toFixed(2)},${(hitInner.y - oy).toFixed(2)}`,
          `${(hitOuter.x - ox).toFixed(2)},${(hitOuter.y - oy).toFixed(2)}`,
          `${(hitOuter.x + ox).toFixed(2)},${(hitOuter.y + oy).toFixed(2)}`,
          `${(hitInner.x + ox).toFixed(2)},${(hitInner.y + oy).toFixed(2)}`,
        ].join(" ");
        return `<polygon class="spoke-hit" data-spoke="${i}" points="${hitPts}"
            fill="transparent" style="cursor:pointer" />`;
      })
      .join("");

    const polys = ordered
      .map((p) => {
        const color = colors[p.id];
        const dimmed = isolated && isolated !== p.id;
        const opacity = dimmed ? 0.12 : 1;
        const dash = p.lineDash ? `stroke-dasharray="${p.lineDash.join(" ")}"` : "";
        const pts = polygonPoints(p.scores, cx, cy, maxR, angles);
        const markers = p.scores
          .map((s, i) => {
            const pt = polar(cx, cy, scoreRadius(s, maxR), angles[i]);
            return `<g fill="${color}" stroke="none" pointer-events="none">${markerPath(p.marker, pt.x, pt.y)}</g>`;
          })
          .join("");
        return `<g opacity="${opacity}" pointer-events="none">
          <polygon points="${pts}" fill="${color}" fill-opacity="0.07" stroke="${color}" stroke-width="2.5" ${dash} />
          ${markers}
        </g>`;
      })
      .join("");

    chartEl.innerHTML = `<svg viewBox="0 0 ${size} ${size}" role="img" aria-label="Overlay spider chart of all four products on seven capabilities">
      <g pointer-events="none">${rings}</g>
      <g pointer-events="none">${axes}</g>
      <g>${polys}</g>
      <g>${spokeHits}</g>
    </svg>`;

    if (hoverSpoke == null) {
      readoutEl.textContent =
        "Hover or tap a spoke to compare the four on that capability.";
    } else {
      const cap = CAPABILITIES[hoverSpoke];
      const scores = PRODUCTS.map((p) => {
        const c = colors[p.id];
        return `<span class="score-pair"><span class="dot" style="background:${c}"></span>${p.short} ${p.scores[hoverSpoke]}</span>`;
      }).join("");
      readoutEl.innerHTML = `<strong>${cap.full}</strong> · ${scores}`;
    }
  }

  legendEl.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-id]");
    if (!btn) return;
    const id = btn.dataset.id;
    isolated = isolated === id ? null : id;
    render();
  });

  chartEl.addEventListener("pointerover", (e) => {
    const hit = e.target.closest("[data-spoke]");
    if (!hit) return;
    hoverSpoke = Number(hit.dataset.spoke);
    render();
  });

  chartEl.addEventListener("pointerout", (e) => {
    if (!e.target.closest("[data-spoke]")) return;
    // Only clear if leaving the chart entirely or not entering another spoke
    const related = e.relatedTarget;
    if (related && chartEl.contains(related) && related.closest?.("[data-spoke]")) {
      return;
    }
    hoverSpoke = null;
    render();
  });

  chartEl.addEventListener("click", (e) => {
    const hit = e.target.closest("[data-spoke]");
    if (!hit) return;
    const i = Number(hit.dataset.spoke);
    hoverSpoke = hoverSpoke === i ? null : i;
    render();
  });

  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener?.("change", render);

  render();
  return { render };
}

function strongestWeakest(product) {
  const scored = product.scores.map((s, i) => ({ s, i, ...CAPABILITIES[i] }));
  const max = Math.max(...product.scores);
  const min = Math.min(...product.scores);
  const strong = scored.filter((x) => x.s === max);
  const weak = scored.filter((x) => x.s === min);
  const fmt = (arr) =>
    `${arr.map((x) => x.label).join(", ")} (${arr[0].s})`;
  return `Strongest: ${fmt(strong)}. Weakest: ${fmt(weak)}.`;
}

export function mountCapabilityMap(root) {
  const grid = root.querySelector("[data-cap-grid]");

  function render() {
    const colors = Object.fromEntries(
      PRODUCTS.map((p) => [p.id, seriesColor(p.id)])
    );
    const size = 280;
    const cx = size / 2;
    const cy = size / 2 + 4;
    const maxR = 88;
    const angles = spokeAngles(CAPABILITIES.length);

    grid.innerHTML = PRODUCTS.map((focus) => {
      const total = productTotal(focus);
      const others = PRODUCTS.filter((p) => p.id !== focus.id);
      const rings = [1, 2, 3, 4, 5]
        .map((lvl) => {
          const r = scoreRadius(lvl, maxR);
          const pts = angles
            .map((a) => {
              const p = polar(cx, cy, r, a);
              return `${p.x.toFixed(2)},${p.y.toFixed(2)}`;
            })
            .join(" ");
          return `<polygon points="${pts}" fill="none" stroke="var(--hairline)" stroke-width="1" />`;
        })
        .join("");

      const axes = angles
        .map((a, i) => {
          const tip = polar(cx, cy, maxR, a);
          const lp = polar(cx, cy, maxR + 18, a);
          return `
            <line x1="${cx}" y1="${cy}" x2="${tip.x.toFixed(2)}" y2="${tip.y.toFixed(2)}" stroke="var(--hairline)" stroke-width="1" />
            <text x="${lp.x.toFixed(2)}" y="${lp.y.toFixed(2)}" text-anchor="middle" dominant-baseline="middle"
              font-family="var(--font-mono)" font-size="9" fill="var(--muted)">${CAPABILITIES[i].label}</text>
          `;
        })
        .join("");

      const grey = others
        .map((p) => {
          const pts = polygonPoints(p.scores, cx, cy, maxR, angles);
          return `<polygon points="${pts}" fill="none" stroke="var(--line)" stroke-width="1" opacity="0.55" pointer-events="none" />`;
        })
        .join("");

      const color = colors[focus.id];
      const pts = polygonPoints(focus.scores, cx, cy, maxR, angles);
      const dots = focus.scores
        .map((s, i) => {
          const pt = polar(cx, cy, scoreRadius(s, maxR), angles[i]);
          return `<circle class="vertex-hit" data-product="${focus.id}" data-spoke="${i}"
            cx="${pt.x.toFixed(2)}" cy="${pt.y.toFixed(2)}" r="14" fill="transparent" style="cursor:pointer" />
            <circle cx="${pt.x.toFixed(2)}" cy="${pt.y.toFixed(2)}" r="3.5" fill="${color}" pointer-events="none" />`;
        })
        .join("");

      return `<article class="cap-panel" data-panel="${focus.id}">
        <div class="cap-panel-head">
          <span class="color-dot" style="background:${color}"></span>
          <span class="name">${focus.short}</span>
          <span class="total">${total} / 35</span>
        </div>
        <div class="chart-frame" style="max-width:none">
          <svg viewBox="0 0 ${size} ${size}" role="img" aria-label="${focus.name} capability spider chart, total ${total} of 35">
            <g pointer-events="none">${rings}${axes}${grey}
            <polygon points="${pts}" fill="${color}" fill-opacity="0.12" stroke="${color}" stroke-width="2" />
            </g>
            ${dots}
          </svg>
        </div>
        <p class="cap-caption" data-caption>${strongestWeakest(focus)}</p>
      </article>`;
    }).join("");
  }

  grid.addEventListener("pointerover", (e) => {
    const hit = e.target.closest(".vertex-hit");
    if (!hit) return;
    const panel = hit.closest("[data-panel]");
    const caption = panel.querySelector("[data-caption]");
    const product = PRODUCTS.find((p) => p.id === hit.dataset.product);
    const i = Number(hit.dataset.spoke);
    const cap = CAPABILITIES[i];
    caption.textContent = `${cap.full}: ${product.scores[i]}. ${cap.criterion}.`;
  });

  grid.addEventListener("pointerout", (e) => {
    const hit = e.target.closest(".vertex-hit");
    if (!hit) return;
    const panel = hit.closest("[data-panel]");
    const product = PRODUCTS.find((p) => p.id === panel.dataset.panel);
    panel.querySelector("[data-caption]").textContent = strongestWeakest(product);
  });

  grid.addEventListener("click", (e) => {
    const hit = e.target.closest(".vertex-hit");
    if (!hit) return;
    const panel = hit.closest("[data-panel]");
    const caption = panel.querySelector("[data-caption]");
    const product = PRODUCTS.find((p) => p.id === hit.dataset.product);
    const i = Number(hit.dataset.spoke);
    const cap = CAPABILITIES[i];
    const next = `${cap.full}: ${product.scores[i]}. ${cap.criterion}.`;
    caption.textContent =
      caption.dataset.locked === String(i)
        ? (delete caption.dataset.locked, strongestWeakest(product))
        : ((caption.dataset.locked = String(i)), next);
  });

  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener?.("change", render);

  render();
  return { render };
}
