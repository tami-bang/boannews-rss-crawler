# __init__.py
"""
boannews RSS Crawler 패키지

- 공개 API: fetch_rss_entries
- 패키지 로딩 시 버전 정보 설정 (__version__)
RSS URL 검색 + RSS 파싱 + feed 반환
"""

# src/__init__.py
from .rss import fetch_all_entries 

__all__ = ["fetch_entries"]
__version__ = "1.0.0"
