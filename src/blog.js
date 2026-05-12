(function () {
  "use strict";

  var posts = (window.BLOG_POSTS || []).slice().sort(function (a, b) {
    return (b.date || "").localeCompare(a.date || "");
  });

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

  function tagsHtml(tags) {
    if (!tags || !tags.length) return "";
    return '<div class="post-tags">' + tags.map(function (t) {
      return '<span class="post-tag">' + escapeHtml(t) + "</span>";
    }).join("") + "</div>";
  }

  function getPostById(id) {
    for (var i = 0; i < posts.length; i++) {
      if (posts[i].id === id) return posts[i];
    }
    return null;
  }

  function renderList() {
    var listEl = document.getElementById("postList");
    var emptyEl = document.getElementById("emptyState");
    if (!posts.length) {
      if (emptyEl) emptyEl.hidden = false;
      if (listEl) listEl.hidden = true;
      return;
    }

    listEl.innerHTML = posts.map(function (p) {
      return (
        '<article class="post-card">' +
          '<h2 class="post-card-title"><a href="?post=' + encodeURIComponent(p.id) + '">' + escapeHtml(p.title) + "</a></h2>" +
          '<div class="post-meta">' +
            '<span>' + escapeHtml(p.author || "Werner Rall") + "</span>" +
            '<span aria-hidden="true">•</span>' +
            '<time datetime="' + escapeHtml(p.date) + '">' + escapeHtml(formatDate(p.date)) + "</time>" +
          "</div>" +
          tagsHtml(p.tags) +
          '<p class="post-excerpt">' + escapeHtml(p.excerpt || "") + "</p>" +
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
          '<span>' + escapeHtml(post.author || "Werner Rall") + "</span>" +
          '<span aria-hidden="true">•</span>' +
          '<time datetime="' + escapeHtml(post.date) + '">' + escapeHtml(formatDate(post.date)) + "</time>" +
        "</div>" +
        tagsHtml(post.tags) +
        '<div class="post-body">' + (post.content || "") + "</div>" +
      "</article>";

    document.title = post.title + " — The Azure Update";
  }

  function renderFeatured() {
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
    var params = new URLSearchParams(window.location.search);
    var postId = params.get("post");

    if (postId) {
      var post = getPostById(postId);
      if (post) {
        renderSinglePost(post);
      } else {
        renderList();
      }
    } else {
      renderList();
    }

    renderFeatured();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
