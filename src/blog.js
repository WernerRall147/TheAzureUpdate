(function () {
  "use strict";

  var POSTS_DIR = "posts/";
  var VIEWS_API = "/api/views";
  var PAGE_SIZE = 10;

  // Format a raw view count as a short, human label (1200 -> "1.2k").
  function formatViews(n) {
    n = Number(n) || 0;
    var num = n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1).replace(/\.0$/, "") + "k" : String(n);
    return num + (n === 1 ? " view" : " views");
  }

  function viewsBadgeHtml(id, count) {
    var label = count == null ? "" : formatViews(count);
    return '<span class="post-views" data-post-views="' + escapeHtml(id) + '"' +
      (count == null ? ' hidden' : '') + '>' +
      '<span class="post-views-icon" aria-hidden="true">\u25C9</span>' +
      '<span class="post-views-count">' + escapeHtml(label) + '</span>' +
      '</span>';
  }

  // Fetch every post's view count in one call. Resolves to a map keyed by
  // post id, or an empty object if the API is unavailable (e.g. local dev).
  function fetchViewCounts() {
    return fetch(VIEWS_API, { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { return (data && data.counts) || {}; })
      .catch(function () { return {}; });
  }

  // Register a view for a post, at most once per browser session so a page
  // refresh does not inflate the count. Resolves to the new count or null.
  function registerView(id) {
    var key = "viewed:" + id;
    var already = false;
    try { already = sessionStorage.getItem(key) === "1"; } catch (e) {}
    var method = already ? "GET" : "POST";
    var opts = already
      ? { cache: "no-store" }
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ post: id })
        };
    var url = already ? VIEWS_API + "?post=" + encodeURIComponent(id) : VIEWS_API;
    return fetch(url, opts)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!already) { try { sessionStorage.setItem(key, "1"); } catch (e) {} }
        return data ? data.count : null;
      })
      .catch(function () { return null; });
  }

  // Fill any rendered view badges from a { id: count } map.
  function applyViewCounts(counts) {
    if (!counts) return;
    var badges = document.querySelectorAll("[data-post-views]");
    Array.prototype.forEach.call(badges, function (el) {
      var id = el.getAttribute("data-post-views");
      if (!(id in counts)) return;
      var countEl = el.querySelector(".post-views-count");
      if (countEl) countEl.textContent = formatViews(counts[id]);
      el.hidden = false;
    });
  }

  function escapeHtml(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatDate(iso) {
    if (!iso) return "";
    var d = new Date(iso + "T00:00:00");
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
  }

  function parseFrontmatter(raw) {
    var meta = {};
    var body = raw;
    var m = raw.match(/^---\s*\r?\n([\s\S]*?)\r?\n---\s*\r?\n?([\s\S]*)$/);
    if (m) {
      body = m[2];
      m[1].split(/\r?\n/).forEach(function (line) {
        var kv = line.match(/^([A-Za-z_][\w-]*)\s*:\s*(.*)$/);
        if (!kv) return;
        var key = kv[1].trim();
        var val = kv[2].trim();
        if ((val.charAt(0) === '"' && val.slice(-1) === '"') ||
            (val.charAt(0) === "'" && val.slice(-1) === "'")) {
          val = val.slice(1, -1);
        }
        if (val.charAt(0) === "[" && val.slice(-1) === "]") {
          val = val.slice(1, -1).split(",").map(function (s) {
            return s.trim().replace(/^["']|["']$/g, "");
          }).filter(Boolean);
        } else if (key === "tags" && val.indexOf(",") !== -1) {
          val = val.split(",").map(function (s) { return s.trim(); }).filter(Boolean);
        } else if (val === "true") {
          val = true;
        } else if (val === "false") {
          val = false;
        }
        meta[key] = val;
      });
    }
    return { meta: meta, body: body };
  }

  function deriveExcerpt(markdown) {
    var blocks = markdown.split(/\r?\n\r?\n/);
    var para = "";
    for (var i = 0; i < blocks.length; i++) {
      var b = blocks[i].trim();
      if (b && b.charAt(0) !== "#") { para = b; break; }
    }
    var text = para
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      .replace(/[*_`>]/g, "")
      .replace(/^[-+]\s+/gm, "")
      .trim();
    if (text.length > 220) text = text.slice(0, 217) + "...";
    return text;
  }

  function tagsHtml(tags) {
    if (!tags || !tags.length) return "";
    var arr = Array.isArray(tags) ? tags : [tags];
    return '<div class="post-tags">' + arr.map(function (t) {
      return '<span class="post-tag">' + escapeHtml(t) + "</span>";
    }).join("") + "</div>";
  }

  function renderMarkdown(md) {
    if (window.marked && typeof window.marked.parse === "function") {
      return window.marked.parse(md);
    }
    return "<pre>" + escapeHtml(md) + "</pre>";
  }

  // marked turns ```mermaid fences into <pre><code class="language-mermaid">.
  // Swap each for a <div class="mermaid"> holding the decoded source, then let
  // Mermaid draw the SVG. textContent gives us the un-escaped diagram text.
  function renderMermaid(root) {
    if (!root || !window.mermaid) return;
    var blocks = root.querySelectorAll("code.language-mermaid");
    if (!blocks.length) return;
    var nodes = [];
    Array.prototype.forEach.call(blocks, function (code) {
      var pre = code.parentNode;
      if (!pre || !pre.parentNode) return;
      var holder = document.createElement("div");
      holder.className = "mermaid";
      holder.textContent = code.textContent;
      pre.parentNode.replaceChild(holder, pre);
      nodes.push(holder);
    });
    if (!nodes.length) return;
    try {
      window.mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: document.documentElement.classList.contains("dark-mode") ? "dark" : "default"
      });
      window.mermaid.run({ nodes: nodes });
    } catch (err) {
      console.error("Mermaid render failed:", err);
    }
  }

  // A manifest entry is normally a post folder slug ("my-post" ->
  // posts/my-post/index.md). Legacy flat files ("my-post.md") are
  // still supported for backwards compatibility.
  function resolveEntry(entry) {
    var slug = String(entry).replace(/\/+$/, "");
    if (/\.md$/i.test(slug)) {
      return { slug: slug.replace(/\.md$/i, ""), url: POSTS_DIR + slug };
    }
    return { slug: slug, url: POSTS_DIR + slug + "/index.md" };
  }

  // Post metadata is baked into posts/manifest.js at build time, so the list
  // and the home page rail render with zero network requests. Only the
  // single-post view fetches Markdown, and only for the post being read.
  function indexPosts() {
    var index = window.BLOG_INDEX;
    if (!index || !index.length) return null;
    return index.slice().map(function (p) {
      return {
        id: p.id,
        file: p.url,
        title: p.title,
        date: p.date || "",
        author: p.author || "Werner Rall",
        tags: p.tags || [],
        featured: p.featured === true,
        excerpt: p.excerpt || ""
      };
    }).sort(function (a, b) {
      return (b.date || "").localeCompare(a.date || "");
    });
  }

  // Fetch and parse a single post's Markdown body on demand.
  function fetchPostContent(entry) {
    return fetch(entry.file, { cache: "no-cache" })
      .then(function (r) {
        if (!r.ok) throw new Error("Failed to load " + entry.file + " (" + r.status + ")");
        return r.text();
      })
      .then(function (raw) {
        var parsed = parseFrontmatter(raw);
        var post = {};
        for (var k in entry) { if (Object.prototype.hasOwnProperty.call(entry, k)) post[k] = entry[k]; }
        post.content = parsed.body;
        if (parsed.meta.title) post.title = parsed.meta.title;
        return post;
      });
  }

  function loadPosts() {
    var files = (window.BLOG_MANIFEST || []).slice();
    return Promise.all(files.map(function (entry) {
      var ref = resolveEntry(entry);
      return fetch(ref.url, { cache: "no-cache" })
        .then(function (r) {
          if (!r.ok) throw new Error("Failed to load " + ref.url + " (" + r.status + ")");
          return r.text();
        })
        .then(function (raw) {
          var parsed = parseFrontmatter(raw);
          var id = (parsed.meta.id || ref.slug).toString().trim();
          return {
            id: id,
            file: ref.url,
            title: parsed.meta.title || id,
            date: parsed.meta.date || "",
            author: parsed.meta.author || "Werner Rall",
            tags: parsed.meta.tags || [],
            featured: parsed.meta.featured === true,
            excerpt: parsed.meta.excerpt || deriveExcerpt(parsed.body),
            content: parsed.body
          };
        })
        .catch(function (err) {
          console.error(err);
          return null;
        });
    })).then(function (results) {
      return results.filter(Boolean).sort(function (a, b) {
        return (b.date || "").localeCompare(a.date || "");
      });
    });
  }

  function currentPage() {
    var n = parseInt(new URLSearchParams(window.location.search).get("page"), 10);
    return isNaN(n) || n < 1 ? 1 : n;
  }

  function pagerHtml(page, totalPages) {
    if (totalPages <= 1) return "";
    var parts = ['<nav class="post-pager" aria-label="Post pages">'];
    parts.push(page > 1
      ? '<a class="post-pager-link" href="?page=' + (page - 1) + '" rel="prev">&larr; Newer</a>'
      : '<span class="post-pager-link is-disabled" aria-disabled="true">&larr; Newer</span>');
    parts.push('<span class="post-pager-status">Page ' + page + ' of ' + totalPages + '</span>');
    parts.push(page < totalPages
      ? '<a class="post-pager-link" href="?page=' + (page + 1) + '" rel="next">Older &rarr;</a>'
      : '<span class="post-pager-link is-disabled" aria-disabled="true">Older &rarr;</span>');
    parts.push("</nav>");
    return parts.join("");
  }

  function renderList(posts, page) {
    var listEl = document.getElementById("postList");
    var emptyEl = document.getElementById("emptyState");
    if (!listEl) return; // Home page has a Featured rail but no full post list.
    if (!posts.length) {
      if (emptyEl) emptyEl.hidden = false;
      if (listEl) listEl.innerHTML = "";
      return;
    }
    var totalPages = Math.ceil(posts.length / PAGE_SIZE);
    var current = Math.min(page || 1, totalPages);
    var start = (current - 1) * PAGE_SIZE;
    var pageItems = posts.slice(start, start + PAGE_SIZE);

    listEl.innerHTML = pageItems.map(function (p) {
      return (
        '<article class="post-card">' +
          '<h2 class="post-card-title"><a href="?post=' + encodeURIComponent(p.id) + '">' + escapeHtml(p.title) + "</a></h2>" +
          '<div class="post-meta">' +
            '<span>' + escapeHtml(p.author) + "</span>" +
            '<span aria-hidden="true">•</span>' +
            '<time datetime="' + escapeHtml(p.date) + '">' + escapeHtml(formatDate(p.date)) + "</time>" +
          '<span aria-hidden="true">\u2022</span>' +
          viewsBadgeHtml(p.id, null) +
          "</div>" +
          tagsHtml(p.tags) +
          '<p class="post-excerpt">' + escapeHtml(p.excerpt) + "</p>" +
          '<a class="post-read-more" href="?post=' + encodeURIComponent(p.id) + '">Read more &rarr;</a>' +
        "</article>"
      );
    }).join("") + pagerHtml(current, totalPages);
  }

  // The post shell (title, meta, tags) comes from the prebuilt index and is
  // painted immediately; the body is filled in once its Markdown arrives, so
  // the reader never stares at a blank page during the fetch.
  function renderSinglePost(post) {
    var listEl = document.getElementById("postList");
    var emptyEl = document.getElementById("emptyState");
    if (!listEl) return;
    if (emptyEl) emptyEl.hidden = true;

    var body = post.content == null
      ? '<p class="post-loading">Loading post&hellip;</p>'
      : renderMarkdown(post.content);

    listEl.innerHTML =
      '<article class="post-full">' +
        '<a class="post-back" href="blog.html">&larr; All posts</a>' +
        '<h1 class="post-full-title">' + escapeHtml(post.title) + "</h1>" +
        '<div class="post-meta">' +
          '<span>' + escapeHtml(post.author) + "</span>" +
          '<span aria-hidden="true">•</span>' +
          '<time datetime="' + escapeHtml(post.date) + '">' + escapeHtml(formatDate(post.date)) + "</time>" +
          '<span aria-hidden="true">\u2022</span>' +
          viewsBadgeHtml(post.id, null) +
        "</div>" +
        tagsHtml(post.tags) +
        '<div class="post-body">' + body + "</div>" +
      "</article>";

    if (post.content != null) renderMermaid(listEl);

    document.title = post.title + " - The Azure Update";
  }

  // Swap the placeholder for the rendered Markdown once it has loaded.
  function fillPostBody(post) {
    var bodyEl = document.querySelector(".post-full .post-body");
    if (!bodyEl) return renderSinglePost(post);
    bodyEl.innerHTML = renderMarkdown(post.content);
    renderMermaid(bodyEl);
    var titleEl = document.querySelector(".post-full-title");
    if (titleEl && post.title) {
      titleEl.textContent = post.title;
      document.title = post.title + " - The Azure Update";
    }
  }

  function renderFeatured(posts) {
    var featuredEl = document.getElementById("featuredList");
    if (!featuredEl) return;

    var featured = posts.filter(function (p) { return p.featured; });
    var pool = featured.length ? featured : posts.slice(0, 5);

    if (!pool.length) {
      featuredEl.innerHTML = '<p class="featured-empty">No featured posts yet.</p>';
      return;
    }
    featuredEl.innerHTML = pool.slice(0, 5).map(function (p) {
      return (
        '<li class="featured-item">' +
          '<a href="blog.html?post=' + encodeURIComponent(p.id) + '">' +
            '<span class="featured-title">' + escapeHtml(p.title) + "</span>" +
            '<span class="featured-date">' + escapeHtml(formatDate(p.date)) + "</span>" +
          "</a>" +
        "</li>"
      );
    }).join("");
  }

  function init() {
    var postId = new URLSearchParams(window.location.search).get("post");
    var meta = indexPosts();

    // Fallback for a stale manifest without BLOG_INDEX: fetch every post.
    if (!meta) {
      loadPosts().then(function (posts) {
        var match = findPost(posts, postId);
        if (match) {
          renderSinglePost(match);
          trackSingleView(match);
        } else {
          renderList(posts, currentPage());
          fetchViewCounts().then(applyViewCounts);
        }
        renderFeatured(posts);
      });
      return;
    }

    renderFeatured(meta);

    var entry = findPost(meta, postId);
    if (entry) {
      // Paint the shell first, then fill the body when the Markdown lands.
      renderSinglePost(entry);
      fetchPostContent(entry).then(function (post) {
        fillPostBody(post);
        trackSingleView(post);
      }).catch(function (err) {
        console.error(err);
        renderList(meta, currentPage());
        fetchViewCounts().then(applyViewCounts);
      });
      return;
    }

    renderList(meta, currentPage());
    fetchViewCounts().then(applyViewCounts);
  }

  function findPost(posts, postId) {
    if (!postId) return null;
    for (var i = 0; i < posts.length; i++) {
      if (posts[i].id === postId) return posts[i];
    }
    return null;
  }

  function trackSingleView(post) {
    registerView(post.id).then(function (count) {
      if (count != null) applyViewCounts(defineOne(post.id, count));
    });
  }

  function defineOne(id, count) {
    var o = {};
    o[id] = count;
    return o;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
