---
title: Why I host this site on Azure Static Web Apps
date: 2026-05-10
author: Werner Rall
tags: [Azure, Static Web Apps, DevOps]
featured: true
excerpt: A short tour of why a vanilla HTML + CSS site on Azure Static Web Apps is hard to beat for personal sites.
---

Static Web Apps gives me a global CDN, free SSL, a custom domain, GitHub Actions deploys, and a generous free tier — without standing up a single VM.

### The setup in one paragraph

Push to `main`, GitHub Actions builds `src/`, and the content is live on the edge in under a minute. Routing, security headers, and SPA fallback are all configured in `staticwebapp.config.json`.

### What I'd add next

- An Azure Function for a contact form.
- Easy Auth for a members-only area.
- An RSS feed generated at build time.
