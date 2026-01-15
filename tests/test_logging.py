# tests/test_logging.py
"""
CRON/실행 로그 존재 및 최근 로그 확인
"""

import pytest
from tests.helpers import get_recent_logs

def test_logs_exist_and_recent():
    logs = get_recent_logs()
    assert len(logs) > 0, "로그 파일 없음 또는 내용 없음"

    print("최근 로그 10줄 확인:")
    for line in logs[-10:]:
        print(line)

