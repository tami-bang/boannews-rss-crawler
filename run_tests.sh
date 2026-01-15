#!/bin/bash
# ===============================================================
# run_tests.sh - NewsCrawler 프로젝트 테스트 통합 실행 스크립트
# ===============================================================
# 사용법:
#   ./run_tests.sh fast   -> FAST 모드 (개발/디버그용)
#   ./run_tests.sh full   -> FULL 모드 (운영/회귀용)
# 기능:
# 1. FAST 모드: CRON 대기시간 단축, 반복 테스트 빠르게
# 2. FULL 모드: 실제 CRON 간격 반영, 운영/회귀 테스트용
# 3. 병렬 실행 지원 (pytest-xdist)
# 4. 테스트 결과 요약 출력
# ===============================================================

# ------------------------------
# 1. 실행 모드 선택
# ------------------------------
MODE=${1:-fast}
if [[ "$MODE" != "fast" && "$MODE" != "full" ]]; then
    echo "사용법: ./run_tests.sh [fast|full]"
    exit 1
fi

export TEST_MODE=${MODE^^}  # FAST 또는 FULL

echo "=== Test Mode: $MODE ==="

# 프로젝트 루트를 PYTHONPATH에 추가
export PYTHONPATH=$(pwd):$PYTHONPATH

# ------------------------------
# 2. pytest 명령어 설정
# ------------------------------
PYTEST_CMD="pytest -v tests/"

# 병렬 옵션 (CPU 2개 기준, 필요 시 변경 가능)
PYTEST_CMD+=" -n 2 --dist=loadscope"

# 모드별 안내 메시지
if [[ "$MODE" == "fast" ]]; then
    echo "=== Running FAST tests (CRON waits shortened) ==="
else
    echo "=== Running FULL tests (including CRON simulations) ==="
fi

# ------------------------------
# 3. 테스트 실행
# ------------------------------
$PYTEST_CMD
RESULT=$?

# ------------------------------
# 4. 테스트 결과 처리
# ------------------------------
if [[ $RESULT -eq 0 ]]; then
    echo "=== All tests passed successfully! ==="
else
    echo "=== Some tests failed! Check logs above. ==="
fi

exit $RESULT

