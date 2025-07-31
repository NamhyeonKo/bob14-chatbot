# Bobbot API Server

FastAPI 기반의 보안 분석 API 서버입니다. 사용자 관리와 IP 주소 IoC(Indicator of Compromise) 분석 기능을 제공합니다.

## 주요 기능

- 🔐 **사용자 관리**: 안전한 사용자 생성 및 조회
- 🛡️ **IoC 분석**: VirusTotal API를 통한 IP 주소 악성코드 분석
- 📊 **접근 로깅**: 사용자 접근 기록 및 IP 추적
- 🔒 **API 키 인증**: 보안 강화된 API 접근 제어

## 기술 스택

- **Framework**: FastAPI
- **Database**: MySQL/MariaDB with SQLAlchemy ORM
- **Security**: PBKDF2 password hashing, API key authentication
- **External API**: VirusTotal API integration
- **Deployment**: Docker & Docker Compose

## 설치 및 실행

### 1. 환경 설정

```bash
# Python 3.12+ 필요
python --version

# uv 사용 (권장)
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

uv sync

# 또는 pip 사용
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 설정 파일 생성

`conf.json` 파일을 생성하고 다음과 같이 설정:

```json
{
    "api_key": "your-api-key-here",
    "virustotal_api_key": "your-virustotal-api-key",
    "database": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "your-password",
        "database": "bobbot"
    },
    "log": "debug"
}
```

### 3. 데이터베이스 설정

```bash
# MySQL/MariaDB 데이터베이스 생성
mysql -u root -p
CREATE DATABASE bobbot;
```

### 4. 실행 방법

#### 개발 환경

```bash
# 직접 실행
python main.py

# uvicorn으로 실행 (reload 모드)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Docker 실행

```bash
# Docker Compose로 전체 스택 실행
docker-compose up -d

# 개별 컨테이너 빌드
docker build -t bobbot-api .
docker run -p 8000:8000 bobbot-api
```

## API 문서

서버 실행 후 다음 URL에서 API 문서 확인:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

## API 엔드포인트

### 사용자 관리

- `POST /users/`: 새 사용자 생성
- `GET /users/{user_id}`: 사용자 정보 조회 (접근 IP 자동 분석)

### IoC 분석

- `POST /ioc/analyze/ip`: IP 주소 악성코드 분석

## 사용 예시

### 1. 사용자 생성

```bash
curl -X POST "http://localhost:8000/users/" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword"
  }'
```

### 2. IP 분석

```bash
curl -X POST "http://localhost:8000/ioc/analyze/ip" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "8.8.8.8"
  }'
```

## 인증

모든 API 요청에는 `X-API-Key` 헤더가 필요합니다:

```http
X-API-Key: your-api-key-here
```

## 데이터베이스 스키마

### UserTable

- 사용자 기본 정보 (ID, 이메일, 사용자명, 해시된 비밀번호)

### AccessLogTable

- 사용자 접근 로그 (접근 시간, IP 주소, 액션)

### IoCTable

- IP 분석 결과 (악성/의심/무해 카운트, 평판 점수, VirusTotal 데이터)

## 보안 기능

- **PBKDF2 해싱**: 100,000회 반복을 통한 안전한 비밀번호 저장
- **Salt**: 각 비밀번호마다 고유한 salt 사용
- **API 키 인증**: 모든 엔드포인트에 API 키 필수
- **자동 IP 분석**: 사용자 접근 시 IP 주소 자동 위험도 분석

## 개발

### 프로젝트 구조

```text
app/
├── api/          # API 엔드포인트
├── core/         # 핵심 설정 및 보안
├── crud/         # 데이터베이스 작업
├── models/       # SQLAlchemy 모델
├── schemas/      # Pydantic 스키마
└── database.py   # 데이터베이스 연결
```

### 코딩 스타일

- Python 3.12+ 타입 힌트 사용
- FastAPI 모범 사례 준수
- SQLAlchemy 2.0+ 스타일

## 라이선스

이 프로젝트는 BOB(Best of the Best) 14기 교육과정의 일환으로 개발되었습니다.
