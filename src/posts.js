/* =========================================================
   posts.js — Blog post data for The Azure Update
   ---------------------------------------------------------
   To add a new post:
     1. Copy an existing object in the array below.
     2. Give it a unique `id` (lowercase, dashed).
     3. Fill in title, date (YYYY-MM-DD), excerpt and content.
     4. Set `featured: true` to surface it in the right sidebar.
     5. Save the file — the blog page picks it up automatically.

   `content` accepts HTML. Use <p>, <h3>, <ul>, <code>, <pre>,
   <a href="..."> as you would in any HTML document.
   ========================================================= */

window.BLOG_POSTS = [
  {
    id: "welcome-to-the-azure-update",
    title: "Welcome to The Azure Update",
    date: "2026-05-12",
    author: "Werner Rall",
    tags: ["Azure", "Announcement"],
    featured: true,
    excerpt: "Kicking off the blog with a quick note on what to expect — Azure, AI, Quantum, and the occasional PowerShell rant.",
    content: `
      <p>Welcome! This is the first post on <strong>The Azure Update</strong> blog. I've been collecting Azure, AI, and Quantum links here for a while, and I wanted a place to write longer-form thoughts alongside the curated tiles.</p>
      <h3>What you'll find here</h3>
      <ul>
        <li>Hands-on walkthroughs with Azure services I'm actively using.</li>
        <li>Notes on Azure AI Foundry, Copilot, and the agent ecosystem.</li>
        <li>Quantum computing experiments with the Quantum Development Kit.</li>
        <li>DevOps, PowerShell, and the occasional C# deep dive.</li>
      </ul>
      <p>Thanks for stopping by — more soon.</p>
    `
  },
  {
    id: "why-azure-static-web-apps",
    title: "Why I host this site on Azure Static Web Apps",
    date: "2026-05-10",
    author: "Werner Rall",
    tags: ["Azure", "Static Web Apps", "DevOps"],
    featured: true,
    excerpt: "A short tour of why a vanilla HTML + CSS site on Azure Static Web Apps is hard to beat for personal sites.",
    content: `
      <p>Static Web Apps gives me a global CDN, free SSL, a custom domain, GitHub Actions deploys, and a generous free tier — without standing up a single VM.</p>
      <h3>The setup in one paragraph</h3>
      <p>Push to <code>main</code>, GitHub Actions builds <code>src/</code>, and the content is live on the edge in under a minute. Routing, security headers, and SPA fallback are all configured in <code>staticwebapp.config.json</code>.</p>
      <h3>What I'd add next</h3>
      <ul>
        <li>An Azure Function for a contact form.</li>
        <li>Easy Auth for a members-only area.</li>
        <li>An RSS feed generated at build time.</li>
      </ul>
    `
  }
];
