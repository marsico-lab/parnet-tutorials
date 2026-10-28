"""Resolve every file the notebooks need through ``config/filepaths.yaml``.

No notebook in this repository contains an absolute path. A notebook asks for a logical
name and gets back a :class:`pathlib.Path`; which file that is depends on the machine,
and the mapping lives in one gitignored YAML file per machine.

The failure mode this is built to avoid is a notebook that runs on the author's machine
and dies three cells in on someone else's. :func:`model_path` and :func:`dataset_path`
check that the file exists at resolution time and raise with the config key, the resolved
path and the line to edit, rather than letting a later ``torch.load`` fail on its own.
"""

from __future__ import annotations

import pathlib
from typing import Any

import yaml

#: Marker that identifies the project root when walking up from the working directory.
_ROOT_MARKER = 'pyproject.toml'

_CONFIG_RELATIVE = pathlib.Path('config') / 'filepaths.yaml'
_EXAMPLE_RELATIVE = pathlib.Path('config') / 'filepaths.example.yaml'


def project_root(start: pathlib.Path | str | None = None) -> pathlib.Path:
    """Return the repository root, found by walking up from *start* (default: cwd).

    Jupyter sets the working directory to the notebook's own directory, so a notebook in
    ``notebooks/`` finds the root one level up without knowing where it was launched from.
    """
    here = pathlib.Path(start or pathlib.Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / _ROOT_MARKER).is_file():
            return candidate
    raise FileNotFoundError(
        f'No {_ROOT_MARKER} found walking up from {here}. Run this from inside a clone '
        'of parnet-tutorials.'
    )


def config_path(root: pathlib.Path | None = None) -> pathlib.Path:
    """Return the path of the active ``config/filepaths.yaml``, or explain how to make one."""
    root = root or project_root()
    path = root / _CONFIG_RELATIVE
    if not path.exists():
        raise FileNotFoundError(
            f'{path} does not exist. This file is machine-specific and deliberately not '
            f'committed. Create it with:\n'
            f'    cp {root / _EXAMPLE_RELATIVE} {root}/config/filepaths.$(hostname -s).yaml\n'
            f'    # edit the copy so its paths exist here\n'
            f'    cd {root}/config && ln -sf filepaths.$(hostname -s).yaml filepaths.yaml'
        )
    return path


def load_config(root: pathlib.Path | None = None) -> dict[str, Any]:
    """Parse ``config/filepaths.yaml`` into a plain dict."""
    return yaml.safe_load(config_path(root).read_text()) or {}


def resolve(value: str, root: pathlib.Path | None = None) -> pathlib.Path:
    """Resolve one config value: absolute paths as-is, relative ones from the project root."""
    root = root or project_root()
    path = pathlib.Path(value).expanduser()
    return path if path.is_absolute() else (root / path)


def _lookup(section: str, key: str, root: pathlib.Path | None = None) -> pathlib.Path:
    root = root or project_root()
    config = load_config(root)
    if section not in config:
        raise KeyError(f"config/filepaths.yaml has no '{section}:' section. See config/filepaths.example.yaml.")
    entries = config[section] or {}
    if key not in entries:
        raise KeyError(
            f"config/filepaths.yaml has no '{section}: {key}:' entry. "
            f'Known keys in that section: {sorted(entries)}'
        )
    return resolve(entries[key], root)


def dataset_path(key: str, root: pathlib.Path | None = None, *, must_exist: bool = True) -> pathlib.Path:
    """Resolve ``datasets: <key>`` and, by default, require that it exists."""
    path = _lookup('datasets', key, root)
    if must_exist and not path.exists():
        raise FileNotFoundError(
            f"Dataset '{key}' resolves to {path}, which does not exist on this machine. "
            f'Edit the datasets section of {config_path(root)}.'
        )
    return path


def classification_path(key: str, root: pathlib.Path | None = None, *, must_exist: bool = True) -> pathlib.Path:
    """Resolve ``classification: <key>`` and, by default, require that it exists."""
    path = _lookup('classification', key, root)
    if must_exist and not path.exists():
        raise FileNotFoundError(
            f"Classification dataset '{key}' resolves to {path}, which does not exist here. "
            f'Edit the classification section of {config_path(root)}.'
        )
    return path


def model_path(key: str, root: pathlib.Path | None = None, *, must_exist: bool = True) -> pathlib.Path:
    """Resolve ``models: <key>`` to the model STEM.

    The stem has no suffix: callers append ``.safetensors`` for the weights and
    ``.config.json`` for the architecture. Both are checked when *must_exist*.
    """
    stem = _lookup('models', key, root)
    if must_exist:
        missing = [
            str(stem) + suffix
            for suffix in ('.safetensors', '.config.json')
            if not pathlib.Path(str(stem) + suffix).exists()
        ]
        if missing:
            raise FileNotFoundError(
                f"Model '{key}' resolves to the stem {stem}, but these are missing: {missing}. "
                f'Edit the models section of {config_path(root)}.'
            )
    return stem


def task_names(key: str, root: pathlib.Path | None = None) -> list[str]:
    """Read an ordered task-name list from ``config/tasks/<key>.yaml``.

    Task names are a property of the DATASET a model was trained on, not of the model, so
    they live here rather than in the library. The order is the track order of the
    corresponding output axis and must not be sorted.
    """
    root = root or project_root()
    path = root / 'config' / 'tasks' / f'{key}.yaml'
    if not path.exists():
        available = sorted(p.stem for p in (root / 'config' / 'tasks').glob('*.yaml'))
        raise FileNotFoundError(f'No task config {path}. Available: {available}')
    payload = yaml.safe_load(path.read_text())
    return list(payload['tasks'])
