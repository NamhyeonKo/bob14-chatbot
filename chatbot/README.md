# Bobbot API (Slack Chatbot 백엔드)

보안 위협 인텔리전스(CTI) 및 IoC(Indicator of Compromise) 분석 자동화 API 서버입니다. 
외부 인텔리전스(VirusTotal, Hybrid Analysis, Urlscan)와 연동하여 IP, 도메인, 파일 해시 등 다양한 보안 정보를 분석·저장합니다.
추가로 bobwiki 검색 기능도 제공합니다.

**Slack Chatbot Socket Mode와 연동**하여 Slack 채널에서 보안 분석 및 bobwiki 검색을 실시간으로 수행할 수 있습니다.

## 주요 기능

- **CTI 분석**: IP/도메인/파일 해시 입력 시, 적합한 외부 인텔리전스 API를 자동 선택하여 분석 결과 저장
- **IOC 분석**: IP 기반 악성 여부 분석 및 DB 저장
- **User 관리**: 사용자 등록, 조회, 접근 로그 기록
- **API 키 인증**: 모든 API는 X-API-Key 헤더 필요
- **MySQL 연동**: SQLAlchemy 기반 ORM, DB에 결과 저장
- **Docker 지원**: Dockerfile, docker-compose 포함
- **Slack Bot 연동**: Socket Mode를 통한 실시간 Slack 채널 보안 분석 및 bobwiki 검색 결과 제공

## 설치 및 환경설정

### 1. Python 환경
- Python 3.10 이상 권장
- 의존성 설치:

```bash
pip install -r requirements.txt
```

### 2. DB 준비
- maria DB 사용
- conf.json에 DB 접속 정보 입력

### 3. 외부 API 키 준비
- conf.json에 아래 항목 추가/수정:
```json
{
  "database": { ... },
  "api_key": "<내부 API 인증키>",
  "VIRUSTOTAL_API_KEY": "<발급받은 키>",
  "HYBRID_API_KEY": "<발급받은 키>",
  "URLSCAN_API_KEY": "<발급받은 키>"
}
```

### 4. DB 테이블 생성
- Alembic 등 마이그레이션 도구 사용 또는 최초 1회 수동 생성 필요

### 5. 실행
```bash
uvicorn main:app --reload
```

## 주요 API 엔드포인트

### 1. CTI 분석
- **POST /cti/analyze**
- 입력: `{ "item": "8.8.8.8" }` (IP, 도메인, 해시 모두 지원)
- 응답: 분석 결과 및 원시 데이터

### 2. IOC 분석
- **POST /ioc/analyze/ip**
- 입력: `{ "ip": "8.8.8.8" }`
- 응답: 악성/의심/정상 카운트 등

### 3. User
- **POST /users/**: 사용자 등록
- **GET /users/{user_id}**: 사용자 조회 및 접근 IP IoC 분석

## 인증
- 모든 API 요청 시 `X-API-Key` 헤더 필수

## 예시 요청 (curl)
```bash
curl -X POST http://localhost:8000/cti/analyze \
  -H "X-API-Key: <내부키>" \
  -H "Content-Type: application/json" \
  -d '{"item": "example.com"}'
```

## Slack Chatbot 연동 (Socket Mode)

이 API는 Slack Chatbot의 백엔드 서버로 사용됩니다. Slack Socket Mode를 통해 실시간으로 보안 분석을 수행할 수 있습니다.

### Slack Bot 설정 방법

1. **Slack App 생성**
   - [api.slack.com](https://api.slack.com/apps) 에서 새 앱 생성
   - Socket Mode 활성화
   - Bot Token Scopes 설정: `chat:write`, `app_mentions:read`, `channels:history`

2. **Bot Token & App Token 발급**
   ```json
   {
     "slack": {
       "bot_token": "xoxb-your-bot-token",
       "app_token": "xapp-your-app-token"
     }
   }
   ```

3. **Slack에서 사용법**
   ```
   @botname ioc 8.8.8.8
   @botname bobwiki 고남현
   ```

4. **응답 형태**
   - 분석 결과를 Slack 채널에 실시간 전송
   - 악성도 점수, 탐지 업체, 위험 레벨 표시
   - 외부 인텔리전스 요약 정보 제공
   - bobwiki에서 원하는 검색 결과 요약 제공

### Socket Mode 장점
- **실시간 통신**: WebSocket 기반 즉시 응답
- **방화벽 우회**: 인바운드 연결 불필요
- **보안성**: 토큰 기반 인증, HTTPS 암호화

## 개발/운영 참고
- 외부 인텔리전스 API는 요금제/쿼터 제한이 있으니 키 관리 주의
- conf.json 등 민감정보는 git에 커밋하지 마세요
- DB 테이블 구조/스키마는 models/ 참고
- raw_data 필드는 외부 API 원본 전체 저장(용량 주의)

## 프로젝트 구조

```text
app/
├── api/          # API 엔드포인트
├── core/         # 핵심 설정 및 보안
├── crud/         # 데이터베이스 작업
├── models/       # SQLAlchemy 모델
├── schemas/      # Pydantic 스키마
└── database.py   # 데이터베이스 연결
```

## 라이선스
bob14기 교육으로 만들어짐
