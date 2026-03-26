import { expect, test } from '@playwright/test'

test('home page loads', async ({ page }) => {
  await page.goto('/')

  await expect(page.locator('main').getByText('Routine Cloud', { exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Learn more' })).toBeVisible()
})
