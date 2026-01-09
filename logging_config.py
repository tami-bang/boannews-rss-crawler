import logging
from logging.handlers import TimedRotatingFileHandler
import os
from typing import Literal

def setup_logging(
    log_path: str = "logs/app.log",
    mode: Literal["dev", "prod"] = "dev"
) -> None:
    """
    로깅 설정
    - 로그파일 경로가 주어지면 해당 경로 사용
    - 매일 자정 새로운 로그파일 생성, 이전 로그는 날짜별로 백업
    - 14일 경과한 로그 자동 삭제
    - 개발 모드(dev) → 콘솔에도 DEBUG 출력
    - 운영 모드(prod) → 콘솔에는 WARNING 이상만 출력

    Args:
        log_path (str): 로그 파일 경로
        mode (Literal["dev","prod"]): 개발/운영 모드
    """
    
    # logs 폴더 없으면 생성
 
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # 파일은 DEBUG 이상 기록

    if root.handlers:
        return  # 중복 핸들러 방지
    
    # 파일 핸들러: DEBUG~ERROR 모두 기록, 하루 단위 회전, 14일 보관
    file_handler = TimedRotatingFileHandler(
        log_path,
        when="midnight",
        interval=1,
        backupCount=14,
        encoding="utf-8",
        utc=False
    )
    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s : %(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_fmt)
    file_handler.setLevel(logging.DEBUG)    # DEBUG 이상 모두 기록
    root.addHandler(file_handler)

    # 콘솔 핸들러
    class ConsoleFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if mode == "dev":
                # 개발 모드: DEBUG와 WARNING 이상 출력
                return record.levelno == logging.DEBUG or record.levelno >= logging.WARNING
            else:
                # 운영 모드: WARNING 이상만 출력
                return record.levelno >= logging.WARNING

    console_handler = logging.StreamHandler()
    console_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s : %(message)s"
    )
    console_handler.setFormatter(console_fmt)
    console_handler.addFilter(ConsoleFilter())
    root.addHandler(console_handler)

    root.info("로깅 설정 완료. 로그 파일: %s, 모드: %s", log_path, mode)