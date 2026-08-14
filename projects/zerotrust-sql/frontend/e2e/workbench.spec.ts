import {expect, test} from '@playwright/test';

test('runs a safe query and records the allowed audit event', async ({page}) => {
  await page.goto('/app');
  await expect(page.getByRole('heading', {name: /Ask\. Inspect\./})).toBeVisible();
  await expect(page.getByText('Run a question to inspect generated SQL')).toBeVisible();

  await page.getByLabel('Business question').fill('Top 10 customers by revenue');
  await page.getByRole('button', {name: 'Generate + validate'}).click();

  await expect(page.locator('.verdict')).toContainText('ALLOWED');
  await expect(page.getByRole('heading', {name: 'Security report'})).toBeVisible();
  await expect(page.locator('.checks .fail')).toHaveCount(0);
  await expect(page.getByRole('table').first()).toContainText('revenue');
  await expect(page.getByRole('heading', {name: 'Recent audit events'})).toBeVisible();
  await expect(page.getByRole('table').last()).toContainText('allowed');
});

test('attack lab blocks hostile SQL before execution', async ({page}) => {
  await page.goto('/app');
  await page.getByRole('button', {name: /Read the decoy credentials table/}).click();

  await expect(page.locator('.verdict')).toContainText('BLOCKED');
  await expect(page.locator('.verdict')).toContainText('table_allowlist');
  await expect(page.locator('.checks .fail').first()).toContainText('table_allowlist');
  await expect(page.getByText('Query blocked before reaching the database.')).toBeVisible();
});

test('excessive result requests are bounded with a visible limit rewrite', async ({page}) => {
  await page.goto('/app');
  await page.getByRole('button', {name: /One million rows/}).click();

  await expect(page.locator('.verdict')).toContainText('ALLOWED');
  await expect(page.locator('.verdict mark')).toHaveText('LIMIT INJECTED');
  await expect(page.getByText(/LIMIT 100/).first()).toBeVisible();
});

test('mobile workbench keeps controls accessible without horizontal overflow', async ({page}) => {
  await page.setViewportSize({width: 375, height: 812});
  await page.goto('/app');

  await expect(page.getByLabel('Business question')).toBeVisible();
  await expect(page.getByRole('button', {name: 'Generate + validate'})).toBeVisible();
  await expect(page.getByRole('heading', {name: 'Attack lab'})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
