import os
from google.cloud import storage
from google.oauth2 import service_account
from datetime import datetime

# 현재 파이썬 파일 기준 상대경로로 키 파일 경로 지정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(BASE_DIR, 'gcs_key.json')

# GCS 설정
GCS_BUCKET = 'de-project2-bucket-1'
GCS_PREFIX = 'kyobo'
LOCAL_IMAGE_DIR = os.path.join(BASE_DIR, 'images')
LOCAL_EXCEL_DIR = os.path.join(BASE_DIR, 'excel_data')

# 인증 객체 생성
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
client = storage.Client(credentials=credentials)

def upload_file_to_gcs(bucket_name, source_file_path, destination_blob_path):
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_path)
    blob.upload_from_filename(source_file_path)
    print(f"✅ 업로드 완료: {source_file_path} → gs://{bucket_name}/{destination_blob_path}")

def upload_directory_to_gcs(local_dir, gcs_prefix):
    for root, _, files in os.walk(local_dir):
        for file_name in files:
            local_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(local_path, local_dir)
            gcs_path = f"{gcs_prefix}/{relative_path.replace(os.sep, '/')}"
            upload_file_to_gcs(GCS_BUCKET, local_path, gcs_path)

def main():
    print("\n📂 이미지 업로드 시작")
    upload_directory_to_gcs(LOCAL_IMAGE_DIR, f"{GCS_PREFIX}/images")

    print("\n📂 엑셀 업로드 시작")
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    for file in os.listdir(LOCAL_EXCEL_DIR):
        if file.endswith(".xlsx"):
            local_path = os.path.join(LOCAL_EXCEL_DIR, file)
            gcs_path = f"{GCS_PREFIX}/excel/{file.replace('.xlsx', f'_{timestamp}.xlsx')}"
            upload_file_to_gcs(GCS_BUCKET, local_path, gcs_path)

    print("\n🎉 전체 업로드 완료!")

if __name__ == "__main__":
    main()
