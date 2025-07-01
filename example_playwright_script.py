import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(record_video_dir="videos")
        # Start tracing
        await context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page = await context.new_page()

        # Step 1: Navigate to the Playwright website.
        await page.goto("https://playwright.dev/")

        # Step 2: Click on the search bar.
        await page.get_by_label("Search").click()

        # Step 3: Type "test" into the search bar.
        await page.get_by_placeholder("Search docs").fill("test")

        # Step 4: Press Enter to search.
        await page.get_by_placeholder("Search docs").press("Enter")

        # Step 5: Wait for the search results to load.
        await page.wait_for_timeout(3000)

        # Stop tracing
        await context.tracing.stop(path = "trace.zip")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
