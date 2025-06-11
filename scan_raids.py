import asyncio
import re
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)
import os
from dotenv import load_dotenv
import pandas as pd
import utils as u

glenn = {"csv": "raids_glenn.csv", "links": "links_glenn.txt"}
koma = {"csv": "raids_koma.csv", "links": "links_koma.txt"}
lia = {"csv": "raids.csv", "links":"links.txt"}

files = lia

cat_order = pd.CategoricalDtype(categories=['Open', 'Dead', 'Defeat', 'Unknown'], ordered=True)

async def run():

    async with async_playwright() as p:
        with open("updates.txt", "w", encoding="utf-8") as f:
            pass
        links = u.read_links(file_path=files["links"])
        df = pd.read_csv(files["csv"], index_col=None)

        # Add new links to the DataFrame if they're not already present
        for link in links:
            if link not in df["link"].values:
                new_row = {
                    "link": link,
                    "status": "Unknown",
                    "host": "Unknown",
                    "participants": pd.NA,
                    "spots": pd.NA,
                    "HP": pd.NA,
                    "HPperspot": pd.NA,
                    "time": pd.NA,
                    "days": pd.NA,
                }
                df = df._append(new_row, ignore_index=True)

        # leave out only the ongoing or unchecked raids for further processing 
        df2 = df[(df.status != "Dead") & (df.status != "Defeat")]
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir="auth_data",  # directory where cookies/storage will be saved
            headless=False,
        )
        page = await context.new_page()

        for index, row in df2.iterrows():
            await page.goto(row["link"])
            try:
                iframe = page.frame_locator("#portal_canvas_iframe")
                health = await u.find_health(iframe)

                if health == 0:
                    host = await u.handle_successful_raid(iframe)
                    df2.loc[index,["status","host"]]= ["Dead",host]

                else:
                    try:
                        time_left,days_left,host,participants,open_spots = await u.handle_ongoing_raid(iframe)
                        if open_spots > 0:
                            HP_per_spot = health / open_spots
                            df2.loc[
                                index,
                                [
                                    "status",
                                    "host",
                                    "participants",
                                    "spots",
                                    "HP",
                                    "HPperspot",
                                    "time",
                                    "days",
                                ],
                            ] = [
                                "Open",
                                host,
                                participants,
                                open_spots,
                                health,
                                HP_per_spot,
                                time_left,
                                days_left,
                            ]
                        else:
                            df2.loc[
                                index,
                                [
                                    "status",
                                    "host",
                                    "participants",
                                    "spots",
                                    "HP",
                                    "HPperspot",
                                    "time",
                                    "days",
                                ],
                            ] = [
                                "Full",
                                host,
                                participants,
                                30 - participants,
                                health,
                                None,
                                time_left,
                                days_left,
                            ]

                    except Exception as e:
                        # Fall back to visible timer text if script doesn't exist or fails
                        try:
                            host = await u.handle_defeated_raid(iframe)
                            df2.loc[index,["status","host"]]= ["Defeat",host]
                        except Exception as inner_e:
                            print("Couldn't extract timer from page at all.")
                            print(f"Error: {inner_e}")
            except Exception as e:
                print(f"[❌] Failed to process {link}: {e}")
        merged = pd.merge(df, df2, on="link", how="outer", suffixes=("_df", "_df2"))
        for column in df.columns:
            if column != "link":  # We don't overwrite the 'link' column
                merged[column] = merged[f"{column}_df2"].combine_first(
                    merged[f"{column}_df"]
                )

        # Step 3: Select the necessary columns, removing the suffixes
        merged = merged[df.columns]
        merged = merged.sort_values(by=['status', 'HPperspot'], ascending=[True, True])
        merged["spots"].astype("Int64")
        merged.to_csv(files["csv"], index=False)
        
        df2 = merged[merged["status"]=="Open"]
        df2=df2.sort_values(by="time", ascending=False)
        for index, row in df2.iterrows():
            with open("updates.txt", "a", encoding="utf-8") as f:
                text = f"{row["link"]} • {row["spots"]} slots • {row["HPperspot"]/1000000:.1f}M each • {row["time"]/3600:.1f} hours left"
                if row["HPperspot"]<1e7:
                    text = f"[⭐] {row["link"]} • {row["spots"]} slots • {row["HPperspot"]/1000000:.1f}M each • {row["time"]/3600:.1f} hours left"
                if row["time"]<7200:
                    text = f"[⚠️] {row["link"]} • {row["spots"]} slots • {row["HPperspot"]/1000000:.1f}M each • {row["time"]/3600:.1f} hours left"    
                if row["time"]<7200 and row["HPperspot"]<1e7:
                    text = f"[⚠️⭐] {row["link"]} • {row["spots"]} slots • {row["HPperspot"]/1000000:.1f}M each • {row["time"]/3600:.1f} hours left"
                f.write(text+"\n")
        await context.close()


asyncio.run(run())
