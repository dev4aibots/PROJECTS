import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// Browser flows for CF-01. They prove interaction and accessibility of the explicit
// demo workbench only. They do NOT prove persistence, authorization or real AI.
const routes = ['/demo', '/demo/projects', '/demo/projects?view=board', '/demo/projects/new', '/demo/guide'];
const filterTabs = (page: Page) => page.getByRole('navigation', { name: 'Project status filters' });
const projectsNav = (page: Page) => page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: /^Projects/ });
const tableRows = (page: Page) => page.getByRole('table', { name: 'Projects in the sample agency workspace' }).locator('tbody tr');

test.describe('routing and shell', () => {
  test('root redirects to the explicit demo workbench', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/demo\/projects$/);
    await expect(page.getByRole('heading', { level: 1, name: 'Projects' })).toBeVisible();
    await expect(page.getByText('Sample workspace.', { exact: true })).toBeVisible();
  });
  test('unknown route shows the not-found boundary', async ({ page }) => {
    const response = await page.goto('/nowhere');
    expect(response?.status()).toBe(404);
    await expect(page.getByRole('heading', { level: 1, name: 'This page is not here.' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Open ClientFlow demo' })).toHaveAttribute('href', '/demo/projects');
  });
  test('missing project id shows an explicit not-found state', async ({ page }) => {
    await page.goto('/demo/projects/20000000-0000-4000-8000-000000000099');
    await expect(page.getByRole('heading', { level: 1, name: 'Project not found' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Back to projects' })).toBeVisible();
  });
});

test.describe('workbench filters', () => {
  test('search, status tabs and clear filters are URL driven', async ({ page }) => {
    await page.goto('/demo/projects');
    await expect(tableRows(page)).toHaveCount(8);
    await expect(projectsNav(page)).toContainText('8');

    await page.getByLabel('Search projects or clients').fill('coffee');
    await page.getByRole('button', { name: 'Search projects' }).click();
    await expect(page).toHaveURL(/q=coffee/);
    await expect(tableRows(page)).toHaveCount(2);
    await expect(page.getByText('Search: “coffee”')).toBeVisible();

    await filterTabs(page).getByRole('link', { name: /^In review/ }).click();
    await expect(page).toHaveURL(/status=review/);
    await expect(page).toHaveURL(/q=coffee/);
    await expect(page.getByRole('heading', { name: 'No projects found' })).toBeVisible();

    await page.getByRole('link', { name: 'Clear filters' }).first().click();
    await expect(page).toHaveURL(/\/demo\/projects$/);
    await expect(tableRows(page)).toHaveCount(8);
    await expect(filterTabs(page).getByRole('link', { name: /^All projects/ })).toHaveAttribute('aria-current', 'page');
  });
  test('attention filter shows only overdue open projects and links from metrics', async ({ page }) => {
    await page.goto('/demo');
    await page.getByRole('link', { name: /Needs attention/ }).click();
    await expect(page).toHaveURL(/attention=1/);
    await expect(page.getByText('Showing overdue projects')).toBeVisible();
    await expect(tableRows(page)).toHaveCount(1);
    await expect(tableRows(page).first()).toContainText('Customer portal');
    await expect(tableRows(page).first()).toContainText('Overdue');
  });
  test('unknown status and out-of-range page values degrade safely', async ({ page }) => {
    await page.goto('/demo/projects?status=deleted;drop&page=999');
    await expect(page.getByText('Unknown status ignored')).toBeVisible();
    await expect(tableRows(page)).toHaveCount(8);
    await expect(page.getByRole('navigation', { name: 'Pagination' })).toContainText('1 / 1');
    await expect(page.getByRole('navigation', { name: 'Pagination' }).getByRole('link', { name: 'Next' })).toHaveAttribute('aria-disabled', 'true');
  });
  test('board view changes status inline and every count follows the same data', async ({ page }) => {
    await page.goto('/demo/projects?view=board');
    await expect(page.getByRole('link', { name: 'Board view' })).toHaveAttribute('aria-current', 'page');
    const review = page.getByRole('region', { name: 'In review column' });
    const completed = page.getByRole('region', { name: 'Completed column' });
    await expect(review.getByRole('article')).toHaveCount(2);
    await expect(completed.getByRole('article')).toHaveCount(1);

    await page.getByLabel('Status for Autumn collection launch').selectOption('completed');
    await expect(page.getByRole('status').filter({ hasText: 'Autumn collection launch updated in this demo session.' })).toBeVisible();
    await expect(review.getByRole('article')).toHaveCount(1);
    await expect(completed.getByRole('article')).toHaveCount(2);
    await expect(filterTabs(page).getByRole('link', { name: /^In review/ })).toContainText('1');
    await expect(filterTabs(page).getByRole('link', { name: /^Completed/ })).toContainText('2');
    await expect(page.getByRole('link', { name: /^In review/ }).filter({ hasText: 'Ready for a second look' })).toContainText('01');
  });
});

test.describe('project create and edit', () => {
  test('rejects invalid input with focused, described field errors and keeps the draft', async ({ page }) => {
    await page.goto('/demo/projects/new');
    await page.locator('#field-description').fill('Draft brief that must survive validation.');
    await page.getByRole('button', { name: 'Create project' }).click();
    await expect(page.locator('#form-error')).toContainText('Check the highlighted fields.');
    const name = page.locator('#field-name');
    await expect(name).toBeFocused();
    await expect(name).toHaveAttribute('aria-invalid', 'true');
    await expect(name).toHaveAttribute('aria-describedby', 'error-name');
    await expect(page.locator('#error-name')).toHaveText('Enter a project name.');
    await expect(page.locator('#error-clientId')).toHaveText('Choose a valid client.');
    await expect(page.locator('#field-description')).toHaveValue('Draft brief that must survive validation.');
    await expect(page).toHaveURL(/\/demo\/projects\/new$/);
  });
  test('creates a project that appears in the list, counts and deadline rail, then edits it', async ({ page }) => {
    await page.goto('/demo/projects/new');
    await page.locator('#field-name').fill('Loyalty app pilot');
    await page.locator('#field-clientId').selectOption({ label: 'Fieldwork Coffee' });
    await page.locator('#field-status').selectOption('active');
    await page.locator('#field-dueDate').fill('2026-09-10');
    await page.getByRole('button', { name: 'Create project' }).click();

    await expect(page).toHaveURL(/\/demo\/projects$/);
    await expect(page.getByRole('status').filter({ hasText: 'Loyalty app pilot created in this demo session.' })).toBeVisible();
    await expect(tableRows(page)).toHaveCount(9);
    await expect(tableRows(page).first()).toContainText('Loyalty app pilot');
    await expect(projectsNav(page)).toContainText('9');
    await expect(page.getByRole('complementary', { name: 'Upcoming deadlines' })).toContainText('Loyalty app pilot');
    await expect(page.getByRole('link', { name: /^In progress/ }).filter({ hasText: 'Projects in motion' })).toContainText('04');

    await tableRows(page).first().getByRole('link', { name: 'Loyalty app pilot' }).click();
    await expect(page.getByRole('heading', { level: 1, name: 'Edit project' })).toBeVisible();
    await expect(page.getByText('Editing version 1.')).toBeVisible();
    await page.locator('#field-name').fill('Loyalty app pilot — phase 2');
    await page.locator('#field-status').selectOption('completed');
    await page.getByRole('button', { name: 'Save changes' }).click();
    await expect(page).toHaveURL(/\/demo\/projects$/);
    await expect(tableRows(page).first()).toContainText('Loyalty app pilot — phase 2');
    await expect(tableRows(page).first()).toContainText('Completed');
    await expect(filterTabs(page).getByRole('link', { name: /^Completed/ })).toContainText('2');
  });
  test('reload resets the in-memory sample data as documented', async ({ page }) => {
    await page.goto('/demo/projects?view=board');
    await page.getByLabel('Status for Design system foundations').selectOption('archived');
    await expect(page.getByRole('region', { name: 'Archived column' }).getByRole('article')).toHaveCount(2);
    await page.reload();
    await expect(page.getByRole('region', { name: 'Archived column' }).getByRole('article')).toHaveCount(1);
    await expect(page.getByRole('region', { name: 'Planned column' })).toContainText('Design system foundations');
  });
});

test.describe('accessibility', () => {
  for (const path of routes) {
    test(`axe: no serious or critical violations on ${path}`, async ({ page }) => {
      await page.goto(path);
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
      const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
      const blocking = results.violations.filter(v => v.impact === 'serious' || v.impact === 'critical');
      expect(blocking.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.map(n => n.target.join(' ')) }))).toEqual([]);
    });
  }
  test('skip link moves focus to main content', async ({ page }) => {
    await page.goto('/demo/projects');
    await page.keyboard.press('Tab');
    await expect(page.getByRole('link', { name: 'Skip to main content' })).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.locator('#main-content')).toBeFocused();
  });
});
