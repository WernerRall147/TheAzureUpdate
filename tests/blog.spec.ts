import { test, expect } from '@playwright/test';

test.describe('Blog page', () => {

  test('loads with title and subtitle banner', async ({ page }) => {
    await page.goto('/blog.html');
    await expect(page.locator('.site-title')).toHaveText('The Azure Update');
    await expect(page.locator('.site-subtitle')).toContainText('Werner Rall');
  });

  test('renders post cards from the manifest', async ({ page }) => {
    await page.goto('/blog.html');
    // Wait for at least one card to render (posts are fetched async)
    await expect(page.locator('.post-card').first()).toBeVisible();
    const cards = page.locator('.post-card');
    await expect(cards).toHaveCount(2); // welcome + static-web-apps post
  });

  test('each post card has title, date, tags, excerpt, and read more link', async ({ page }) => {
    await page.goto('/blog.html');
    const firstCard = page.locator('.post-card').first();
    await expect(firstCard.locator('.post-card-title a')).toBeVisible();
    await expect(firstCard.locator('time')).toBeVisible();
    await expect(firstCard.locator('.post-tag').first()).toBeVisible();
    await expect(firstCard.locator('.post-excerpt')).not.toBeEmpty();
    await expect(firstCard.locator('.post-read-more')).toBeVisible();
  });

  test('cards are ordered newest first by date', async ({ page }) => {
    await page.goto('/blog.html');
    await expect(page.locator('.post-card').first()).toBeVisible();
    const dates = await page.locator('.post-card time').evaluateAll(els =>
      els.map(el => el.getAttribute('datetime') || '')
    );
    const sorted = [...dates].sort().reverse();
    expect(dates).toEqual(sorted);
  });

  test('featured sidebar lists featured posts', async ({ page }) => {
    await page.goto('/blog.html');
    await expect(page.locator('#featuredList .featured-item').first()).toBeVisible();
    const featuredCount = await page.locator('#featuredList .featured-item').count();
    expect(featuredCount).toBeGreaterThan(0);
    expect(featuredCount).toBeLessThanOrEqual(5);
  });

  test('clicking a post card opens the full post and renders markdown', async ({ page }) => {
    await page.goto('/blog.html');
    await expect(page.locator('.post-card').first()).toBeVisible();

    const firstTitle = await page.locator('.post-card-title a').first().textContent();
    await page.locator('.post-card-title a').first().click();

    await expect(page).toHaveURL(/\?post=/);
    await expect(page.locator('.post-full')).toBeVisible();
    await expect(page.locator('.post-full-title')).toHaveText(firstTitle!.trim());

    // Markdown rendered: at least one paragraph or heading element in the body
    const bodyChildren = await page.locator('.post-body > *').count();
    expect(bodyChildren).toBeGreaterThan(0);

    // Back link returns to the list
    await page.locator('.post-back').click();
    await expect(page.locator('.post-card').first()).toBeVisible();
  });

  test('direct URL with ?post=<id> renders that post', async ({ page }) => {
    await page.goto('/blog.html?post=welcome-to-the-azure-update');
    await expect(page.locator('.post-full-title')).toHaveText('Welcome to The Azure Update');
    // Page title is updated for the single-post view
    await expect(page).toHaveTitle(/Welcome to The Azure Update/);
  });

  test('unknown ?post=<id> falls back to the post list', async ({ page }) => {
    await page.goto('/blog.html?post=does-not-exist');
    await expect(page.locator('.post-card').first()).toBeVisible();
  });

  test('nav links from blog page jump back to home anchors', async ({ page }) => {
    await page.goto('/blog.html');
    const aiLink = page.locator('.site-nav .nav-links a[href="index.html#ai"]');
    await expect(aiLink).toBeVisible();
    await aiLink.click();
    await expect(page).toHaveURL(/index\.html#ai$/);
    await expect(page.locator('#ai')).toBeVisible();
  });

  test('dark mode toggle persists across navigation to blog page', async ({ page }) => {
    await page.goto('/');
    await page.locator('#themeToggle').click();
    await expect(page.locator('html')).toHaveClass(/dark-mode/);

    await page.goto('/blog.html');
    await expect(page.locator('html')).toHaveClass(/dark-mode/);
  });

  test('home page Blog nav link points to blog.html', async ({ page }) => {
    await page.goto('/');
    const blogLink = page.locator('.site-nav .nav-links a[href="blog.html"]');
    await expect(blogLink).toBeVisible();
    await expect(blogLink).toHaveText('Blog');
  });

});
