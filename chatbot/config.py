import os
import json

CONFIG_FILE = './conf.json'

# conf.json 파일이 없으면 환경변수를 이용해 새로 생성
if not os.path.isfile(CONFIG_FILE):
    # 필요한 환경 변수가 설정되었는지 확인
    db_password = os.environ.get('DB_PASSWORD')
    log_level = os.environ.get('LOG_LVL')
    api_key = os.environ.get('API_KEY')

    if not all([db_password, log_level, api_key]):
        raise ValueError("필수 환경 변수가 설정되지 않았습니다: DB_PASSWORD, LOG_LVL, API_KEY")

    config_data = {
        "dbpassword": db_password,
        "log": log_level,
        "api_key": api_key
    }
    with open(CONFIG_FILE, 'w') as new_conf:
        json.dump(config_data, new_conf, indent=4)

# 설정 파일 읽기
with open(CONFIG_FILE, 'r') as main_conf:
    conf = json.load(main_conf)