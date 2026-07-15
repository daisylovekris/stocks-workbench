import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "akshare_daily_quote_check_v0.1.py"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


def test_off_benchmark_date_fails_closed_before_network() -> None:
    result = run_script("--date", "2026-07-13")

    assert result.returncode == 2
    assert "2026-07-06" in result.stdout
    assert "tools/generate_daily_facts.py" in result.stdout
    assert "\u672a\u53d1\u8d77\u4efb\u4f55\u8054\u7f51\u8bf7\u6c42" in result.stdout
    assert "\u8bf7\u66f4\u65b0 THS_BENCHMARK" not in result.stdout


def test_help_identifies_frozen_benchmark_and_production_entry() -> None:
    result = run_script("--help")

    assert result.returncode == 0
    assert "2026-07-06" in result.stdout
    assert "tools/generate_daily_facts.py" in result.stdout
