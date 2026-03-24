import { test, expect } from '@playwright/test';

test('homepage loads with about section', async ({ page }) => {
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
  await expect(page.locator('#carousel_7b63')).toBeVisible();
  await expect(page.locator('#carousel_ai_header')).toBeVisible();
  await expect(page.locator('#carousel_quantum_header')).toBeVisible();
  await expect(page.locator('#carousel_learn_header')).toBeVisible();
  await expect(page.locator('#carousel_blog_header')).toBeVisible();
  await expect(page.locator('#carousel_x_header')).toBeVisible();
});

test('disclaimer is present', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('.disclaimer-section')).toBeVisible();
});

test('sections are ordered correctly (newer first)', async ({ page }) => {
  await page.goto('/');
  const sectionIds = await page.locator('section[id]').evaluateAll(els => els.map(el => el.id));
  const expected = ['about', 'carousel_ai_header', 'carousel_ai_content', 'carousel_quantum_header', 'carousel_quantum_content', 'carousel_blog_header', 'carousel_blog_content', 'carousel_learn_header', 'carousel_learn_content', 'carousel_7b63', 'carousel_4585', 'carousel_x_header', 'carousel_x_content'];
  expect(sectionIds).toEqual(expected);
});