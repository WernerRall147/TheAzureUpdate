# The Azure Update

A personal landing page and blog by **Werner Rall**, curating links and long-form posts about Azure, AI / Copilot, Quantum Computing, DevOps, and Microsoft Learn content. Hosted on **Azure Static Web Apps**.

Live site: <https://www.theazureupdate.com>

---

## What the site looks like

The site has **two pages**, both sharing the same navigation, header banner, and dark-mode toggle.

### 1. Home - `src/index.html`

A two-column landing page:

- **Top nav** with anchor links (About, AI & Copilot, Quantum, Blog, Learning, Azure, Community) and social icons (GitHub, X, LinkedIn, YouTube, Blog, Credly).
- **Header banner** - site title "The Azure Update" with the subtitle "with Werner Rall".
- **Sidebar profile** (`.sidebar`) with photo, bio, and outbound links.
- **Main content** organised into themed sections, each rendered as a CSS-grid of clickable tile cards:
  - AI & Copilot
  - Quantum Computing
  - Blog & Articles
  - Learning & Certifications
  - Azure
  - Community
- **Disclaimer section** at the bottom.
- **Floating dark-mode toggle** (sun/moon button, bottom-right), persisted via `localStorage`.

### 2. Blog - `src/blog.html`

Reuses the same nav/header, then switches to a blog-specific layout:

- **Main column** (`.blog-main`) - list of post cards (title, author, date, tags, excerpt, "Read more").
- **Featured sidebar** (`.blog-sidebar`) - top featured posts + external links (aka.ms/wernerrall, Tech Community).
- **Single-post view** - when the URL has `?post=<id>`, the same page renders the full Markdown content with a "← All posts" back link. The page `<title>` updates to match the post.

---

## Architecture

Intentionally framework-free - plain HTML, CSS, and a small amount of vanilla JS. No build step.

```
┌─────────────────────────────────────────────────────────┐
│  Azure Static Web Apps (CDN + static hosting)           │
│  routing/headers via staticwebapp.config.json           │
└─────────────────────────────────────────────────────────┘
                          │
              serves files from src/
                          │
   ┌──────────────────────┼──────────────────────┐
   ▼                      ▼                      ▼
index.html            blog.html               site.css
(landing page)        (blog list +            (shared styles,
                       single post)            light/dark theme)
                          │
                          ├── blog.js          ← fetches + renders posts
                          ├── posts/manifest.js ← list of post filenames
                          └── posts/*.md       ← Markdown posts w/ frontmatter
                                  │
                              marked.min.js (CDN) ← MD → HTML
```

### Key files

| Path | Purpose |
|---|---|
| [src/index.html](src/index.html) | Home page (sidebar profile + tile grids) |
| [src/blog.html](src/blog.html) | Blog page shell (list + featured sidebar) |
| [src/blog.js](src/blog.js) | Client-side blog engine: loads manifest, fetches Markdown, parses YAML-ish frontmatter, renders list or single post |
| [src/posts/manifest.js](src/posts/manifest.js) | `window.BLOG_MANIFEST` - **auto-generated** list of post folder slugs (do not edit by hand) |
| [scripts/generate-manifest.mjs](scripts/generate-manifest.mjs) | Scans `src/posts/*/index.md` and (re)writes `manifest.js`; runs on `npm run posts` and automatically via `prestart` on `npm start` |
| [src/posts/&lt;slug&gt;/index.md](src/posts/) | Individual posts, one folder each; frontmatter keys: `id`, `title`, `date`, `author`, `tags`, `featured`, `excerpt` |
| [src/site.css](src/site.css) | All styling, including dark-mode rules |
| [staticwebapp.config.json](staticwebapp.config.json) | SWA config - security headers, cache rules for `/images/*` and `*.css`, SPA-style fallback to `index.html` |
| [package.json](package.json) | Dev-only deps: `sirv-cli` (local static server) and `@playwright/test` |
| [playwright.config.ts](playwright.config.ts) | Playwright config (chromium/firefox/webkit, baseURL `http://localhost:8000`) |

### How the blog renders (client-side flow)

1. `blog.html` loads `posts/manifest.js`, which sets `window.BLOG_MANIFEST` (a list of post folder slugs).
2. `blog.js` iterates the manifest, `fetch`es each post's Markdown at `posts/<slug>/index.md`.
3. Each file is split into **frontmatter** (between `---` fences) and **body**.
4. Posts are sorted by `date` descending.
5. If `?post=<id>` is in the URL, the matching post is rendered full-width via `marked`. Otherwise the post-card list and Featured sidebar are rendered.
6. Unknown `?post=<id>` falls back to the list.

### Adding a post

Each post is a **self-contained folder**. The manifest is generated for you - you never edit it by hand.

1. Create a folder and an `index.md` inside it:
   ```
   src/posts/my-post/index.md
   ```
   with frontmatter:
   ```md
   ---
   id: my-post
   title: My Post Title
   date: 2026-05-14
   tags: [Azure, AI]
   featured: true
   ---
   Body in Markdown...
   ```
2. Run `npm start` (or `npm run posts`). The manifest regenerates automatically and the post is live.

> The folder name is the post's default `id` and its URL slug (`blog.html?post=my-post`). Images can later live alongside `index.md` in the same folder.

