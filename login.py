import asyncio
import re
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)
import os
from dotenv import load_dotenv


async def run():
    load_dotenv()

    email = os.getenv("KANO_EMAIL")
    password = os.getenv("KANO_PASSWORD")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="auth_data",  # directory where cookies/storage will be saved
            headless=False,
        )
        page = await context.new_page()

        # STEP 1: Login
        await page.goto(
            "https://www.kanoplay.com/la_cosa_nostra/?kpv=login&game_name=la_cosa_nostra"
        )
        await page.wait_for_selector("input[name='email']", timeout=15000)

        await page.fill("input[name='email']", email)
        await page.fill("input[name='password']", password)
        await page.check("#login_remember_check")

        await page.evaluate(
            """() => {
            rememberPass();
            return ajax({
                page: 'account/login',
                data: 'kpv=play&game_name=la_cosa_nostra',
                form_id: 'login_form',
                update_id: 'login_response_container'
            });
        }"""
        )
        await page.wait_for_url("**/la_cosa_nostra/**")
        await page.goto("https://www.kanoplay.com/la_cosa_nostra/")
        await asyncio.sleep(30)
        await context.close()


asyncio.run(run())
