import { expect, test } from '@playwright/test';

test('create, interrupt, approve, refresh, and manage memory', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Start a governed run' })).toBeVisible();
  await expect(page.getByText('No runs for this identity yet.')).toBeVisible();

  await page.getByLabel('Research task').fill('Analyze sensitive financial risk and summarize the evidence');
  await page.getByLabel(/Save one explicit preference memory/).check();
  await page.getByRole('button', { name: /Start graph/ }).click();

  await expect(page.getByText('Human approval required')).toBeVisible();
  await expect(page.getByText('financial domain')).toBeVisible();
  await expect(page.getByRole('link', { name: /Deterministic research fixture/ })).toBeVisible();

  await page.getByRole('button', { name: 'Approve & resume' }).click();
  await expect(page.getByText('Final deliverable')).toBeVisible();
  await expect(page.locator('.status')).toHaveText('completed');

  await page.reload();
  await expect(page.locator('.status')).toHaveText('completed');
  await expect(page.getByText('Final deliverable')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Memory manager' })).toBeVisible();
  await expect(page.getByText(/Past task: Research brief/)).toBeVisible();

  await page.getByRole('button', { name: 'Delete' }).click();
  await expect(page.getByText(/No saved memories/)).toBeVisible();
});

test('cancel is owner-visible and terminal', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Research task').fill('Analyze legal risk before publishing this policy');
  await page.getByRole('button', { name: /Start graph/ }).click();
  await expect(page.getByText('Human approval required')).toBeVisible();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.locator('.status')).toHaveText('canceled');
  await expect(page.getByRole('button', { name: 'Approve & resume' })).toHaveCount(0);
});

test('reject ends the run without executing the writer', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Research task').fill('Assess medical risk before publishing this advice');
  await page.getByRole('button', { name: /Start graph/ }).click();
  await expect(page.getByText('Human approval required')).toBeVisible();
  await page.getByRole('button', { name: 'Reject' }).click();
  await expect(page.locator('.status')).toHaveText('rejected');
  await expect(page.getByText('Final deliverable')).toHaveCount(0);
  await expect(page.locator('.timeline li').filter({ hasText: 'writer' })).toHaveCount(0);
});

test('mobile workspace keeps primary controls accessible without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Start a governed run' })).toBeVisible();
  await expect(page.getByLabel('Research task')).toBeVisible();
  await expect(page.getByRole('button', { name: /Start graph/ })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Memory manager' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
