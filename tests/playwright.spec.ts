import { test, expect } from '@playwright/test';

test('homepage loads with sidebar profile', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('h2');
  await expect(page.locator('#about h2')).toContainText('Werner Rall');
});

test('navigation links are present', async ({ page }) => {
  await page.goto('/');
  const nav = page.locator('.site-nav');
  await expect(nav.locator('.nav-links a')).toHaveCount(7);
  await expect(nav.locator('.nav-socials a')).toHaveCount(6);
});

test('dark mode toggle exists', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#themeToggle')).toBeVisible();
});

test('all sections are present', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#about')).toBeVisible();
  await expect(page.locator('#ai')).toBeVisible();
  await expect(page.locator('#quantum')).toBeVisible();
  await expect(page.locator('#blog')).toBeVisible();
  await expect(page.locator('#learning')).toBeVisible();
  await expect(page.locator('#azure')).toBeVisible();
  await expect(page.locator('#community')).toBeVisible();
  await expect(page.locator('.site-header')).toBeVisible();
});

test('disclaimer is present', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('.disclaimer-section')).toBeVisible();
});

test('content sections are ordered correctly (newer first)', async ({ page }) => {
  await page.goto('/');
  const sectionIds = await page.locator('.main-content section[id]').evaluateAll(els => els.map(el => el.id));
  const expected = ['ai', 'quantum', 'blog', 'learning', 'azure', 'community'];
  expect(sectionIds).toEqual(expected);
});

test('no legacy framework references', async ({ page }) => {
  await page.goto('/');
  const html = await page.content();
  expect(html).not.toContain('nicepage');
  expect(html).not.toContain('jquery');
  expect(html).toContain('site.css');
});

test('tile grid uses CSS grid layout', async ({ page }) => {
  await page.goto('/');
  const display = await page.locator('.tile-grid').first().evaluate(el => getComputedStyle(el).display);
  expect(display).toBe('grid');
});

test('header logo and sidebar layout are present', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('.header-logo')).toBeVisible();
  await expect(page.locator('.sidebar')).toBeVisible();
  await expect(page.locator('.sidebar-photo')).toBeVisible();
  await expect(page.locator('.page-layout')).toBeVisible();
});