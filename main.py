import asyncio
import re
from playwright.async_api import async_playwright

BASE_URL = "https://www.thecsiaquill.com"
ALL_NEWS_URL = f"{BASE_URL}/all-news"

def slugify(title: str) -> str:
    # 소문자 변환
    title = title.lower()
    # '를 -로 변경
    title = title.replace("'", "-")
    # 공백과 특수문자 -> -
    title = re.sub(r"[^a-z0-9]+", "-", title)
    # 양쪽 - 제거
    title = title.strip("-")
    return title

async def scroll_to_bottom(page, step=500, delay=500):
    previous_height = await page.evaluate("document.body.scrollHeight")
    while True:
        await page.evaluate(f"window.scrollBy(0, {step});")
        await page.wait_for_timeout(delay)
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

async def get_all_titles(page):
    await page.goto(ALL_NEWS_URL)
    await page.wait_for_timeout(2000)

    await scroll_to_bottom(page)  # 페이지 끝까지 스크롤

    # 기사 컨테이너가 로드 대기
    await page.wait_for_selector('div[data-hook="item-container"]', timeout=15000)

    divs = await page.query_selector_all('div[data-hook="item-action"][aria-label]')
    titles = []
    for d in divs:
        title = await d.get_attribute("aria-label")
        if title:
            titles.append(title.strip())
    return list(set(titles))

async def get_article_view(page, url):
    await page.goto(url)
    try:
        # 7초 대기
        await page.wait_for_selector('span.FyJQDJ', timeout=7000)
    except Exception:
        return "조회수 없음"

    spans = await page.query_selector_all('span.FyJQDJ')
    for span in spans:
        text = (await span.inner_text()).strip().lower()
        if "view" in text:
            match = re.search(r"(\d+)\s*views", text)
            if match:
                return match.group(1)
    return "조회수 없음"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        titles = await get_all_titles(page)
        print(f"전체 기사 개수: {len(titles)}\n")

        for title in titles:
            slug = slugify(title)
            article_url = f"{BASE_URL}/post/{slug}"
            view_count = await get_article_view(page, article_url)
            print(f"제목: {title}")
            print(f"URL: {article_url}")
            print(f"조회수: {view_count}")
            print("-" * 40)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
