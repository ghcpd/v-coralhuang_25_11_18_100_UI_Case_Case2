# SD Upscale Plugin - Bug Fix Project

## Overview

This project demonstrates debugging and fixing a broken Stable Diffusion WebUI plugin. The original `input.py` contains intentional UI bugs that have been identified, documented, and fixed in `fixed_plugin.py`.

## Bug Summary

### Bug 1: Parameter Order Mismatch
**Issue**: The `ui()` method returns components in order `[info, upscaler_index, overlap, scale_factor]`, but the `run()` method expects `(p, _, overlap, upscaler_index, scale_factor)`. This causes runtime parameter swapping.

**Impact**: The upscaler selection receives overlap values, and the overlap parameter receives upscaler values.

**Fix**: Reordered UI component return to match: `[info, overlap, upscaler_index, scale_factor]`

### Bug 2: Upscaler Radio Type Mismatch
**Issue**: The Upscaler `Radio` component lacks `type="index"`, causing it to return a string (upscaler name) instead of an integer index.

**Impact**: The code attempts to use the string as a list index: `shared.sd_upscalers[upscaler_index]`, causing TypeError.

**Fix**: Added `type="index"` to the Radio component and implemented defensive type checking in `run()`.

### Bug 3: Inconsistent "None" Upscaler Behavior
**Issue**: When upscaler is "None", the buggy code still applies `scale_factor` using low-quality `Image.NEAREST` resampling.

**Impact**: Users expect "None" to disable upscaling, but images are still resized.

**Fix**: When upscaler is "None", the original image is passed through unchanged (no scaling applied).

### Bug 4: Missing Overlap Validation
**Issue**: The overlap slider allows values 0-256 without validation against tile dimensions.

**Impact**: When overlap >= tile size, the tiling algorithm produces errors or pathological behavior.

**Fix**: Added validation to clamp overlap to `min(tile_width, tile_height) - 1`.

## Project Structure

```
.
├── input.py           # Original buggy plugin (read-only reference)
├── fixed_plugin.py    # Fixed version with all bugs resolved
├── test_plugin.py     # Comprehensive test suite (17 tests)
├── setup.sh          # Dependency installation script
├── test.sh           # Test execution script
├── run.sh            # Optional interactive test harness
├── Dockerfile        # Container for reproducible testing
└── README.md         # This file
```

## Requirements

- Python 3.10 or later
- pip (Python package manager)
- Docker (optional, for containerized testing)

## Quick Start

### Local Testing

1. **Install Dependencies**
   ```bash
   bash setup.sh
   ```
   Or on Windows PowerShell:
   ```powershell
   python -m pip install Pillow
   ```

2. **Run Tests**
   ```bash
   bash test.sh
   ```
   Or on Windows PowerShell:
   ```powershell
   python test_plugin.py
   ```

3. **Optional: Interactive Harness**
   ```bash
   bash run.sh
   ```
   This opens a Python REPL with both buggy and fixed plugins loaded for manual testing.

### Docker Testing

1. **Build the Container**
   ```bash
   docker build -t sd-upscale-test .
   ```

2. **Run Tests in Container**
   ```bash
   docker run sd-upscale-test
   ```

3. **Interactive Mode**
   ```bash
   docker run -it sd-upscale-test /app/run.sh
   ```

## Test Suite

The test suite (`test_plugin.py`) includes:

### Tests for Buggy Plugin (4 tests)
- `test_bug1_parameter_order_mismatch` - Documents parameter order issue
- `test_bug2_upscaler_type_mismatch` - Verifies missing `type="index"`
- `test_bug3_upscaler_indexing_error` - Demonstrates indexing errors
- `test_bug4_none_upscaler_still_scales` - Documents unwanted scaling with "None"

### Tests for Fixed Plugin (9 tests)
- `test_fix1_parameter_order_correct` - Verifies correct parameter order
- `test_fix2_upscaler_has_type_index` - Confirms `type="index"` is present
- `test_fix3_run_with_correct_parameters` - Tests normal operation
- `test_fix4_defensive_type_handling` - Tests string upscaler_index handling
- `test_fix5_none_upscaler_no_scaling` - Verifies no scaling with "None"
- `test_fix6_overlap_validation` - Tests overlap clamping
- `test_fix7_invalid_upscaler_index_handling` - Tests out-of-range indices
- `test_fix8_negative_upscaler_index_handling` - Tests negative indices
- `test_fix9_defensive_code_exists` - Verifies defensive code in source

