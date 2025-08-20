# 🤖 Bobbot - 보안 위협 분석 Slack 챗봇

보안 위협 인텔리전스(CTI) 및 IoC 분석을 자동화하는 FastAPI 기반 Slack 챗봇입니다.  
외부 인텔리전스(VirusTotal, Hybrid Analysis, Urlscan)와 연동하여 IP, 도메인, 파일 해시를 실시간 분석하고,  
BobWiki 검색 기능도 제공합니다.

## ✨ 주요 기능

- 🔍 **CTI 분석**: IP/도메인/파일 해시 자동 분석 및 결과 저장
- 🛡️ **IoC 분석**: IP 기반 악성 여부 분석
- 👥 **사용자 관리**: 사용자 등록/조회, 접근 로그 기록
- 🔐 **API 키 인증**: X-API-Key 헤더 기반 보안
- 💬 **Slack 연동**: Socket Mode를 통한 실시간 채팅 분석
- 📚 **BobWiki 검색**: 위키 컨텐츠 검색 및 요약
- 🐳 **Docker 지원**: 완전한 컨테이너화 환경

## 🚀 빠른 시작 (Docker)

### 1. 저장소 클론

```bash
git clone https://github.com/NamhyeonKo/bob14-chatbot.git
cd bob14-chatbot
```

### 2. 환경설정 파일 생성

#### `.env` 파일 생성:

```bash
# Database Configuration
MYSQL_ROOT_PASSWORD=your_mysql_root_password
MYSQL_DATABASE=bobbot
MYSQL_USER=bobbot
MYSQL_PASSWORD=your_mysql_password

# Application Configuration
DB_HOST=mariadb
DB_PORT=3306
DB_USER=bobbot
DB_PASSWORD=your_mysql_password
DB_NAME=bobbot

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token
```

#### `conf.json` 파일 생성:

```json
{
    "database": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "",
        "database": "bobbot"
    },
    "log": "debug",
    "api_key": "your_internal_api_key",
    "virustotal_api_key": "your_virustotal_api_key",
    "hybrid_analysis_api_key": "your_hybrid_analysis_api_key", 
    "urlscan_api_key": "your_urlscan_api_key"
}
```

### 3. Docker로 실행

```bash
docker-compose up --build -d
```

서비스가 http://localhost:8000 에서 실행됩니다.

## 🔧 로컬 개발 환경

### 1. Python 환경 (3.12+ 권장)

```bash
pip install -r requirements.txt
```

### 2. MariaDB 준비

```bash
# Docker로 MariaDB 실행
docker run -d --name bobbot-mariadb \
  -e MYSQL_ROOT_PASSWORD=password \
  -e MYSQL_DATABASE=bobbot \
  -p 3306:3306 mariadb:10.11
```

### 3. 애플리케이션 실행

```bash
uvicorn main:app --reload
```

## 📡 API 엔드포인트

### CTI 분석

```bash
POST /cti/analyze
Content-Type: application/json
X-API-Key: your_api_key

{
  "item": "8.8.8.8"  # IP, 도메인, 파일 해시 지원
}
```

### IoC 분석

```bash
POST /ioc/analyze/ip
Content-Type: application/json  
X-API-Key: your_api_key

{
  "ip": "192.168.1.1"
}
```

### 사용자 관리

```bash
# 사용자 등록
POST /users/
{
  "username": "testuser",
  "email": "test@example.com"
}

# 사용자 조회 (접근 IP IoC 자동 분석)
GET /users/{user_id}
```

### API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 💬 Slack 챗봇 설정

### 1. Slack App 생성

1. [api.slack.com/apps](https://api.slack.com/apps)에서 새 앱 생성
2. **Socket Mode** 활성화
3. **Bot Token Scopes** 설정:
   - `chat:write`
   - `app_mentions:read`
   - `channels:history`

### 2. 토큰 발급

- **Bot User OAuth Token**: `xoxb-`로 시작
- **App-Level Token**: `xapp-`로 시작 (connections:write 스코프 필요)

### 3. Slack에서 사용법

```txt
@bobbot cti 8.8.8.8
@bobbot ioc malicious-domain.com
@bobbot wiki 고남현
```

### 4. 응답 예시

```txt
🔍 CTI 분석 결과: 8.8.8.8
━━━━━━━━━━━━━━━━━━━━━━
🛡️ 위험도: 안전 (0/84 탐지)
🏢 소유자: Google LLC
🌍 위치: 미국
⏰ 분석 시간: 2024-08-20 15:30:25
```

## 🔐 보안 고려사항

- **민감정보 관리**: `.env`, `conf.json`은 Git에 커밋되지 않음
- **API 키 보호**: 모든 외부 API 키는 환경변수로 관리
- **인증**: X-API-Key 헤더 기반 API 접근 제어
- **Docker 보안**: 최소 권한 원칙, 비루트 사용자 실행

## 🚨 외부 API 제한사항

| 서비스 | 무료 한도 | 비고 |
|--------|-----------|------|
| VirusTotal | 1000 req/month | 공개 API |
| Hybrid Analysis | 200 req/month | 샌드박스 분석 |
| URLScan.io | 1000 req/month | URL 스캔 |

## 🛠️ 개발 가이드

### 새로운 분석 엔진 추가

1. `app/crud/` 에 분석 로직 구현
2. `app/api/` 에 엔드포인트 추가  
3. `app/schemas/` 에 요청/응답 스키마 정의
4. `app/models/` 에 DB 모델 추가

### 로그 확인

```bash
# Docker 환경
docker-compose logs api -f

# 로컬 환경  
tail -f app.log
```

## 📄 라이센스

이 프로젝트는 BoB(Best of the Best) 14기 교육과정의 일환으로 개발되었습니다.

---
