import subprocess
import sys


def test_cli_module_displays_help():
    result = subprocess.run(
        [sys.executable, "-m", "uk_job_market_agents", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--snapshot" in result.stdout
    assert "--mode" in result.stdout

    assert "usage: python -m uk_job_market_agents" in result.stdout
