# 엑셀 파일에는 있는데 이미지는 크롤링되지 않은 책들만 다시 크롤링

import os
import requests
import asyncio
from playwright.async_api import async_playwright

async def download_image_from_detail(book_id, save_dir):
    url = f"https://product.kyobobook.co.kr/detail/{book_id}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url)
            await page.wait_for_timeout(2000)

            # 대표 이미지 태그 선택
            img_elem = await page.query_selector('div.blur_img_box img')
            img_url = await img_elem.get_attribute('src') if img_elem else None

            if img_url:
                img_data = requests.get(img_url).content
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, f"{book_id}.jpg")
                with open(save_path, "wb") as f:
                    f.write(img_data)
                print(f"✅ 저장 완료: {book_id}")
            else:
                print(f"❌ 이미지 태그 없음: {book_id}")

        except Exception as e:
            print(f"❗ 실패: {book_id} → {e}")
        finally:
            await browser.close()

async def recover_missing_images(field_code, id_file):
    save_dir = os.path.join("bestseller_images", field_code.zfill(2))

    with open(id_file, "r", encoding="utf-8") as f:
        book_ids = [line.strip() for line in f if line.strip()]

    for book_id in book_ids:
        await download_image_from_detail(book_id, save_dir)

# 실행 예시
if __name__ == "__main__":
    asyncio.run(recover_missing_images("01", "missing_images_01.txt"))
