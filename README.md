# SD Upscale Plugin - Bug Fixes and Testing

This project contains a buggy SD upscale plugin (`input.py`) and a fixed version (`fixed_plugin.py`), along with a complete test suite to verify the fixes.

## Bugs Fixed

### 1. Parameter Order Mismatch
**Problem**: `ui()` returned `[info, upscaler_index, overlap, scale_factor]` but `run()` expected `[info, overlap, upscaler_index, scale_factor]`, causing parameter values to be swapped at runtime.

**Fix**: Corrected the return order in `ui()` to match `run()` signature: `[info, overlap, upscaler_index, scale_factor]`.

### 2. Upscaler Radio Type Mismatch
**Problem**: The Radio component returned a string (upscaler name) instead of an integer index, but `run()` used it directly as a list index without type checking.

**Fix**: 
- Restored `type="index"` in the Radio component to return integer indices
- Added defensive type checking in `run()` to handle both integer indices and string names

### 3. Inconsistent Scale Factor Behavior
**Problem**: When upscaler was "None", the code still applied scaling using `Image.resize()`, contradicting user expectations.

**Fix**: When upscaler is "None", the original image is returned without any scaling applied.

### 4. Missing Overlap Validation
**Problem**: The overlap slider allowed values up to 256 with no validation against tile dimensions, potentially causing errors in `images.split_grid()`.

**Fix**: Added validation to clamp overlap to `min(tile_width, tile_height) - 1` to prevent pathological behavior.

## Project Structure

```
.
├── input.py              # Original buggy plugin (read-only)
├── fixed_plugin.py       # Fixed plugin implementation
├── test_harness.py       # Mock SD WebUI modules for testing
├── test_plugin.py        # Test suite
├── setup.sh              # Environment setup script
├── run.sh                # Environment verification script
├── test.sh               # Test execution script
├── Dockerfile            # Containerized testing
└── README.md             # This file
```

## Quick Start

### Local Testing

1. **Setup environment**:
   ```bash
   ./setup.sh
   ```

2. **Verify setup** (optional):
   ```bash
   ./run.sh
   ```

3. **Run tests**:
   ```bash
   ./test.sh
   ```

### Docker Testing

1. **Build the Docker image**:
   ```bash
   docker build -t sd-upscale-test .
   ```

2. **Run tests in container**:
   ```bash
   docker run --rm sd-upscale-test
   ```

## Test Suite

The test suite (`test_plugin.py`) includes:

1. **Parameter Order Test**: Verifies that UI and run() parameter order matches
2. **Upscaler Type Handling**: Tests integer index and string name handling
3. **None Upscaler Behavior**: Verifies that "None" upscaler doesn't apply scaling
4. **Overlap Validation**: Tests that large overlap values are safely clamped
5. **End-to-End Test**: Full pipeline test with realistic parameters

## Design Decisions

### Mock Implementation
Since the actual Stable Diffusion WebUI is not available, we created mock implementations of:
- `modules.scripts.Script` base class
- `modules.shared` (sd_upscalers, opts, state)
- `modules.images` (flatten, split_grid, combine_grid, save_image)
- `modules.devices` (torch_gc)
- `modules.processing` (fix_seed, process_images, Processed)

These mocks provide minimal functionality needed to test the plugin logic without requiring the full SD WebUI installation.

### Fix Strategy
- **Parameter Order**: Fixed at the source (UI return order) rather than adding workarounds in run()
- **Type Safety**: Added both UI-level fix (type="index") and defensive checks in run() for robustness
- **Behavior Consistency**: Made "None" upscaler behavior explicit and predictable
- **Input Validation**: Added clamping with warning messages rather than failing silently

## Requirements

- Python 3.8+
- pip
- Docker (optional, for containerized testing)

Dependencies are installed automatically by `setup.sh`:
- Pillow (PIL)
- gradio

## Troubleshooting

### Tests fail with import errors
- Ensure `setup.sh` has been run successfully
- Activate the virtual environment: `source venv/bin/activate`
- Verify dependencies: `pip list | grep -E "(Pillow|gradio)"`

### Docker build fails
- Ensure Docker is running
- Check that all files are present in the project directory
- Verify Dockerfile syntax

### Permission denied on scripts
- Make scripts executable: `chmod +x setup.sh run.sh test.sh`
- On Windows, use Git Bash or WSL to run shell scripts

## License

This is a test/demonstration project for debugging purposes.


