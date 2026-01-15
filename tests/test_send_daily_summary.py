# tests/test_send_daily_summary.py
import pytest
from send_daily_summary import clean_text, start_dt, end_dt

def test_clean_text():
    assert clean_text("<b>abc</b>") =="abc"
    assert clean_text(None) =="내용 없음"

def test_date_range():
    assert start_dt < end_dt,"start_dt가 end_dt보다 크거나 같음"


