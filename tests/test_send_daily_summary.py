# tests/test_send_daily_summary.py
"""
send_daily_summary 모듈 테스트
- 텍스트 정리(clean_text) 및 날짜 범위 확인
"""

import pytest
from send_daily_summary import clean_text, start_dt, end_dt

def test_clean_text():
    """HTML 태그 제거 및 None 처리 확인"""
    assert clean_text("<b>abc</b>") == "abc"
    assert clean_text(None) == "내용 없음"

def test_date_range():
    """start_dt < end_dt 확인"""
    assert start_dt < end_dt, "start_dt가 end_dt보다 크거나 같음"

