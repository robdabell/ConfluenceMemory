/** @typedef {{ date: string, tsla: number, spcx: number }} PriceRow */

export const PRODUCTS = [
  {
    id: "cursor",
    name: "Cursor Canvases",
    short: "Cursor",
    blurb:
      "Interactive reports and dashboards that render beside the agent chat inside the IDE.",
    scores: [2, 3, 0, 3, 1, 5, 5],
    lineDash: null,
    marker: "circle",
  },
  {
    id: "sites",
    name: "ChatGPT Sites",
    short: "Sites",
    blurb:
      "A site or small app built in ChatGPT Work and hosted for you, with a real URL.",
    scores: [5, 5, 5, 5, 0, 4, 3],
    lineDash: [7, 4],
    marker: "square",
  },
  {
    id: "claude",
    name: "Claude artifacts",
    short: "Claude",
    blurb:
      "Pages and tools built beside the chat, published to a claude.ai link.",
    scores: [4, 3, 2, 3, 5, 3, 3],
    lineDash: [2.5, 3.5],
    marker: "triangle",
  },
  {
    id: "gemini",
    name: "Gemini Canvas",
    short: "Gemini",
    blurb:
      "A code preview inside the Gemini app, shared as a Gemini link.",
    scores: [3, 2, 1, 1, 4, 1, 1],
    lineDash: [10, 3, 2, 3],
    marker: "diamond",
  },
];

export const CAPABILITIES = [
  {
    label: "Reach",
    full: "Sharing reach",
    criterion: "How widely a published page can be opened",
  },
  {
    label: "Access",
    full: "Access control",
    criterion: "Choosing who sees it: people, workspace or public",
  },
  {
    label: "Domain",
    full: "Own domain",
    criterion: "Hosting the page on your own domain",
  },
  {
    label: "Data",
    full: "Data and backend",
    criterion: "Database, logins, storage or live data behind the page",
  },
  {
    label: "Free tier",
    full: "Free-plan access",
    criterion: "Works without paying",
  },
  {
    label: "Refresh",
    full: "Refresh and reuse",
    criterion: "Reruns, versions and updates after publishing",
  },
  {
    label: "Dev fit",
    full: "Dev workflow fit",
    criterion: "Sits inside a coding workflow",
  },
];

export const COMPARISON_ROWS = [
  {
    label: "Lives in",
    cells: [
      "Agents Window or editor side panel. Built from React components such as tables, charts and diffs.",
      "ChatGPT Work on web, or Work or Codex in the desktop app. Public beta since 9 Jul 2026.",
      "An artifact pane next to the chat, from documents to interactive apps.",
      "A Canvas panel in the Gemini app. You switch Canvas on before asking for a page.",
    ],
    bold: [false, false, false, false],
  },
  {
    label: "Publish and share",
    cells: [
      "Publish by URL since June 2026. Viewers see a snapshot you republish.",
      "Hosted at a chatgpt.site address as a living page, with versions.",
      "Publish gives a claude.ai link. A Netlify connector can deploy the code as a real site.",
      "A g.co/gemini/share link that opens inside Gemini on the web. Workspace users can also share through Drive.",
    ],
    bold: [false, true, false, false],
  },
  {
    label: "Who can view",
    cells: [
      "Members of your Cursor team only, read-only.",
      "Private at first. Share with chosen people, your workspace, or the public.",
      "One source calls it public or nothing. Team and Enterprise need an Owner to allow external sharing.",
      "Anyone with the link. No password, invite list or analytics, and viewers can copy the source.",
    ],
    bold: [false, true, false, false],
  },
  {
    label: "Custom domain",
    cells: [
      "No",
      "Yes, by adding DNS records.",
      "No on claude.ai. Possible through Netlify.",
      "No. Third-party hosts are the usual route.",
    ],
    bold: [false, true, false, false],
  },
  {
    label: "Data and backend",
    cells: [
      "Reruns saved SQL, API or shell queries for fresh data. Canvases are saved outside your git repo by default.",
      "Can include a database, per-user logins, saved progress and uploads.",
      "Reported: storage up to 20MB, MCP integrations and live-refreshing artifacts.",
      "Previews code only. For server-side keys, Google points to AI Studio and Cloud Run.",
    ],
    bold: [false, true, false, false],
  },
  {
    label: "Plans",
    cells: [
      "Sharing needs a paid Cursor plan.",
      "Plus, Pro, Business, Enterprise and Edu. Not Free or Go.",
      "Every plan, including Free.",
      "Canvas is in the Gemini app. Usage limits change often.",
    ],
    bold: [false, false, true, false],
  },
];

