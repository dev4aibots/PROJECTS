import {expect, test} from '@playwright/test';

test('allows a clean prompt and updates privacy-safe telemetry', async ({page}) => {
  await page.goto('/app');
  await expect(page.getByText('Choose a demo or send a prompt')).toBeVisible();

  await page.getByLabel('Prompt').fill('Explain retrieval augmented generation.');
  await page.getByRole('button', {name: 'Send through gateway'}).click();

  await expect(page.getByRole('heading', {name: 'safe'})).toBeVisible();
  await expect(page.getByText('Safely processed: Explain retrieval augmented generation.')).toBeVisible();
  await expect(page.locator('.check.BLOCK')).toHaveCount(0);
  await expect(page.getByRole('heading', {name: 'Privacy-safe history'})).toBeVisible();
  await expect(page.getByRole('table')).toContainText('safe');
});

test('blocks a multi-family injection before provider execution', async ({page}) => {
  await page.goto('/app');
  await page.getByRole('button', {name: 'Injection attack'}).click();

  await expect(page.getByRole('heading', {name: 'blocked'})).toBeVisible();
  await expect(page.getByText('No answer was released.')).toBeVisible();
  await expect(page.locator('.check.BLOCK')).toContainText('injection');
  await expect(page.getByText(/provider none/)).toBeVisible();
});

test('redacts PII and visibly reports the warning', async ({page}) => {
  await page.goto('/app');
  await page.getByLabel('Prompt').fill('Contact alex@example.com about the report.');
  await page.getByRole('button', {name: 'Send through gateway'}).click();

  await expect(page.getByRole('heading', {name: 'warned'})).toBeVisible();
  await expect(page.getByText('Safely processed: Contact [REDACTED:email] about the report.')).toBeVisible();
  await expect(page.locator('.check.WARN').first()).toContainText('pii_input');
  await expect(page.locator('.result')).not.toContainText('alex@example.com');
});

test('shows a controlled error when the gateway cannot be reached', async ({page}) => {
  await page.route('**/api/gateway', (route) => route.abort());
  await page.goto('/app');
  await page.getByRole('button', {name: 'Send through gateway'}).click();

  await expect(page.getByRole('alert')).toContainText('could not be completed');
});

test('keeps controls accessible without mobile horizontal overflow', async ({page}) => {
  await page.setViewportSize({width: 375, height: 812});
  await page.goto('/app');

  await expect(page.getByLabel('Gateway token')).toBeVisible();
  await expect(page.getByLabel('Prompt')).toBeVisible();
  await expect(page.getByRole('button', {name: 'Send through gateway'})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
