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
model_path = r'C:\2024신한해커톤\운동 인식 프로젝트\model\worksearch_model.h5'  # 모델 파일 경로
img_path = r'C:\2024신한해커톤\운동 인식 프로젝트\Data\testImage\rightImage.jpg'  # 예측할 이미지 경로

predicted_value = predict_image(model_path, img_path)

# 예측 결과 출력
if predicted_value > 0.5:
    print(f'자세가 올바릅니다 , 예측값은 {predicted_value:.2f} 입니다.')
else:
    print(f'자세가 올바르지않습니다 , 예측값은 {predicted_value:.2f} 입니다.')