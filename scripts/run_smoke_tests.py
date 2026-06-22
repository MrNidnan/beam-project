#!/usr/bin/env python

import argparse
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SMOKE_SCRIPTS = {
    'windows': [
        'scripts/smoke_imports.py',
        'scripts/smoke_virtualdj.py',
        'scripts/smoke_foobar.py',
        'scripts/smoke_mixxx.py',
        'scripts/smoke_icecast.py',
        'scripts/smoke_smtc.py',
        'scripts/smoke_background_pipeline.py',
        'scripts/smoke_network_display_port.py',
        'scripts/smoke_network_apply_wiring.py',
    ],
    'linux': [
        'scripts/smoke_imports.py',
        'scripts/smoke_mixxx.py',
        'scripts/smoke_icecast.py',
        'scripts/smoke_mpris.py',
        'scripts/smoke_background_pipeline.py',
        'scripts/smoke_network_display_port.py',
        'scripts/smoke_network_apply_wiring.py',
    ],
}

FATAL_OUTPUT_PATTERNS = [
    re.compile(r'Traceback \(most recent call last\):', re.IGNORECASE),
    re.compile(r'^ERROR:\w+', re.IGNORECASE | re.MULTILINE),
    re.compile(r'\bCRITICAL\b', re.IGNORECASE),
]

SKIP_OUTPUT_PATTERNS = [
    re.compile(r'\bskipped\b', re.IGNORECASE),
    re.compile(r"No module named 'wx'", re.IGNORECASE),
    re.compile(r'ModuleNotFoundError:\s+No module named [\"\']wx[\"\']', re.IGNORECASE),
]


def _parse_args():
    parser = argparse.ArgumentParser(description='Run Beam smoke test suite with strict log/error detection.')
    parser.add_argument(
        '--platform',
        required=True,
        choices=['windows', 'linux'],
        help='Target smoke suite platform.',
    )
    return parser.parse_args()


def _classify_result(return_code, output):
    if return_code != 0:
        if any(pattern.search(output) for pattern in SKIP_OUTPUT_PATTERNS):
            return 'SKIP'
        return 'FAIL'

    if any(pattern.search(output) for pattern in FATAL_OUTPUT_PATTERNS):
        return 'FAIL'

    if any(pattern.search(output) for pattern in SKIP_OUTPUT_PATTERNS):
        return 'SKIP'

    return 'PASS'


def _run_script(script_rel_path):
    script_path = ROOT / script_rel_path
    command = [sys.executable, str(script_path)]
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    output = (completed.stdout or '') + (completed.stderr or '')
    status = _classify_result(completed.returncode, output)
    return status, output.strip()


def main():
    args = _parse_args()
    scripts = SMOKE_SCRIPTS[args.platform]

    results = []
    for script_rel_path in scripts:
        status, output = _run_script(script_rel_path)
        results.append((script_rel_path, status, output))

        print('[{0}] {1}'.format(status, script_rel_path))
        if output:
            print(output)

    pass_count = sum(1 for _, status, _ in results if status == 'PASS')
    skip_count = sum(1 for _, status, _ in results if status == 'SKIP')
    fail_count = sum(1 for _, status, _ in results if status == 'FAIL')

    print(
        'SMOKE SUMMARY: platform={0} total={1} pass={2} skip={3} fail={4}'.format(
            args.platform,
            len(results),
            pass_count,
            skip_count,
            fail_count,
        )
    )

    return 1 if fail_count else 0


if __name__ == '__main__':
    raise SystemExit(main())
