# 교보문고에서 가장 작은 분류 단위로 크롤링 돌림
# 분류에 해당하는 field code를 field_list.txt에서 수정 후 파일 실행시킬 것

'''
Playwright 기반 교보문고 전체 페이지 이미지 + 엑셀 크롤러

실행 전 설치:
pip install playwright requests beautifulsoup4
playwright install
'''

import asyncio
import os
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def crawl_category(field_code, browser, download_dir):
    print(f"\n===== 분류 코드 {field_code} 크롤링 시작 =====")
    base_url = f"https://product.kyobobook.co.kr/category/KOR/{field_code}#?page={{page}}&type=all&per=50&sort=sel"

    # 폴더 생성
    image_dir = f"images/{field_code}"
    os.makedirs(image_dir, exist_ok=True)

    # Playwright 브라우저 컨텍스트 설정 (엑셀 다운로드 허용)
    context = await browser.new_context(accept_downloads=True)
    page = await context.new_page()

    # 1. 첫 페이지 접속
    await page.goto(base_url.format(page=1))
    await page.wait_for_timeout(3000)

    # 2. 엑셀 다운로드
    try:
        async with page.expect_download() as download_info:
            await page.click('button:has-text("Excel다운로드")')
        download = await download_info.value
        save_path = os.path.join(download_dir, f"meta_{field_code}.xlsx")
        await download.save_as(save_path)
        print(f"엑셀 저장 완료: {save_path}")
    except Exception as e:
        print(f"[엑셀 다운로드 오류] {e}")

    # 3. 마지막 페이지 번호 추출
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    last_btn = soup.select_one('.btn_page_num[data-role="last"]')
    if last_btn and last_btn.text.strip().isdigit():
        last_page = int(last_btn.text.strip())
    else:
        last_page = 1
    print(f"전체 페이지 수: {last_page}")

    # 4. 전체 페이지 순회하며 이미지 다운로드
    for page_num in range(1, last_page + 1):
        print(f"페이지 {page_num} 이미지 크롤링 중...")
        await page.goto(base_url.format(page=page_num))
        await page.wait_for_timeout(5000)

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
                if img_tag:
                    img_url = img_tag.get("src") or img_tag.get("data-src")
                    if img_url:
                        img_data = requests.get(img_url).content
                        with open(f"{image_dir}/{book_id}.jpg", "wb") as f:
                            f.write(img_data)
            except Exception as e:
                print(f"[이미지 저장 오류] {e}")
                continue

    await context.close()

async def main():
    # 폴더 생성
    os.makedirs("images", exist_ok=True)
    os.makedirs("excel_data", exist_ok=True)

    # 분류코드 목록 로딩
    with open("field_list.txt", "r", encoding="utf-8") as f:
        field_codes = [line.strip() for line in f if line.strip()]

    # 브라우저 실행
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        for field_code in field_codes:
            await crawl_category(field_code, browser, "excel_data")
        await browser.close()

    print("\n전체 작업 완료!")

# 실행
asyncio.run(main())

