# 1. 베이스 이미지 선택
FROM python:3.13.2

# 2. 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 3. 작업 디렉토리 설정 (가장 일반적인 /app 사용)
WORKDIR /app

# 4. 의존성 설치 (빌드 캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사
COPY . .

# 6. 애플리케이션 포트 노출
EXPOSE 8000

# 7. 컨테이너 실행 명령어
# 'main:app'은 main.py 파일의 app 변수를 의미합니다. 파일명이 다르면 수정해주세요.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]