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

function readDate(file) {
  try {
    const raw = readFileSync(file, "utf8");
    const fm = raw.match(/^---\s*[\r\n]+([\s\S]*?)[\r\n]+---/);
    if (fm) {
      const dm = fm[1].match(/^date\s*:\s*(.+)$/m);
      if (dm) return dm[1].trim().replace(/^["']|["']$/g, "");
    }
  } catch {
    /* ignore unreadable files */
  }
  return "";
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
        entries.push({ slug: name, date: readDate(indexPath) });
      }
    } catch {
      /* folder without an index.md is not a post */
    }
  } else if (name.toLowerCase().endsWith(".md")) {
    // Legacy flat post: posts/<name>.md
    entries.push({ slug: name, date: readDate(full) });
  }
}

// Newest first (the client re-sorts by date too; this just keeps the
// generated file tidy and human-readable).
entries.sort((a, b) => (b.date || "").localeCompare(a.date || ""));

const list = entries.map((e) => `  ${JSON.stringify(e.slug)}`).join(",\n");

const out = `/* posts/manifest.js - AUTO-GENERATED. Do not edit by hand.
   Regenerate with: npm run posts (runs automatically on npm start).

   Each entry is a post folder under posts/ that contains an index.md,
   e.g. "my-new-post" -> posts/my-new-post/index.md.

   To publish a post:
     1. Create a folder: src/posts/<your-slug>/
     2. Write src/posts/<your-slug>/index.md (with frontmatter).
     3. Run npm start (or npm run posts) - done.
*/
window.BLOG_MANIFEST = [
${list}
];
`;

writeFileSync(join(postsDir, "manifest.js"), out, "utf8");
console.log(`[posts] Generated manifest with ${entries.length} post(s).`);
