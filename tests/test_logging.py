# tests/test_logging.py
import pytest
import os

def test_logs_exist_and_recent():
    """
    CRON/실행 로그 존재 확인 및 최근 로그 출력
    """
    log_file = "logs/app.log"
    assert os.path.exists(log_file), f"{log_file} 없음"

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) > 0, "로그 내용 없음"

    # 최근 로그 10줄 출력
    recent = lines[-10:]
    print("최근 로그 확인:")
    for line in recent:
        print(line.strip())
