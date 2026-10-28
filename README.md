# PARNET tutorials

Notebooks for using PARNET: loading a model, predicting eCLIP signal, reading what a
checkpoint actually contains, fine-tuning, embeddings, and interpretation.

Every notebook here is executed as part of the test suite. A tutorial that does not run
is not a tutorial.

## Install

PARNET itself comes from the `refactor` branch while that work is in progress:

```bash
pip install "git+https://github.com/marsico-lab/parnet-marsico-lab.git@refactor"
pip install -e ".[run]"
```

On a machine with an older NVIDIA driver, install torch from the matching CUDA index
first, otherwise pip resolves a build whose `torch.cuda.is_available()` is False with no
error at all:

```bash
pip install --index-url https://download.pytorch.org/whl/cu118 "torch>=2.5"
pip install -e ".[run]"
```

## Paths

No notebook contains an absolute path. Each one asks for a logical name and
`config/filepaths.yaml` says what that means on this machine:

```bash
cp config/filepaths.example.yaml config/filepaths.$(hostname -s).yaml
# edit the copy so its paths exist here
cd config && ln -sf filepaths.$(hostname -s).yaml filepaths.yaml
```

The per-machine file and the symlink are both gitignored; only the example is committed.
Relative paths resolve from the repository root, absolute paths are used as they are.

Models and datasets are never committed. They are large, and several are unpublished.

## Task names

A model knows how many output tasks it has and nothing about what they are called. Track
names are a property of the dataset, so they live in `config/tasks/*.yaml` and are read
with `parnet_tutorials.task_names('encode-223')`.

Filter tracks by cell type using the `ct` field of those files, never by splitting the
track name. Content and model label disagree at 10 of the 223 ENCODE tracks, and at 4 the
cell type itself differs.

## Shared machines

`torch` defaults to one thread per core, so several people training at once on one box
oversubscribe it. Measured with four processes on 16 cores: 34.3 steps per second each at
a cap of 2 threads, against 3.9 uncapped. Caps of 1, 2 and 4 behave the same; 8 drops to
23.6.

```python
import torch
torch.set_num_threads(2)
```

The first cell of every notebook here does that.

## Running the tests

```bash
python tests/run_notebooks.py            # execute every notebook
python tests/run_notebooks.py 01 02      # only some
pytest tests -q                          # the unit tests
```
