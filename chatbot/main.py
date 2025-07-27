import uvicorn
import time
from config import conf

LOG = conf.get('log', 'info') # 설정 파일에서 로그 레벨을 가져오고, 없으면 'info'를 기본값으로

if __name__ == '__main__':
    try:
        if LOG == 'debug':
            uvicorn.run(
                "api:app",
                host='0.0.0.0',
                port=8080,
                workers=1,
                log_level='debug', # 로그 레벨을 debug로 변경
                reload=True,
            )
        else:
            uvicorn.run(
                "api:app",
                host='0.0.0.0',
                port=8080,
                workers=5,
                log_level='warning',
                reload=False,
            )
    except KeyboardInterrupt:
        print('\nExiting\n')
    except Exception as errormain:
        print('Failed to Start API')
        print('='*100)
        print(str(errormain))
        print('='*100)
        print('Exiting\n')