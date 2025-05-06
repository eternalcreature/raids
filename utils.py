import re
from urllib.parse import urlparse
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


def strip_url(url):
    match = re.search(r"/([^/?]+)(?:\?|$)", url)
    if match:
        return match.group(1)
    return None


async def find_health(iframe):
    health_text_locator = iframe.locator(".boss-image-box .progress-bar-inner-text")
    health = extract_current_health(await health_text_locator.inner_text())
    return health


async def handle_successful_raid(iframe):
    host = await iframe.locator("div.raid-boss-hd span").nth(0).inner_text()
    print(f"Processed successful raid hosted by {host}.")
    return host.split("'")[0]


async def handle_ongoing_raid(iframe):
    time_container = iframe.locator("div.boss-time-rem")
    time_content = await time_container.locator("script").text_content()

    match = re.search(r'secondCountDownTimer\("(\d+)"', time_content)
    time_left = int(match.group(1))
    days_left = seconds_to_dhms(time_left)
    host_locator = iframe.locator("span.boss-world-header")
    host = await host_locator.inner_text()

    participants_locator = iframe.locator(
        ".boss-table-more td", has_text="Participants"
    ).locator("span")

    participants_text = await participants_locator.inner_text()
    participants = int(participants_text.replace(",", "").strip())
    open_spots = 30 - participants
    print(f"Processed ongoing raid hosted by {host}.")
    return time_left, days_left, host, participants, open_spots


async def handle_defeated_raid(iframe):
    time_container = iframe.locator("div.boss-time-rem span#boss_time_left")
    visible_timer = await time_container.inner_text()
    host_locator = iframe.locator("span.boss-world-header")
    host = await host_locator.inner_text()
    print(f"Processed defeated raid hosted by {host}.")
    return host


def extract_current_health(text):
    """Extract the number before the slash in a health string."""
    match = re.search(r"([0-9,]+)\s*/", text)
    if match:
        # Remove commas and convert to integer
        return int(match.group(1).replace(",", ""))
    return None


def seconds_to_dhms(seconds):
    seconds = int(float(seconds))  # in case it's a float string like "78060.8600"
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{days}:{hours:02}:{minutes:02}:{secs:02}"


def is_valid_url(url):
    """Check if a string is a valid URL."""
    parsed = urlparse(url)
    return all([parsed.scheme in ("http", "https"), parsed.netloc])


def read_links(file_path="links.txt"):
    """Read valid, unique URLs from a file, preserving order."""
    seen = set()
    links = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            link = line.strip()
            urlcode = strip_url(link)
            if urlcode not in seen:
                seen.add(link)
                links.append(
                    "https://www.kanoplay.com/la_cosa_nostra/boss/raid/" + urlcode
                )
    return links
