import time
import requests
import base64
import openai
from datetime import datetime


# Google Cloud Vision API 엔드포인트
vision_url = "https://vision.googleapis.com/v1/images:annotate"

# Google Cloud Vision API 키
vision_api_key = ""  # 여기에 실제 API 키를 입력하세요

# OpenAI API 키 설정
openai.api_key = ''  # 여기에 실제 OpenAI API 키를 입력하세요

# 이미지 파일 경로
image_path = r'D:\2024신한해커톤\영수증 처리 프로젝트\test\example.jpg'

# 이미지 파일을 읽어서 Base64로 인코딩
with open(image_path, "rb") as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode()

# Google Cloud Vision API 요청 페이로드 생성
payload = {
    "requests": [
        {
            "image": {
                "content": encoded_image
            },
            "features": [
                {
                    "type": "TEXT_DETECTION"
                }
            ]
        }
    ]
}

# Google Cloud Vision API 요청 보내기
response = requests.post(vision_url, json=payload, params={"key": vision_api_key})

# 결과 처리 및 텍스트 추출
if response.status_code == 200:
    result = response.json()
    if 'textAnnotations' in result['responses'][0]:
        ocr_text = result['responses'][0]['textAnnotations'][0]['description']
        print("OCR로 추출된 텍스트:")
        print(ocr_text)
    else:
        print("텍스트를 인식하지 못했습니다.")
        ocr_text = ""
else:
    print(f"Error: {response.status_code}")
    print(response.text)
    ocr_text = ""

# OCR로 추출한 텍스트를 GPT-4 모델에 전달하여 분석
if ocr_text:
    def process_receipt_text(receipt_text):
        # GPT-4 모델에 입력할 프롬프트
        prompt = f"""
        다음은 영수증에서 OCR을 통해 추출된 텍스트입니다:

        텍스트: "{receipt_text}"

        1. 이 텍스트에서 결제 시간을 찾아서 'YYYY-MM-DD HH:MM' 형식으로 반환하세요.
        2. 결제 시 텀블러를 사용해 절약했는지 여부를 확인하세요. "텀블러 할인" 또는 "할인 없음"으로만 대답하세요.

        답변 형식:
        결제 시간: YYYY-MM-DD HH:MM
        텀블러 사용: 텀블러 할인 / 할인 없음
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
            ],
                max_tokens=100,
                temperature=0.2,
            )
            return response['choices'][0]['message']['content'].strip()

        except openai.error.RateLimitError:
            print("Rate limit exceeded. Retrying after a short delay...")
            time.sleep(60)  # 60초 대기 후 재시도
            return process_receipt_text(receipt_text)

    # GPT-4 함수 호출
    gpt_result = process_receipt_text(ocr_text)    
    
print(gpt_result)
print("=====================================")

# GPT가 반환한 결과

# 결제 시간과 현재 시간 비교
payment_time_str = gpt_result.split("결제 시간: ")[1].split("\n")[0]
payment_time = datetime.strptime(payment_time_str, "%Y-%m-%d %H:%M")
current_time = datetime.now()

# 24시간 이내인지 확인
time_difference = current_time - payment_time
if time_difference.total_seconds() < 24 * 3600:
    within_24_hours = True
else:
    within_24_hours = False

# 텀블러 사용 여부 확인
tumbler_used = "텀블러" in gpt_result or "컵" in gpt_result

# 최종 판단
if within_24_hours and tumbler_used:
    result = "조건 만족: 리워드 제공"
elif not within_24_hours  :
    result = "조건 불충족: 24시간 지남."
else :
    result = "조건 불충족: 텀블러 관련 키워드 없음."

print(result)
