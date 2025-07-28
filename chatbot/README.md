# Bobbot Chatbot API

FastAPI 기반의 채팅봇 API 서버입니다.

## 설치 방법

```bash
# 가상환경 생성
python -m venv .myvenv
source .myvenv/bin/activate  # Linux/Mac
# or
.myvenv\Scripts\activate  # Windows

# 패키지 설치
pip install -e .
```

## 실행 방법

```bash
# 방법 1: python으로 직접 실행
python main.py

# 방법 2: uvicorn으로 실행
uvicorn main:app --reload
```

## API 엔드포인트

- `POST /users/`: 새 사용자 생성
- `GET /users/{user_id}`: 사용자 정보 조회
- `POST /users/login`: 사용자 로그인

## 인증

모든 API 요청에는 `X-API-Key` 헤더가 필요합니다.
