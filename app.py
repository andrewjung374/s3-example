from flask import Flask, render_template, Response
# pip install flask opencv-python boto3
import cv2
import boto3
import os
from datetime import datetime

app = Flask(__name__)

# 네이버 클라우드 플랫폼 Object Storage 설정
# .env에 api 설정 값, api gateway url 넣으면 됨
CLOVA_API_URL = os.getenv("CLOVA_API_URL")  # 클로바 OCR API URL로 변경
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY")  # 클로바 OCR API Key로 변경
ACCESS_KEY = os.getenv('your_access_key') # 네이버 Obejct Storage Access Key로 변경
SECRET_KEY = os.getenv('your_secret_key') # 네이버 Obejct Storage Secret Key로 변경
REGION_NAME = 'kr-standard'
ENDPOINT_URL = 'https://kr.object.ncloudstorage.com'
BUCKET_NAME = os.getenv('your_bucket_name') # 네이버 Obejct Storage Secret Key로 변경

# S3 클라이언트 생성
s3 = boto3.client('s3',
                  aws_access_key_id=ACCESS_KEY,
                  aws_secret_access_key=SECRET_KEY,
                  region_name=REGION_NAME,
                  endpoint_url=ENDPOINT_URL)

# 카메라 설정
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def capture_and_upload():
    ret, frame = camera.read()
    if not ret:
        print("Failed to capture image")
        return "Failed to capture image"

    # 이미지 파일 이름 생성 (현재 시간 기준)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"captured_image_{timestamp}.jpg"
    
    # 이미지를 임시 파일로 저장
    cv2.imwrite(filename, frame)
    
    # Object Storage에 업로드
    try:
        s3.upload_file(filename, BUCKET_NAME, filename)
        print(f"Image uploaded successfully: {filename}")
        result = f"Image uploaded successfully: {filename}"
    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        result = f"Error uploading image: {str(e)}"
    
    # 임시 파일 삭제
    os.remove(filename)
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture', methods=['POST'])
def capture():
    result = capture_and_upload()
    return result

if __name__ == '__main__':
    app.run(debug=True)