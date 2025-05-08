# 교보문고에서 가장 작은 분류 단위로 크롤링 돌림
# 분류에 해당하는 field code를 field_list.txt에서 수정 후 파일 실행시킬 것

'''
pip install selenium
pip install chromedriver
pip install beautifulsoup4
pip install chromedriver_autoinstaller
pip install requests pillow

먼저 터미널 또는 아나콘다 프롬프트 또는 둘 다에 설치해주세요.
'''

from selenium import webdriver
from chromedriver_autoinstaller import install as install_chromedriver
from bs4 import BeautifulSoup
import time
import pandas as pd
import os
import requests

# 크롬 드라이버 설치 및 실행
install_chromedriver()
driver = webdriver.Chrome()

# 폴더 생성
os.makedirs('images', exist_ok=True)
os.makedirs('meta_data', exist_ok=True)

# 분류 코드 리스트 로딩
with open("field_list.txt", "r", encoding="utf-8") as f:
    field_codes = [line.strip() for line in f if line.strip()]

# 각 분류 코드에 대해 크롤링
for field_code in field_codes:
    print(f"\n===== 📚 분류 코드 {field_code} 크롤링 시작 =====")
    base_url = f"https://product.kyobobook.co.kr/category/KOR/{field_code}#?page={{page}}&type=all&per=50&sort=new"

    # 첫 페이지 로딩
    driver.get(base_url.format(page=1))
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # 마지막 페이지 번호 추출
    last_btn = soup.select_one('.btn_page_num[data-role="last"]')
    if last_btn and last_btn.text.strip().isdigit():
        last_page = int(last_btn.text.strip())
    else:
        last_page = 1
    print(f"🔎 총 페이지 수: {last_page}")

    # 이미지 폴더 생성 (분류별)
    image_dir = f'images/{field_code}'
    os.makedirs(image_dir, exist_ok=True)

    # 데이터 수집
    data = []

    for page in range(1, last_page + 1):
        print(f"▶ 페이지 {page} 크롤링 중...")
        driver.get(base_url.format(page=page))
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        items = soup.select('.prod_item')

        for item in items:
            try:
                link_number = item.find('a', class_="prod_link")['href'].split("/")[-1].strip()
                title = item.find('span', class_="prod_name").get_text(strip=True)
                labels = item.find('span', class_="prod_label")
                if labels:
                    for label in labels:
                        title = title.replace(label.text.strip(), '')

                author_tag = item.find('span', class_="prod_author")
                if author_tag:
                    author_link = author_tag.find('a')
                    author = author_link.text.strip() if author_link else author_tag.text.strip()
                    if not author:
                        author = ""
                else:
                    author = ""

                raw_intro = item.select_one('.prod_introduction')
                if raw_intro:
                    intro_clean = raw_intro.text.strip().replace('\n', ' ').replace('\r', ' ')
                    intro_truncated = (intro_clean[:100] + '...') if len(intro_clean) > 100 else intro_clean
                else:
                    intro_truncated = ""

                review_tag = item.select_one('.review_klover_text')
                review = float(review_tag.text.strip()) if review_tag else None

                # 이미지 저장
                img_tag = item.select_one('.img_box img')
                if img_tag:
                    img_url = img_tag.get('src') or img_tag.get('data-src')
                    if img_url:
                        img_data = requests.get(img_url).content
                        with open(f'{image_dir}/{link_number}.jpg', 'wb') as f:
                            f.write(img_data)

                # 데이터 저장
                data.append((link_number, title, author, intro_truncated, review))

            except Exception as e:
                print(f"[❗오류] {e}")
                continue

    # 분류별 CSV 저장
    df = pd.DataFrame(data, columns=['Num', 'Title', 'Author', 'Introduction', 'Review'])
    df.to_csv(f'meta_data/books_{field_code}.csv', index=False, encoding='utf-8-sig')
    print(f"✅ 저장 완료: meta_data/books_{field_code}.csv")

driver.quit()
print("🎉 전체 크롤링 완료")
