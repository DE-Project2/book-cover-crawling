import os
import io
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.cluster import DBSCAN
from io import BytesIO
import requests
from tqdm import tqdm
from google.cloud import storage
import colorsys
from concurrent.futures import ThreadPoolExecutor, as_completed

# === GCS 인증 설정 ===
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "valid-might-460212-k2-aa639e904de6.json"

# === GCS에서 CSV 불러오기 ===
client = storage.Client()
bucket = client.bucket("de-project2-bucket-1")
csv_blob = bucket.blob("kyobo/csv/combined/after_preprocessing_novel.csv")
csv_data = csv_blob.download_as_text()
df = pd.read_csv(io.StringIO(csv_data))

# === 이미지 URL 리스트 ===
image_urls = df['image_url'].tolist()

# === 출력 폴더 설정 ===
output_folder = 'C:/Users/User/PycharmProjects/PythonProject/color_extraction_csv'
os.makedirs(output_folder, exist_ok=True)

# === 색상 추출 관련 함수 ===
def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def extract_colors_with_dbscan(img, eps=16, min_samples=10):
    img = img.convert('RGB')
    img.thumbnail((100, 100))
    pixels = np.array(img).reshape(-1, 3)
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(pixels)
    labels = db.labels_

    colors, counts = [], []
    for label in np.unique(labels):
        if label == -1:
            continue
        cluster_pixels = pixels[labels == label]
        mean_rgb = cluster_pixels.mean(axis=0)
        colors.append(mean_rgb)
        counts.append(len(cluster_pixels))

    return np.array(colors), np.array(counts), len(pixels)

def hex_to_hsl(hex_color):
    try:
        hex_color = hex_color.strip().lstrip('#')
        if len(hex_color) != 6:
            return '', '', ''
        r, g, b = [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return round(h * 360, 2), round(s * 100, 2), round(l * 100, 2)
    except Exception:
        return '', '', ''

def hsl_to_color_name(h, s, l):
    if h == '' or s == '' or l == '':
        return ''

    if s <= 5:
        if l >= 85:
            return '흰색 계열'
        elif l <= 35:
            return '검정색 계열'
        else:
            return '회색 계열'

    if 0 <= h < 15 or h >= 345:
        base = 'red'
    elif 15 <= h < 45:
        base = 'orange'
    elif 45 <= h < 70:
        base = 'yellow'
    elif 70 <= h < 160:
        base = 'green'
    elif 160 <= h < 200:
        base = 'cyan'
    elif 200 <= h < 250:
        base = 'blue'
    elif 250 <= h < 290:
        base = 'navy'
    elif 290 <= h < 345:
        base = 'purple'
    else:
        base = 'etc'

    if l >= 65:
        return f'pastel_{base}'
    else:
        return f'basic_{base}'

# === 개별 이미지 처리 함수 (병렬 처리용) ===
def process_image(idx_url_pair):
    idx, url = idx_url_pair
    try:
        if not url or pd.isna(url):
            return idx, []

        response = requests.get(url, timeout=10)
        image = Image.open(BytesIO(response.content))
        colors, counts, total_pixels = extract_colors_with_dbscan(image)

        if len(colors) == 0:
            return idx, []

        sorted_indices = np.argsort(-counts)
        colors = colors[sorted_indices]
        counts = counts[sorted_indices]

        hex_colors = [rgb_to_hex(c) for c in colors]
        ratios = [round((cnt / total_pixels) * 100, 1) for cnt in counts]

        row_data = []
        for c, r in zip(hex_colors, ratios):
            h, s, l = hex_to_hsl(c)
            color_name = hsl_to_color_name(h, s, l)
            row_data.extend([c, color_name, r, h, s, l])

        return idx, row_data

    except Exception as e:
        print(f"[{idx + 2}행] 에러 발생: {e}")
        return idx, []

# === 병렬 처리 실행 ===
max_color_count = 0
all_rows = [None] * len(image_urls)

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(process_image, (i, url)) for i, url in enumerate(image_urls)]
    for future in tqdm(as_completed(futures), total=len(futures), desc="병렬 처리 중"):
        idx, row = future.result()
        all_rows[idx] = row
        if row:
            max_color_count = max(max_color_count, len(row) // 6)

# === 컬럼 수 맞추기 ===
for row in all_rows:
    while len(row) < max_color_count * 6:
        row.extend([''] * 6)

# === 결과 DataFrame 생성 ===
columns = []
for i in range(1, max_color_count + 1):
    columns.extend([
        f'HEX{i}', f'color{i}', f'비율{i}', f'H{i}(각도)', f'S{i}(%)', f'L{i}(%)'
    ])
result_df = pd.DataFrame(all_rows, columns=columns)

# === product_id 추가 ===
result_df.insert(0, 'product_id', df['product_id'])

# === CSV 저장 ===
final_path = os.path.join(output_folder, 'color_novel.csv')
result_df.to_csv(final_path, index=False)
print(f"✅ 최종 색상 정보가 '{final_path}'에 저장되었습니다!")
