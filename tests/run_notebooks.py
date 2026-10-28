"""Execute every notebook and report pass/fail per notebook.

This is the acceptance test for the repository: a tutorial that does not run is not a
tutorial. Run it on each machine you intend to teach on, because the failures that matter
are environment failures.

    python tests/run_notebooks.py                 # all notebooks
    python tests/run_notebooks.py 01 04           # only those whose name starts with 01/04
    python tests/run_notebooks.py --timeout 1200

Executed copies are written to notebooks/_executed/ (gitignored) so a failure can be
opened and read, with the traceback in place.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from parnet_tutorials.paths import project_root  # noqa: E402


def run_one(path: pathlib.Path, out_dir: pathlib.Path, timeout: int) -> dict:
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(
        nb,
        timeout=timeout,
        kernel_name='python3',
        allow_errors=False,
        # Run with the notebook's own directory as cwd, which is what Jupyter does, so
        # project_root() walks up the same way here as it will interactively.
        resources={'metadata': {'path': str(path.parent)}},
    )
    started = time.time()
    record = {'notebook': path.name, 'status': 'passed', 'error': None}
    try:
        client.execute()
    except CellExecutionError as exc:
        record['status'] = 'failed'
        record['error'] = str(exc).strip().split('\n')[-1][:400]
    except Exception as exc:  # noqa: BLE001 - a kernel death is a real result too
        record['status'] = 'failed'
        record['error'] = f'{type(exc).__name__}: {exc}'[:400]
    record['seconds'] = round(time.time() - started, 1)
    out_dir.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, out_dir / path.name)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('prefixes', nargs='*', help='only notebooks whose name starts with one of these')
    parser.add_argument('--timeout', type=int, default=1800, help='per-cell timeout in seconds')
    parser.add_argument('--report', default=None, help='write a JSON report here')
    args = parser.parse_args()

    root = project_root(pathlib.Path(__file__).parent)
    notebooks = sorted((root / 'notebooks').glob('*.ipynb'))
    if args.prefixes:
        notebooks = [n for n in notebooks if any(n.name.startswith(p) for p in args.prefixes)]
    if not notebooks:
        print('no notebooks matched', file=sys.stderr)
        return 2

    out_dir = root / 'notebooks' / '_executed'
    results = []
    for path in notebooks:
        print(f'--- {path.name} ... ', end='', flush=True)
        record = run_one(path, out_dir, args.timeout)
        results.append(record)
        print(f"{record['status']} ({record['seconds']}s)")
        if record['error']:
            print(f"      {record['error']}")

    failed = [r for r in results if r['status'] != 'passed']
    print(f"\n{len(results) - len(failed)}/{len(results)} notebooks passed")
    if args.report:
        pathlib.Path(args.report).write_text(json.dumps(results, indent=1) + '\n')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
