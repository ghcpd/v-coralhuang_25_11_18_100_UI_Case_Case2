# Fixed SD Upscale Plugin

This project bundles a standalone `fixed_plugin.py` implementation that addresses the UI wiring bugs present in the original `input.py` sample. It also includes environment scripts, tests, and Docker assets so you can reproduce the workflow end-to-end.

## Setup

```bash
./setup.sh
```

This script creates a local `.venv`, bootstraps pip (even when `ensurepip` is disabled), and installs the testing dependencies from `requirements.txt`.

## Running the demo

```bash
./run.sh
```

`run.sh` uses the same virtual environment to execute `fixed_plugin.py`, which prints a summary of the sanitized upscale parameters.

## Testing

```bash
./test.sh
```

This invokes `pytest` through the virtual environment and will fail if the original bugs still exist or if behavior departs from the spec.

## Docker

Build the image and run the test suite inside a container:

```bash
docker build -t sd-upscale:latest .
docker run --rm sd-upscale:latest
```

The container installs the same dependencies via `setup.sh` and the default `CMD` executes `./test.sh`, fulfilling the requirement that `docker run` executes the tests end-to-end.
