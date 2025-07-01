import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(record_video_dir="videos")
        await context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = await context.new_page()

        # Step 1: Navigate to the Playwright website and perform a search.
        await page.goto("https://playwright.dev/")
        await page.get_by_label("Search").click()
        await page.get_by_placeholder("Search docs").fill("test")
        await page.get_by_placeholder("Search docs").press("Enter")

        # Step 2: Wait for the search results to load and finish the session.
        await page.wait_for_timeout(3000)

        await context.tracing.stop(path = "trace.zip")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())