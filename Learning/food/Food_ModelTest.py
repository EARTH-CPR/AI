from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np

def predict_image(model_path, img_path):
    # 모델 불러오기
    model = load_model(model_path, compile=False)

    # 이미지를 모델에 넣기 위한 전처리
    img = image.load_img(img_path, target_size=(150, 150))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)  # 배치 크기 추가
    img_array /= 255.0  # 모델이 학습된 대로 이미지 스케일 조정

    # 이미지 예측
    prediction = model.predict(img_array)

    # 예측된 숫자값 반환
    return float(prediction[0][0])

# 사용 예시
model_path = r'D:\2024신한해커톤\음식 섭취 추정 프로젝트\food_testmodel_v1.h5'  # 모델 파일 경로
img_path = r'D:\2024신한해커톤\음식 섭취 추정 프로젝트\TestImage\example.jpg'  # 예측할 이미지 경로

predicted_value = predict_image(model_path, img_path)
print(f'예측된 숫자값은 {predicted_value:.2f} 입니다.')