import {
  CAPABILITIES,
  COMPARISON_ROWS,
  JOBS,
  PRODUCTS,
  SOURCES,
  productTotal,
} from "./data.js";
import { mountCapabilityMap, mountOverlayChart } from "./charts.js";
import { mountDashboard } from "./dashboard.js";

function renderFour() {
  const el = document.querySelector("[data-four]");
  el.innerHTML = PRODUCTS.map(
    (p) => `<article>
      <h3>${p.name}</h3>
      <p>${p.blurb}</p>
    </article>`
  ).join("");
}

function renderComparison() {
  const el = document.querySelector("[data-cmp]");
  const heads = ["", ...PRODUCTS.map((p) => p.name)];
  const body = COMPARISON_ROWS.map((row) => {
    const cells = row.cells
      .map((text, i) => {
        const cls = row.bold[i] ? ' class="lead"' : "";
        const content = row.bold[i] ? `<strong>${text}</strong>` : text;
        return `<td${cls}>${content}</td>`;
      })
      .join("");
    return `<tr><th scope="row">${row.label}</th>${cells}</tr>`;
  }).join("");

  el.innerHTML = `<table class="cmp-table">
    <thead><tr>${heads.map((h) => `<th scope="col">${h}</th>`).join("")}</tr></thead>
    <tbody>${body}</tbody>
  </table>`;
}

function renderScoreGrid() {
  const el = document.querySelector("[data-heat]");
  const head = `<thead><tr>
    <th>Capability</th><th>Criterion</th>
    ${PRODUCTS.map((p) => `<th>${p.short}</th>`).join("")}
  </tr></thead>`;

  const rows = CAPABILITIES.map((cap, i) => {
    const cells = PRODUCTS.map((p) => {
      const s = p.scores[i];
      return `<td class="heat-cell heat-${s}">${s}</td>`;
    }).join("");
    return `<tr>
      <th scope="row">${cap.full}</th>
      <td class="criterion">${cap.criterion}</td>
      ${cells}
    </tr>`;
  }).join("");

  const totals = PRODUCTS.map((p) => {
    const t = productTotal(p);
    return `<td class="heat-cell">${t}</td>`;
  }).join("");

  el.innerHTML = `<table class="heat-table">
    ${head}
    <tbody>
      ${rows}
      <tr class="heat-total">
        <th scope="row">Total of 35</th>
        <td class="criterion"></td>
        ${totals}
      </tr>
    </tbody>
  </table>`;

  const key = document.querySelector("[data-heat-key]");
  key.innerHTML = `<div class="heat-key-swatches">
    ${[0, 1, 2, 3, 4, 5]
      .map((n) => `<span class="heat-${n}">${n}</span>`)
      .join("")}
  </div>
  <span>Higher is better.</span>`;
}

function renderJobs() {
  const el = document.querySelector("[data-jobs]");
  el.innerHTML = JOBS.map(
    (j) => `<div>
      <dt>${j.job}</dt>
      <dd>${j.answer}</dd>
    </div>`
  ).join("");
}

function renderSources() {
  const el = document.querySelector("[data-sources]");
  el.innerHTML = SOURCES.map(
    (s) =>
      `<li><a href="${s.href}" target="_blank" rel="noopener noreferrer">${s.label}</a></li>`
  ).join("");
}

renderFour();
renderComparison();
renderScoreGrid();
renderJobs();
renderSources();

mountOverlayChart(document.querySelector("[data-overlay]"));
mountCapabilityMap(document.querySelector("[data-capability]"));
mountDashboard(document.querySelector("[data-dash]"));
