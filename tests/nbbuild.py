"""Build .ipynb files from a list of (kind, text) cells.

Authoring notebooks as JSON by hand is unreadable and error-prone. The notebooks in this
repository are generated from plain source by the scripts in ``notebooks/_src``.
"""

from __future__ import annotations

import hashlib
import json
import pathlib


def build(cells: list[tuple[str, str]], path: pathlib.Path, kernel: str = 'python3') -> pathlib.Path:
    """Write *cells* as a notebook at *path*. Each cell is ('md'|'code', source)."""
    out = []
    for position, (kind, text) in enumerate(cells):
        source = text.strip('\n').split('\n')
        source = [line + '\n' for line in source[:-1]] + [source[-1]]
        # Stable id derived from position and content, so regenerating a notebook
        # without changing it produces no diff.
        cell_id = hashlib.sha1(f'{position}:{text}'.encode()).hexdigest()[:8]
        if kind == 'md':
            out.append({'cell_type': 'markdown', 'id': cell_id, 'metadata': {}, 'source': source})
        elif kind == 'code':
            out.append({'cell_type': 'code', 'id': cell_id, 'execution_count': None,
                        'metadata': {}, 'outputs': [], 'source': source})
        else:
            raise ValueError(f'unknown cell kind {kind!r}')
    nb = {
        'cells': out,
        'metadata': {
            'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': kernel},
            'language_info': {'name': 'python'},
        },
        'nbformat': 4,
        'nbformat_minor': 5,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nb, indent=1) + '\n')
    return path
