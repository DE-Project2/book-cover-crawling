# 엑셀 파일에는 있는데 이미지는 크롤링되지 않은 책들 리스트 생성

import os
import pandas as pd

def find_excel_items_missing_images(field_code):
    field_code = field_code.zfill(2)
    image_dir = os.path.join("bestseller_images", field_code)
    excel_path = os.path.join("bestseller_meta", f"best_meta_{field_code}.xlsx")
    output_path = f"missing_images_{field_code}.txt"

    if not os.path.exists(image_dir):
        print(f"❗ 이미지 폴더 없음: {image_dir}")
        return
    if not os.path.exists(excel_path):
        print(f"❗ 엑셀 파일 없음: {excel_path}")
        return

    # 📸 이미지 파일 목록
    image_files = [f for f in os.listdir(image_dir) if f.endswith(".jpg")]
    image_ids = set(f.replace(".jpg", "") for f in image_files)

    # 📋 엑셀에서 book_id 추출
    df = pd.read_excel(excel_path)
    candidates = [col for col in df.columns if df[col].astype(str).str.contains("S000").any()]
    if not candidates:
        print(f"❗ 엑셀에서 book_id 컬럼을 찾을 수 없음: {excel_path}")
        return

    book_ids_in_excel = set(df[candidates[0]].astype(str).str.extract(r'(S\d{12})', expand=False).dropna())
    only_in_excel = sorted(book_ids_in_excel - image_ids)

    print(f"\n📊 [분류코드 {field_code}]")
    print(f" - 엑셀 수: {len(book_ids_in_excel)}")
    print(f" - 이미지 수: {len(image_ids)}")
    print(f" - 이미지가 없는 엑셀 항목 수: {len(only_in_excel)}")

    if only_in_excel:
        print(f"📁 누락된 book_id를 {output_path}로 저장합니다.")
        with open(output_path, "w", encoding="utf-8") as f:
            for bid in only_in_excel:
                f.write(bid + "\n")

# 실행
find_excel_items_missing_images("01")