export const JOBS = [
  {
    job: "Review agent output inside the IDE",
    answer: "Cursor Canvases",
  },
  {
    job: "Hosted app with logins, a database and your own domain",
    answer: "ChatGPT Sites",
  },
  {
    job: "Quick shareable page or tool, even on a free plan",
    answer: "Claude artifacts, or Gemini Canvas",
  },
  {
    job: "Full-stack app on Google tooling",
    answer: "Gemini through AI Studio",
  },
];

export const SOURCES = [
  {
    label: "StockAnalysis, TSLA price history",
    href: "https://stockanalysis.com/stocks/tsla/history/",
  },
  {
    label: "StockAnalysis, SPCX price history",
    href: "https://stockanalysis.com/stocks/spcx/history/",
  },
  {
    label: "Google Finance, TSLA",
    href: "https://www.google.com/finance/quote/TSLA:NASDAQ",
  },
  {
    label: "Google Finance, SPCX",
    href: "https://www.google.com/finance/quote/SPCX:NASDAQ",
  },
  {
    label: "The Motley Fool, SpaceX IPO",
    href: "https://www.fool.com/investing/2026/10/08/if-you-invested-5000-in-spacex-at-its-ipo-here-is/",
  },
  {
    label: "Cursor docs, Canvases",
    href: "https://cursor.com/docs/agent/tools/canvas",
  },
  {
    label: "OpenAI Help, ChatGPT Sites",
    href: "https://help.openai.com/en/articles/20001339-creating-and-using-chatgpt-sites",
  },
  {
    label: "Markloop, artifact sharing compared",
    href: "https://markloop.io/blog/claude-artifact-sharing-compared/",
  },
  {
    label: "DEV, where to host what your AI builds",
    href: "https://dev.to/amir_wm/chatgpt-sites-vs-the-alternatives-where-to-host-what-your-ai-builds-3i37",
  },
  {
    label: "Shareable, sharing a Gemini page",
    href: "https://useshareable.com/blog/how-to-share-a-gemini-page",
  },
  {
    label: "GeminiLaunch, Canvas to a website",
    href: "https://www.geminilaunch.com/blogs/turn-gemini-canvas-into-website",
  },
  {
    label: "Google Workspace Updates, sharing canvases",
    href: "https://workspaceupdates.googleblog.com/2026/04/share-chats-canvases-and-generated-media-from-the-Gemini-app-securely-via-Google-Drive.html",
  },
];

