# Instructions for Running Tests

This document provides step-by-step instructions for setting up and running the SD upscale plugin tests.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Docker (optional, for containerized testing)

## Local Testing (Linux/macOS/Git Bash on Windows)

### Step 1: Setup Environment

Run the setup script to create a virtual environment and install dependencies:

```bash
./setup.sh
```

This will:
- Create a Python virtual environment in `venv/`
- Install required packages: Pillow, gradio

**Note**: On Windows PowerShell, you may need to use Git Bash or WSL to run shell scripts. Alternatively, you can manually run:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install Pillow gradio
```

### Step 2: Verify Setup (Optional)

Run the verification script:

```bash
./run.sh
```

This checks that all dependencies are available.

### Step 3: Run Tests

Execute the test suite:

```bash
./test.sh
```

Or run directly with Python:

```bash
python test_plugin.py
```

### Expected Output

You should see output like:

```
============================================================
SD Upscale Plugin Test Suite
============================================================
Test 1: Parameter order matching...
  [OK] UI components created successfully
  [OK] Fixed plugin handles correct parameter order
  [OK] Buggy plugin fails as expected: IndexError

Test 2: Upscaler type handling...
  [OK] Fixed plugin handles integer upscaler index
  [OK] Fixed plugin handles string upscaler name (defensive)
  [OK] Buggy plugin fails with string as expected: TypeError

Test 3: 'None' upscaler behavior...
  [OK] Fixed plugin handles 'None' upscaler without unexpected scaling
  [WARN] Buggy plugin failed: IndexError (may be due to other bugs)

Test 4: Overlap validation...
Warning: Tile overlap clamped to 99 (tile size: 100x100)
  [OK] Fixed plugin handles large overlap (150) safely
  [OK] Fixed plugin handles normal overlap (32) correctly

Test 5: End-to-end functionality...
  [OK] Fixed plugin completes end-to-end processing successfully

============================================================
Test Results: 5 passed, 0 failed
============================================================
```

All tests should pass (5 passed, 0 failed).

## Docker Testing

### Step 1: Build Docker Image

```bash
docker build -t sd-upscale-test .
```

This will:
- Use Python 3.10 slim base image
- Copy all project files
- Run `setup.sh` to install dependencies
- Set default command to run tests

### Step 2: Run Tests in Container

```bash
docker run --rm sd-upscale-test
```

The `--rm` flag automatically removes the container after execution.

### Expected Output

Same as local testing - all 5 tests should pass.

## Windows PowerShell Alternative

If you're on Windows and don't have Git Bash or WSL:

1. **Setup**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install Pillow gradio
   ```

2. **Run Tests**:
   ```powershell
   python test_plugin.py
   ```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'gradio'"

**Solution**: Run `setup.sh` or manually install dependencies:
```bash
pip install Pillow gradio
```

### Issue: "Permission denied" on shell scripts

**Solution**: Make scripts executable:
```bash
chmod +x setup.sh run.sh test.sh
```

On Windows, use Git Bash or run Python commands directly.

### Issue: Docker build fails

**Solution**: 
- Ensure Docker is running
- Check that all files are present in the project directory
- Verify Dockerfile syntax

### Issue: Tests hang or timeout

**Solution**: This should not happen with the current implementation. If it does:
- Check Python version (3.8+ required)
- Ensure all dependencies are installed
- Check system resources

## Test Interpretation

- **[OK]**: Test passed as expected
- **[FAIL]**: Test failed (should not happen with fixed plugin)
- **[WARN]**: Expected behavior for buggy plugin (tests are verifying bugs exist)

## Files Overview

- `input.py`: Original buggy plugin (read-only reference)
- `fixed_plugin.py`: Fixed plugin with all bugs resolved
- `test_harness.py`: Mock SD WebUI modules for testing
- `test_plugin.py`: Test suite (5 tests covering all bug fixes)
- `setup.sh`: Environment setup script
- `run.sh`: Environment verification script
- `test.sh`: Test execution script
- `Dockerfile`: Containerized testing configuration

## Next Steps

After verifying tests pass:
1. Review `BUG_ANALYSIS.md` for detailed bug explanations
2. Review `fixed_plugin.py` to see the fixes
3. Compare with `input.py` to understand what changed