### Hosting / deployment notes

- **Azure Static Web Apps** serves everything in `src/` as-is - no bundler, no SSR.
- [staticwebapp.config.json](staticwebapp.config.json) adds:
  - Security headers: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`.
  - Long cache (`30 days, immutable`) for `/images/*`, 7-day cache for `*.css`.
  - `navigationFallback` → rewrites unknown routes to `index.html`.

---

## Blog view counts

Each blog post shows a live view count (in the post meta line, on both the
card list and the single-post view). It is powered by the Static Web Apps
**managed Functions API** in [api/](api/), backed by **Azure Table Storage**.

```
browser (blog.js) ──HTTP──▶ /api/views (Azure Function) ──▶ Azure Table Storage
   GET  /api/views            → { counts: { <id>: <n> } }   (fills every badge)
   POST /api/views { post }   → { id, count }               (increments on read)
```

- A view is counted at most **once per browser session** per post
  (`sessionStorage` guard), so refreshes do not inflate numbers.
- If the API or storage is unavailable (e.g. plain `npm start` with no
  Functions host), the badges stay hidden and the blog works as before.

### One-time setup

The API needs a storage connection string. In the Azure Portal, open the
Static Web App → **Configuration** → **Application settings** and add:

| Name | Value |
|---|---|
| `VIEWS_TABLES_CONNECTION` | connection string of an Azure Storage account |

Optional overrides: `VIEWS_TABLE_NAME` (default `postViews`). The table and
rows are created automatically on first use. To run the API locally, copy
[api/local.settings.json.example](api/local.settings.json.example) to
`api/local.settings.json`, then run the API with
`cd api; npm install; func start` alongside `npm start`.

---

## Running locally

```powershell
npm install
npm run start
```

This serves `src/` at <http://localhost:8000> via `sirv-cli`.

---

## Tests

End-to-end tests use **Playwright** against the locally-served site. Playwright auto-starts `npm run start` before the suite (see [playwright.config.ts](playwright.config.ts)) and runs across **Chromium, Firefox, and WebKit**.

```powershell
npm run playwright_test
```

Reports are written to `pw-report/` (HTML + `report.json`); per-test traces and screenshots land in `test-results/`.

### Home page suite - [tests/playwright.spec.ts](tests/playwright.spec.ts)

| Test | What it checks |
|---|---|
| `homepage loads with sidebar profile` | `/` returns content; sidebar `#about` shows "Werner Rall". |
| `navigation links are present` | Top nav has exactly 7 anchor links and 6 social icons. |
| `dark mode toggle exists` | `#themeToggle` button is visible. |
| `all sections are present` | `#about`, `#ai`, `#quantum`, `#blog`, `#learning`, `#azure`, `#community`, and `.site-header` are all rendered. |
| `disclaimer is present` | `.disclaimer-section` is visible. |
| `content sections are ordered correctly (newer first)` | Section order is `ai → quantum → blog → learning → azure → community`. |
| `no legacy framework references` | HTML contains no `nicepage` or `jquery` references and does load `site.css`. |
| `tile grid uses CSS grid layout` | `.tile-grid` computed `display` is `grid`. |
| `header banner and sidebar layout are present` | Title, subtitle, sidebar, photo, and `.page-layout` all render. |

### Blog suite - [tests/blog.spec.ts](tests/blog.spec.ts)

| Test | What it checks |
|---|---|
| `loads with title and subtitle banner` | `/blog.html` shows site title + subtitle. |
| `renders post cards from the manifest` | Exactly 2 `.post-card` elements render (matches current manifest). |
| `each post card has title, date, tags, excerpt, and read more link` | All card sub-elements are present and non-empty. |
| `cards are ordered newest first by date` | `time[datetime]` values are sorted descending. |
| `featured sidebar lists featured posts` | `#featuredList` has between 1 and 5 items. |
| `clicking a post card opens the full post and renders markdown` | URL gains `?post=`, full post renders, markdown body has children, back link returns to list. |
| `direct URL with ?post=<id> renders that post` | Deep link to `welcome-to-the-azure-update` renders and updates `<title>`. |
| `unknown ?post=<id> falls back to the post list` | Bad id still shows post cards. |
| `nav links from blog page jump back to home anchors` | `index.html#ai` link navigates and `#ai` is visible. |
| `dark mode toggle persists across navigation to blog page` | Toggling dark mode on `/` keeps `html.dark-mode` after navigating to `/blog.html` (verifies `localStorage` persistence). |
| `home page Blog nav link points to blog.html` | Home nav has a visible "Blog" link pointing to `blog.html`. |

---

## Tech stack at a glance

- **Front end:** HTML5, CSS3 (CSS Grid + custom properties for theming), vanilla JS (no framework).
- **Markdown:** [marked](https://github.com/markedjs/marked) via CDN.
- **Hosting:** Azure Static Web Apps.
- **Local dev server:** [`sirv-cli`](https://github.com/lukeed/sirv).
- **Tests:** [Playwright](https://playwright.dev/) across Chromium / Firefox / WebKit.

> Heads up: I can't fetch your Outlook or Teams items from here - only the README rewrite above is in scope for this tool. If you want, share the list and I can help prioritise it.