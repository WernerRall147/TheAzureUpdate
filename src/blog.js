(function () {
  "use strict";

  var POSTS_DIR = "posts/";

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

  function loadPosts() {
    var files = (window.BLOG_MANIFEST || []).slice();
    return Promise.all(files.map(function (file) {
      return fetch(POSTS_DIR + file, { cache: "no-cache" })
        .then(function (r) {
          if (!r.ok) throw new Error("Failed to load " + file + " (" + r.status + ")");
          return r.text();
        })
        .then(function (raw) {
          var parsed = parseFrontmatter(raw);
          var id = (parsed.meta.id || file.replace(/\.md$/i, "")).toString().trim();
          return {
            id: id,
            file: file,
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

  function renderList(posts) {
    var listEl = document.getElementById("postList");
    var emptyEl = document.getElementById("emptyState");
    if (!posts.length) {
      if (emptyEl) emptyEl.hidden = false;
      if (listEl) listEl.innerHTML = "";
      return;
    }
    listEl.innerHTML = posts.map(function (p) {
      return (
        '<article class="post-card">' +
          '<h2 class="post-card-title"><a href="?post=' + encodeURIComponent(p.id) + '">' + escapeHtml(p.title) + "</a></h2>" +
          '<div class="post-meta">' +
            '<span>' + escapeHtml(p.author) + "</span>" +
            '<span aria-hidden="true">•</span>' +
            '<time datetime="' + escapeHtml(p.date) + '">' + escapeHtml(formatDate(p.date)) + "</time>" +
          "</div>" +
          tagsHtml(p.tags) +
          '<p class="post-excerpt">' + escapeHtml(p.excerpt) + "</p>" +
          '<a class="post-read-more" href="?post=' + encodeURIComponent(p.id) + '">Read more &rarr;</a>' +
        "</article>"
      );
    }).join("");
  }

  function renderSinglePost(post) {
    var listEl = document.getElementById("postList");
    var emptyEl = document.getElementById("emptyState");
    if (emptyEl) emptyEl.hidden = true;

    listEl.innerHTML =
      '<article class="post-full">' +
        '<a class="post-back" href="blog.html">&larr; All posts</a>' +
        '<h1 class="post-full-title">' + escapeHtml(post.title) + "</h1>" +
        '<div class="post-meta">' +
          '<span>' + escapeHtml(post.author) + "</span>" +
          '<span aria-hidden="true">•</span>' +
          '<time datetime="' + escapeHtml(post.date) + '">' + escapeHtml(formatDate(post.date)) + "</time>" +
        "</div>" +
        tagsHtml(post.tags) +
        '<div class="post-body">' + renderMarkdown(post.content) + "</div>" +
      "</article>";

    document.title = post.title + " — The Azure Update";
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
          '<a href="?post=' + encodeURIComponent(p.id) + '">' +
            '<span class="featured-title">' + escapeHtml(p.title) + "</span>" +
            '<span class="featured-date">' + escapeHtml(formatDate(p.date)) + "</span>" +
          "</a>" +
        "</li>"
      );
    }).join("");
  }

  function init() {
    loadPosts().then(function (posts) {
      var params = new URLSearchParams(window.location.search);
      var postId = params.get("post");
      if (postId) {
        var match = null;
        for (var i = 0; i < posts.length; i++) {
          if (posts[i].id === postId) { match = posts[i]; break; }
        }
        if (match) {
          renderSinglePost(match);
        } else {
          renderList(posts);
        }
      } else {
        renderList(posts);
      }
      renderFeatured(posts);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
