#!/usr/bin/env node
/*
 * generate-manifest.mjs
 * ---------------------------------------------------------------
 * Scans src/posts/ and (re)writes src/posts/manifest.js.
 *
 * A blog post is simply a folder under posts/ that contains an
 * index.md file, e.g.:
 *
 *     src/posts/my-new-post/index.md
 *
 * To publish a post: create the folder, write index.md, and run
 * `npm run posts` (this also runs automatically on `npm start`).
 *
 * Legacy flat posts (posts/<name>.md) are still picked up so older
 * content keeps working.
 */
import { readdirSync, statSync, readFileSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const postsDir = join(here, "..", "src", "posts");

// Split a post file into its frontmatter block and body.
function splitFrontmatter(raw) {
  const m = raw.match(/^---\s*\r?\n([\s\S]*?)\r?\n---\s*\r?\n?([\s\S]*)$/);
  return m ? { fm: m[1], body: m[2] } : { fm: "", body: raw };
}

// Parse the YAML-ish frontmatter. Mirrors the parser in src/blog.js so the
// build-time index and any client-side fallback agree on the same values.
function parseFrontmatter(fm) {
  const meta = {};
  for (const line of fm.split(/\r?\n/)) {
    const kv = line.match(/^([A-Za-z_][\w-]*)\s*:\s*(.*)$/);
    if (!kv) continue;
    const key = kv[1].trim();
    let val = kv[2].trim();
    if ((val.startsWith('"') && val.endsWith('"')) ||
        (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    if (val.startsWith("[") && val.endsWith("]")) {
      meta[key] = val.slice(1, -1).split(",")
        .map((s) => s.trim().replace(/^["']|["']$/g, ""))
        .filter(Boolean);
    } else if (key === "tags" && val.includes(",")) {
      meta[key] = val.split(",").map((s) => s.trim()).filter(Boolean);
    } else if (val === "true") {
      meta[key] = true;
    } else if (val === "false") {
      meta[key] = false;
    } else {
      meta[key] = val;
    }
  }
  return meta;
}

// First real paragraph, stripped of Markdown, used when a post has no
// explicit excerpt. HTML comments (such as the generated-file marker) and
// headings are skipped.
function deriveExcerpt(markdown) {
  const blocks = markdown.split(/\r?\n\r?\n/);
  let para = "";
  for (const block of blocks) {
    const b = block.trim();
    if (!b || b.startsWith("#") || b.startsWith("<!--")) continue;
    para = b;
    break;
  }
  let text = para
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[*_`>]/g, "")
    .replace(/^[-+]\s+/gm, "")
    .trim();
  if (text.length > 220) text = text.slice(0, 217) + "...";
  return text;
}

function readPost(slug, file, url) {
  const raw = readFileSync(file, "utf8");
  const { fm, body } = splitFrontmatter(raw);
  const meta = parseFrontmatter(fm);
  const tags = meta.tags == null ? [] : (Array.isArray(meta.tags) ? meta.tags : [meta.tags]);
  return {
    id: String(meta.id || slug).trim(),
    url,
    title: meta.title || slug,
    date: meta.date || "",
    author: meta.author || "Werner Rall",
    tags,
    featured: meta.featured === true,
    excerpt: meta.excerpt || deriveExcerpt(body)
  };
}

const entries = [];

for (const name of readdirSync(postsDir)) {
  if (name.startsWith(".")) continue;
  const full = join(postsDir, name);
  const stat = statSync(full);

  if (stat.isDirectory()) {
    const indexPath = join(full, "index.md");
    try {
      if (statSync(indexPath).isFile()) {
        entries.push({
          slug: name,
          post: readPost(name, indexPath, `posts/${name}/index.md`)
        });
      }
    } catch {
      /* folder without an index.md is not a post */
    }
  } else if (name.toLowerCase().endsWith(".md")) {
    // Legacy flat post: posts/<name>.md
    const slug = name.replace(/\.md$/i, "");
    entries.push({
      slug: name,
      post: readPost(slug, full, `posts/${name}`)
    });
  }
}

// Newest first (the client re-sorts by date too; this just keeps the
// generated file tidy and human-readable).
entries.sort((a, b) => (b.post.date || "").localeCompare(a.post.date || ""));

const list = entries.map((e) => `  ${JSON.stringify(e.slug)}`).join(",\n");
const index = entries.map((e) => `  ${JSON.stringify(e.post)}`).join(",\n");

const out = `/* posts/manifest.js - AUTO-GENERATED. Do not edit by hand.
   Regenerate with: npm run posts (runs automatically on npm start).

   Each entry is a post folder under posts/ that contains an index.md,
   e.g. "my-new-post" -> posts/my-new-post/index.md.

   BLOG_INDEX carries the frontmatter for every post so the blog list and
   the home page rail can render without fetching each Markdown file. Only
   the single-post view fetches its own Markdown.

   To publish a post:
     1. Create a folder: src/posts/<your-slug>/
     2. Write src/posts/<your-slug>/index.md (with frontmatter).
     3. Run npm start (or npm run posts) - done.
*/
window.BLOG_MANIFEST = [
${list}
];

window.BLOG_INDEX = [
${index}
];
`;

writeFileSync(join(postsDir, "manifest.js"), out, "utf8");
console.log(`[posts] Generated manifest with ${entries.length} post(s).`);