/** Newest first. Dates are 2026. */
export const CLOSES = [
  { date: "10-16", tsla: 354.72, spcx: 146.03 },
  { date: "10-15", tsla: 362.44, spcx: 148.62 },
  { date: "10-14", tsla: 367.16, spcx: 152.16 },
  { date: "10-13", tsla: 375.23, spcx: 156.54 },
  { date: "10-12", tsla: 378.03, spcx: 163.42 },
  { date: "10-09", tsla: 382.7, spcx: 162.57 },
  { date: "10-08", tsla: 375.0, spcx: 160.57 },
  { date: "10-07", tsla: 377.81, spcx: 167.6 },
  { date: "10-06", tsla: 380.68, spcx: 171.92 },
  { date: "10-05", tsla: 378.73, spcx: 171.09 },
  { date: "10-02", tsla: 370.59, spcx: 158.96 },
  { date: "10-01", tsla: 354.11, spcx: 148.07 },
  { date: "09-30", tsla: 354.81, spcx: 150.86 },
  { date: "09-29", tsla: 352.84, spcx: 149.24 },
  { date: "09-28", tsla: 357.45, spcx: 145.47 },
  { date: "09-25", tsla: 372.11, spcx: 148.68 },
  { date: "09-24", tsla: 377.94, spcx: 148.03 },
  { date: "09-23", tsla: 380.12, spcx: 148.36 },
  { date: "09-22", tsla: 378.9, spcx: 154.72 },
  { date: "09-21", tsla: 375.3, spcx: 151.85 },
  { date: "09-18", tsla: 364.27, spcx: 152.71 },
  { date: "09-17", tsla: 366.2, spcx: 154.81 },
  { date: "09-16", tsla: 358.08, spcx: 150.88 },
  { date: "09-15", tsla: 356.58, spcx: 143.49 },
  { date: "09-14", tsla: 358.97, spcx: 148.15 },
  { date: "09-11", tsla: 365.44, spcx: 151.21 },
  { date: "09-10", tsla: 363.56, spcx: 148.18 },
  { date: "09-09", tsla: 367.81, spcx: 147.55 },
  { date: "09-08", tsla: 368.16, spcx: 153.47 },
  { date: "09-04", tsla: 354.08, spcx: 147.95 },
  { date: "09-03", tsla: 376.37, spcx: 149.74 },
  { date: "09-02", tsla: 357.01, spcx: 140.71 },
  { date: "09-01", tsla: 356.09, spcx: 142.23 },
  { date: "08-31", tsla: 367.95, spcx: 143.69 },
  { date: "08-28", tsla: 348.75, spcx: 141.5 },
  { date: "08-27", tsla: 354.81, spcx: 140.87 },
  { date: "08-26", tsla: 345.82, spcx: 139.63 },
  { date: "08-25", tsla: 350.25, spcx: 137.95 },
  { date: "08-24", tsla: 348.95, spcx: 135.0 },
  { date: "08-21", tsla: 362.86, spcx: 136.97 },
  { date: "08-20", tsla: 345.13, spcx: 134.0 },
  { date: "08-19", tsla: 351.12, spcx: 139.65 },
  { date: "08-18", tsla: 336.87, spcx: 143.34 },
  { date: "08-17", tsla: 339.3, spcx: 146.23 },
  { date: "08-14", tsla: 342.27, spcx: 140.0 },
  { date: "08-13", tsla: 339.96, spcx: 141.29 },
  { date: "08-12", tsla: 327.51, spcx: 146.15 },
  { date: "08-11", tsla: 332.81, spcx: 133.29 },
  { date: "08-10", tsla: 330.88, spcx: 138.74 },
  { date: "08-07", tsla: 328.58, spcx: 133.11 },
];

export const TICKER_FACTS = {
  tsla: {
    name: "Tesla",
    ticker: "NASDAQ: TSLA",
    series: "tesla",
    range52: "$297.38 to $498.82",
    marketCap: "$1.40T",
    ipo: null,
  },
  spcx: {
    name: "SpaceX",
    ticker: "NASDAQ: SPCX",
    series: "spacex",
    range52: "$104.83 to $225.64",
    marketCap: "$1.96T",
    ipo: { price: 135.0, date: "12 Jun 2026" },
  },
};

export function productTotal(product) {
  return product.scores.reduce((a, b) => a + b, 0);
}

export function formatMoney(n) {
  return `$${n.toFixed(2)}`;
}

export function formatSigned(n, digits = 2) {
  const sign = n > 0 ? "+" : n < 0 ? "−" : "";
  return `${sign}${Math.abs(n).toFixed(digits)}`;
}

export function formatPct(n) {
  const sign = n > 0 ? "+" : n < 0 ? "−" : "";
  return `${sign}${Math.abs(n).toFixed(1)}%`;
}

/** Parse MM-DD (2026) into a display label. */
export function formatDateLabel(md) {
  const [mm, dd] = md.split("-").map(Number);
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  return `${months[mm - 1]} ${dd}`;
}

export function formatFullDate(md) {
  return `${formatDateLabel(md)} 2026`;
}
