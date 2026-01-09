# logging_config.py
import logging
from logging.handlers import TimedRotatingFileHandler
import os

def setup_logging(log_path: str="logs/app.log") -> None:
    """로깅 설정 모듈
        매개변수로 로그파일 경로가 주어지면 주어진 경로로,
        주어지지 않으면 logs/app.log 에 로깅 하도록 설정.
        - 매일 자정 새로운 로그파일 생성. (전날 로그는 app.log.yyyymmdd 파일로 저장 됨)
        - 14 일 경과한 파일은 자동 삭제        

    Args:
        log_path (str, optional): _description_. Defaults to "logs/app.log".
    """
    # logs 폴더 없으면 생성
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)    # 개발 서버는 INFO / 운영 서버는 ERROR 레벨 권장.
    
    if root.handlers :
        return
    
    handler = TimedRotatingFileHandler(
        log_path,
        when = "midnight",
        interval = 1,
        backupCount = 14,
        encoding = "utf-8",
        utc = False        
    )
    
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s : %(lineno)d - %(message)s"
    )
    
    handler.setFormatter(fmt)
    root.addHandler(handler)
    # logs 폴더 자동 생성 기능 추가
    # 백업 파일 14일 유지, 매일 자정 새로운 파일 생성
    # 필요하면 level을 운영/개발 모드에 맞게 변경