### Integration Tests (3 tests)
- `test_ui_component_count` - Compares component counts
- `test_title_difference` - Verifies titles indicate buggy vs fixed
- `test_component_order_difference` - Confirms parameter order differences
- `test_fixed_more_robust` - Tests edge cases

**Total: 17 tests** - All tests must pass for validation.

## Expected Output

When running `bash test.sh` or `python test_plugin.py`, you should see:

```
test_bug1_parameter_order_mismatch ... ok
test_bug2_upscaler_type_mismatch ... ok
test_bug3_upscaler_indexing_error ... ok
test_bug4_none_upscaler_still_scales ... ok
test_fix1_parameter_order_correct ... ok
test_fix2_upscaler_has_type_index ... ok
test_fix3_run_with_correct_parameters ... ok
test_fix4_defensive_type_handling ... ok
test_fix5_none_upscaler_no_scaling ... ok
test_fix6_overlap_validation ... ok
test_fix7_invalid_upscaler_index_handling ... ok
test_fix8_negative_upscaler_index_handling ... ok
test_fix9_defensive_code_exists ... ok
test_component_order_difference ... ok
test_fixed_more_robust ... ok
test_title_difference ... ok
test_ui_component_count ... ok

----------------------------------------------------------------------
Ran 17 tests in 0.XXXs

OK
```

## Design Decisions

### 1. Parameter Order Fix
**Decision**: Changed UI return order to match `run()` signature exactly.
**Rationale**: This is the most maintainable solution - the UI component order directly maps to the function signature.

### 2. Type Safety
**Decision**: Added `type="index"` to Radio AND defensive type checking in `run()`.
**Rationale**: Defense in depth - even if the Radio configuration is changed in the future, the code will handle it gracefully.

### 3. "None" Upscaler Behavior
**Decision**: Pass through original image unchanged when "None" is selected.
**Rationale**: This matches user expectations - "None" means no upscaling, not low-quality resizing.

### 4. Overlap Validation
**Decision**: Clamp overlap to `min(width, height) - 1` with a warning message.
**Rationale**: Prevents errors while informing users of the adjustment. An alternative would be to raise an error, but clamping is more user-friendly.

### 5. Index Validation
**Decision**: Default to index 0 for invalid indices (negative or out-of-range).
**Rationale**: Fail gracefully rather than crashing. Index 0 is typically the "None" upscaler, which is a safe default.

## Validation Strategy

The test suite uses comprehensive mocking to simulate the Stable Diffusion WebUI environment:
- **Mock Gradio components** for UI testing
- **Mock SD modules** (processing, shared, images, devices)
- **Mock upscalers** with realistic behavior
- **Image mocking** using PIL for realistic image operations

This approach allows testing without requiring the full SD WebUI installation.

## Continuous Integration

The Docker container provides a reproducible environment for CI/CD:
1. Installs dependencies via `setup.sh`
2. Runs full test suite via `test.sh`
3. Returns exit code 0 on success, 1 on failure

Example GitHub Actions workflow:
```yaml
- name: Build and Test
  run: |
    docker build -t sd-upscale-test .
    docker run sd-upscale-test
```

## Troubleshooting

### Tests fail with import errors
**Solution**: Run `setup.sh` or `python -m pip install Pillow`

### Tests fail with "Mock object" errors
**Solution**: Ensure you're using Python 3.10+ with unittest.mock

### Docker build fails
**Solution**: Ensure Docker is running and you have internet connectivity for base image download

### Specific test fails
**Solution**: Run `python test_plugin.py -v` for verbose output, or run specific tests:
```bash
python -m unittest test_plugin.TestFixedPlugin.test_fix1_parameter_order_correct
```

## Further Development

To extend this project:
1. Add more edge case tests (e.g., zero-size images, extreme scale factors)
2. Add performance benchmarks
3. Add integration tests with real SD WebUI if available
4. Add linting and type checking (mypy, pylint)
5. Add code coverage reporting (coverage.py)

## License

This is a test/demonstration project for bug fixing and testing practices.

## Contact

For questions or issues, please refer to the project repository.
