from flask import Flask
from flask import request
import time
import requests
import base64
import openai
from datetime import datetime

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
from PIL import Image

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/receipt", methods=['POST'])
def receipt():
    requestImg =  request.files["file"]

    # Google Cloud Vision API 엔드포인트
    vision_url = "https://vision.googleapis.com/v1/images:annotate"

    # Google Cloud Vision API 키
    vision_api_key = "AIzaSyCEv0_bOGZu2g7y9vAN-tibfGOMaJWO__c"  # 여기에 실제 API 키를 입력하세요

    # OpenAI API 키 설정
    openai.api_key = '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'  # 여기에 실제 OpenAI API 키를 입력하세요

    encoded_image = base64.b64encode(requestImg.read()).decode()

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

    gpt_result = ""
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

            except openai.error.OpenAIError as e:
                print(f"OpenAI API Error: {e}")
                time.sleep(60)  # 60초 대기 후 재시도
                return process_receipt_text(receipt_text)

        # GPT-4 함수 호출
        gpt_result = process_receipt_text(ocr_text)

    print(gpt_result)
    print("=====================================")

    # GPT가 반환한 결과에서 결제 시간 추출 및 예외 처리
    if "결제 시간: " in gpt_result:
        payment_time_str = gpt_result.split("결제 시간: ")[1].split("\n")[0]
        try:
            payment_time = datetime.strptime(payment_time_str, "%Y-%m-%d %H:%M")
            current_time = datetime.now()

            # 24시간 이내인지 확인
            time_difference = current_time - payment_time
            if time_difference.total_seconds() < 24 * 3600:
                within_24_hours = True
            else:
                within_24_hours = False
        except ValueError:
            print("날짜 형식이 잘못되었습니다.")
            within_24_hours = False
    else:
        print("결제 시간 정보가 텍스트에 없습니다.")
        within_24_hours = False

    # 텀블러 사용 여부 확인
    tumbler_used = "텀블러" in gpt_result or "컵" in gpt_result

    # 최종 판단
    if within_24_hours and tumbler_used:
        # 조건 만족: 리워드 제공
        return "1"
    elif not within_24_hours:
        # 조건 불충족: 24시간 지남.
        return "0"
    # 조건 불충족: 텀블러 관련 키워드 없음.
    return "-1"



@app.route("/food", methods=['POST'])
def food():

    def predict_image(model_path):
        # 모델 불러오기
        model = load_model(model_path, compile=False)

        # 이미지를 모델에 넣기 위한 전처리
        requestImg =  request.files["file"]
        openImage = Image.open(requestImg.stream).convert('RGB')
        resized_image = openImage.resize((150, 150))
        
        # img = image.load_img(img_path, target_size=(150, 150))
        img_array = image.img_to_array(resized_image)
        img_array = np.expand_dims(img_array, axis=0)  # 배치 크기 추가
        img_array /= 255.0  # 모델이 학습된 대로 이미지 스케일 조정

        # 이미지 예측
        prediction = model.predict(img_array)

        # 예측된 숫자값 반환
        return float(prediction[0][0])

    # 사용 예시
    model_path = r'food_testmodel_v1.h5'  # 모델 파일 경로

    predicted_value = predict_image(model_path)
    print(f'예측된 숫자값은 {predicted_value:.2f} 입니다.')
    
    if (predicted_value <= 0.5):
        return "1"
    return "0"

@app.route("/work", methods=['POST'])
def work():
    def predict_image(model_path):
        # 모델 불러오기
        model = load_model(model_path, compile=False)

        # 이미지를 모델에 넣기 위한 전처리
        requestImg =  request.files["file"]
        openImage = Image.open(requestImg.stream).convert('RGB')
        resized_image = openImage.resize((150, 150))
        img_array = image.img_to_array(resized_image)
        img_array = np.expand_dims(img_array, axis=0)  # 배치 크기 추가
        img_array /= 255.0  # 모델이 학습된 대로 이미지 스케일 조정

        # 이미지 예측
        prediction = model.predict(img_array)

        # 예측된 숫자값 반환
        return float(prediction[0][0])

    # 사용 예시
    model_path = r'worksearch_model.h5'

    predicted_value = predict_image(model_path)

    # 예측 결과 출력
    # 자세가 올바릅니다
    if predicted_value > 0.5:
        return "1"
    # 자세가 올바르지않습니다
    else:
        return "0"
