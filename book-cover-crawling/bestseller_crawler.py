import asyncio
import os
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def crawl_category(field_code, browser):
    print(f"\n===== 📚 분류 코드 {field_code} 크롤링 시작 =====")
    base_url = f"https://product.kyobobook.co.kr/category/KOR/{field_code}"

    # ✅ 폴더 생성 (분류코드별)
    image_dir = os.path.join("bestseller_images", field_code)
    excel_dir = "bestseller_meta"
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(excel_dir, exist_ok=True)

    context = await browser.new_context(accept_downloads=True)
    page = await context.new_page()

    try:
        # ✅ 1. 베스트셀러 탭 접속
        await page.goto(f"{base_url}#homeTabBest?page=1&type=best&per=50")
        await page.wait_for_timeout(4000)

        # ✅ 2. 엑셀 다운로드
        try:
            container = page.locator('#homeTabBest')
            button = container.locator('button.excel_down')
            await button.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)
            async with page.expect_download() as download_info:
                await button.click()
            download = await download_info.value
            save_path = os.path.join(excel_dir, f"best_meta_{field_code}.xlsx")
            await download.save_as(save_path)
            print(f"📥 엑셀 저장 완료: {save_path}")
        except Exception as e:
            print(f"[❗엑셀 다운로드 오류] {e}")

        # ✅ 3. 마지막 페이지 번호 추출
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        last_btn = soup.select_one('.btn_page_num[data-role="last"]')
        last_page = int(last_btn.text.strip()) if last_btn and last_btn.text.strip().isdigit() else 1
        print(f"🔎 전체 페이지 수: {last_page}")

        # ✅ 4. 이미지 크롤링
        for page_num in range(1, last_page + 1):
            print(f"▶ 페이지 {page_num} 이미지 크롤링 중...")
            await page.goto(f"{base_url}#homeTabBest?page={page_num}&type=best&per=50")
            await page.wait_for_timeout(4000)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select(".prod_item")

            for item in items:
                try:
                    link = item.find("a", class_="prod_link")
                    if not link:
                        continue
                    book_id = link["href"].split("/")[-1].strip()
                    img_tag = item.select_one(".img_box img")
                    img_url = img_tag.get("src") or img_tag.get("data-src") if img_tag else None
                    if img_url:
                        img_data = requests.get(img_url).content
                        with open(os.path.join(image_dir, f"{book_id}.jpg"), "wb") as f:
                            f.write(img_data)
                except Exception as e:
                    print(f"[❗ 이미지 저장 오류] {e}")
                    continue

    finally:
        await context.close()

async def main():
    with open("bestseller_field_list.txt", "r", encoding="utf-8") as f:
        field_codes = [line.strip() for line in f if line.strip()]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        for field_code in field_codes:
            await crawl_category(field_code, browser)
        await browser.close()

    print("\n🎉 전체 크롤링 완료!")

if __name__ == "__main__":
    asyncio.run(main())
