import re
import asyncio
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

RAID_URL_PATTERN = re.compile(
    r"https?://www\.kanoplay\.com/la_cosa_nostra/boss/raid/[a-z0-9]+\?game_server=server_2"
)
LINKS_FILE = "links.txt"


async def append_links(links):
    with open(LINKS_FILE, "a") as f:
        for link in links:
            f.write(link + "\n")


async def extract_links_from_chat_box(page):
    return await page.eval_on_selector_all(
        "#chat-msgs-box a",
        """elements => elements
            .map(el => el.href)
            .filter(href => href.includes("kanoplay.com/la_cosa_nostra/boss/raid/"))
        """,
    )


async def run():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="auth_data",
            headless=False,
        )

        page = await context.new_page()
        await page.goto("https://www.kanoplay.com/la_cosa_nostra/?game_server=server_2")
        await page.wait_for_timeout(5000)  # Wait for iframe to load

        iframe = page.frame_locator("#portal_canvas_iframe")
        chat_selector = "#chat_pane"

        # Wait for chat pane to appear
        await iframe.locator(chat_selector).wait_for(timeout=10000)

        # Extract and store initial links
        links = await extract_links_from_chat_box(iframe)
        if links:
            await append_links(links)
            print(f"Initial links found: {len(links)}")

        # Monitor for new messages with MutationObserver
        await iframe.evaluate(
            """() => {
                const target = document.querySelector('#chat-msgs-box');
                const observer = new MutationObserver(mutations => {
                    for (const mutation of mutations) {
                        for (const node of mutation.addedNodes) {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                const links = node.querySelectorAll('a');
                                for (const a of links) {
                                    if (/https?:\\/\\/www\\.kanoplay\\.com\\/la_cosa_nostra\\/boss\\/raid\\/.+/.test(a.href)) {
                                        window.dispatchEvent(new CustomEvent("raid-link-found", {
                                            detail: { link: a.href }
                                        }));
                                    }
                                }
                            }
                        }
                    }
                });

                observer.observe(target, { childList: true, subtree: true });
            }
            """
        )

        # Hook into custom raid link event and pipe to Python
        async def handle_raid_link(msg):
            link = msg["detail"]["link"]
            print("New raid link:", link)
            await append_links([link])

        async def listen_for_raid_links():
            async with iframe.expect_event("websocket") as ws_info:
                websocket = (
                    await ws_info.value
                )  # Just ensure any websockets are captured
            await iframe.expose_binding(
                "handleRaidLink",
                lambda _, msg: asyncio.create_task(handle_raid_link(msg)),
            )

            await iframe.evaluate(
                """() => {
                    window.addEventListener("raid-link-found", (event) => {
                        window.handleRaidLink(event);
                    });
                }
                """
            )

        await listen_for_raid_links()

        print("Listening for new raid links... Press Ctrl+C to exit.")
        while True:
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(run())
