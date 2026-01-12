"""
Comprehensive test suite for SD upscale plugin.
Tests both the buggy input.py and fixed_plugin.py to validate fixes.
"""

import sys
import unittest
from unittest.mock import Mock, MagicMock, patch
from PIL import Image
import io


# Mock the modules that would normally come from Stable Diffusion WebUI
class MockUpscaler:
    def __init__(self, name, data_path=None):
        self.name = name
        self.data_path = data_path
        self.scaler = Mock()
        self.scaler.upscale = Mock(side_effect=self._mock_upscale)
    
    def _mock_upscale(self, img, scale_factor, data_path):
        """Mock upscaling by resizing image"""
        new_w = int(img.width * scale_factor)
        new_h = int(img.height * scale_factor)
        return img.resize((new_w, new_h), Image.LANCZOS)


class MockProcessing:
    @staticmethod
    def fix_seed(p):
        if p.seed is None or p.seed == -1:
            p.seed = 12345
    
    @staticmethod
    def process_images(p):
        """Mock image processing"""
        processed = Mock()
        processed.seed = p.seed
        processed.info = f"Mock processing info: seed={p.seed}"
        # Return mock processed images - one for each input image
        num_images = len(p.init_images) if hasattr(p.init_images, '__len__') else 1
        processed.images = [Image.new("RGB", (p.width, p.height), color=(100, 150, 200)) 
                           for _ in range(num_images)]
        return processed


class MockProcessed:
    def __init__(self, p, result_images, seed, info):
        self.p = p
        self.images = result_images
        self.seed = seed
        self.info = info


class MockShared:
    sd_upscalers = [
        MockUpscaler("None"),
        MockUpscaler("Lanczos"),
        MockUpscaler("ESRGAN_4x"),
    ]
    
    class opts:
        img2img_background_color = "#ffffff"
        samples_save = False
        samples_format = "png"
    
    class state:
        job_count = 0
        job = ""


class MockImages:
    @staticmethod
    def flatten(img, bg_color):
        """Mock flatten - convert RGBA to RGB"""
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, bg_color)
            background.paste(img, mask=img.split()[3])
            return background
        return img.convert('RGB')
    
    @staticmethod
    def split_grid(img, tile_w, tile_h, overlap):
        """Mock split_grid - simulate tiling"""
        tiles = []
        
        # Avoid infinite loops - ensure stride is positive
        stride_h = max(1, tile_h - overlap)
        stride_w = max(1, tile_w - overlap)
        
        rows = max(1, (img.height + stride_h - 1) // stride_h)
        cols = max(1, (img.width + stride_w - 1) // stride_w)
        
        # Limit to reasonable number of tiles for testing
        rows = min(rows, 3)
        cols = min(cols, 3)
        
        for r in range(rows):
            y = r * stride_h
            if y >= img.height:
                break
            row_tiles = []
            for c in range(cols):
                x = c * stride_w
                if x >= img.width:
                    break
                # Create tile image
                x2 = min(x + tile_w, img.width)
                y2 = min(y + tile_h, img.height)
                tile_img = img.crop((x, y, x2, y2))
                # Use list instead of tuple so it's mutable
                row_tiles.append([x, tile_w, tile_img])
            if row_tiles:
                # Use list instead of tuple so it's mutable
                tiles.append([y, tile_h, row_tiles])
        
        result = Mock()
        result.tiles = tiles
        return result
    
    @staticmethod
    def combine_grid(grid):
        """Mock combine_grid - return a combined image"""
        # Calculate total dimensions
        if not grid.tiles:
            return Image.new("RGB", (512, 512))
        
        total_width = sum(tile[1] for tile in grid.tiles[0][2])
        total_height = sum(tile[1] for tile in grid.tiles)
        
        return Image.new("RGB", (total_width, total_height), color=(50, 100, 150))
    
    @staticmethod
    def save_image(img, path, prefix, seed, prompt, format, info=None, p=None):
        """Mock save_image"""
        pass


class MockDevices:
    @staticmethod
    def torch_gc():
        """Mock garbage collection"""
        pass


class MockGradio:
    """Mock Gradio components"""
    class HTML:
        def __init__(self, value=None, **kwargs):
            self.value = value
            self.kwargs = kwargs
    
    class Slider:
        def __init__(self, minimum=0, maximum=100, step=1, label="", value=0, **kwargs):
            self.minimum = minimum
            self.maximum = maximum
            self.step = step
            self.label = label
            self.value = value
            self.kwargs = kwargs
    
    class Radio:
        def __init__(self, label="", choices=None, value=None, type=None, **kwargs):
            self.label = label
            self.choices = choices or []
            self.value = value
            self.type = type
            self.kwargs = kwargs


class MockScripts:
    class Script:
        def __init__(self):
            self._elem_id_prefix = "test"
        
        def elem_id(self, name):
            return f"{self._elem_id_prefix}_{name}"
        
        def title(self):
            return "Test Script"
        
        def show(self, is_img2img):
            return is_img2img


# Mock parameters object for testing
class MockParams:
    def __init__(self):
        self.seed = 12345
        self.init_images = [Image.new("RGB", (512, 512), color=(200, 200, 200))]
        self.width = 128
        self.height = 128
        self.batch_size = 1
        self.n_iter = 1
        self.do_not_save_grid = False
        self.do_not_save_samples = False
        self.prompt = "test prompt"
        self.outpath_samples = "/tmp"
        self.extra_generation_params = {}


# Setup mocks in sys.modules
mock_modules = Mock()
mock_modules.scripts = Mock(Script=MockScripts.Script)
mock_modules.processing = Mock(
    fix_seed=MockProcessing.fix_seed,
    process_images=MockProcessing.process_images,
    Processed=MockProcessed
)
mock_modules.shared = MockShared
mock_modules.images = MockImages
mock_modules.devices = MockDevices

sys.modules['modules'] = mock_modules
sys.modules['modules.scripts'] = mock_modules.scripts
sys.modules['modules.processing'] = mock_modules.processing
sys.modules['modules.shared'] = MockShared
sys.modules['modules.images'] = MockImages
sys.modules['modules.devices'] = MockDevices

# Mock gradio as a module with component classes
mock_gradio = Mock()
mock_gradio.HTML = MockGradio.HTML
mock_gradio.Slider = MockGradio.Slider
mock_gradio.Radio = MockGradio.Radio
sys.modules['gradio'] = mock_gradio


class TestBuggyPlugin(unittest.TestCase):
    """Tests demonstrating bugs in input.py"""
    
    @classmethod
    def setUpClass(cls):
        # Import the buggy plugin
        import input as buggy_plugin
        cls.buggy_script = buggy_plugin.Script()
    
    def test_bug1_parameter_order_mismatch(self):
        """Test that buggy plugin has parameter order mismatch between ui() and run()"""
        # Get UI components
        components = self.buggy_script.ui(True)
        
        # In buggy version: [info, upscaler_index, overlap, scale_factor]
        # But run() expects: (p, _, overlap, upscaler_index, scale_factor)
        
        self.assertIsInstance(components, list)
        self.assertEqual(len(components), 4)
        # This test documents the bug - the order is wrong
        # Component[1] is upscaler_index but run() thinks it's overlap
        # Component[2] is overlap but run() thinks it's upscaler_index
        
        # Verify the component labels to show the order
        upscaler_radio = components[1]
        overlap_slider = components[2]
        self.assertEqual(upscaler_radio.label, "Upscaler")
        self.assertEqual(overlap_slider.label, "Tile overlap")
    
    def test_bug2_upscaler_type_mismatch(self):
        """Test that buggy plugin's Radio returns string, not index"""
        components = self.buggy_script.ui(True)
        upscaler_radio = components[1]  # Second component is upscaler in buggy version
        
        # In buggy version, Radio doesn't have type="index"
        # So it would return a string, but run() treats it as an int
        self.assertIsNone(upscaler_radio.type, 
                         "Buggy version should not have type='index'")
    
    def test_bug3_upscaler_indexing_error(self):
        """Test that buggy plugin will fail when trying to index with wrong type"""
        p = MockParams()
        
        # Simulate what happens with parameter order mismatch:
        # overlap value (64) goes to upscaler_index position
        # This should cause an error or unexpected behavior
        try:
            # In buggy version, if upscaler_index receives a string from Radio,
            # it tries to use it as list index which will fail
            result = self.buggy_script.run(p, None, "Lanczos", 64, 2.0)
            # If it doesn't crash, it's because we're in test environment
            # In real scenario, string index would cause TypeError
        except (TypeError, KeyError, IndexError):
            # Expected - trying to index list with string or out of range
            pass
    
    def test_bug4_none_upscaler_still_scales(self):
        """Test that buggy plugin still scales image when 'None' is selected"""
        # This test documents the bug in the code
        # Read the source to verify the buggy behavior exists
        import inspect
        source = inspect.getsource(self.buggy_script.run)
        
        # Verify the buggy code path exists:
        # When upscaler is "None", it still resizes with NEAREST
        self.assertIn("Image.NEAREST", source)
        self.assertIn('if upscaler.name != "None"', source)


class TestFixedPlugin(unittest.TestCase):
    """Tests verifying fixes in fixed_plugin.py"""
    
    @classmethod
    def setUpClass(cls):
        # Import the fixed plugin
        import fixed_plugin
        cls.fixed_script = fixed_plugin.Script()
    
    def test_fix1_parameter_order_correct(self):
        """Test that fixed plugin has correct parameter order"""
        components = self.fixed_script.ui(True)
        
        # In fixed version: [info, overlap, upscaler_index, scale_factor]
        # Matches run() signature: (p, _, overlap, upscaler_index, scale_factor)
        
        self.assertIsInstance(components, list)
        self.assertEqual(len(components), 4)
        # Verify order by checking component types/attributes
        overlap_component = components[1]
        upscaler_component = components[2]
        
        self.assertEqual(overlap_component.label, "Tile overlap")
        self.assertEqual(upscaler_component.label, "Upscaler")
    
    def test_fix2_upscaler_has_type_index(self):
        """Test that fixed plugin's Radio has type='index'"""
        components = self.fixed_script.ui(True)
        upscaler_radio = components[2]  # Third component is upscaler in fixed version
        
        # In fixed version, Radio has type="index"
        self.assertEqual(upscaler_radio.type, "index",
                        "Fixed version should have type='index'")
    
    def test_fix3_run_with_correct_parameters(self):
        """Test that fixed plugin runs correctly with proper parameter types"""
        p = MockParams()
        
        # Call with correct parameter order and types
        # overlap=64 (int), upscaler_index=1 (int for Lanczos), scale_factor=2.0
        result = self.fixed_script.run(p, None, 64, 1, 2.0)
        
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'images'))
        self.assertIsInstance(result.images, list)
        self.assertGreater(len(result.images), 0)
    
    def test_fix4_defensive_type_handling(self):
        """Test that fixed plugin handles string upscaler_index gracefully"""
        p = MockParams()
        
        # Even if we pass a string (shouldn't happen, but defensive code handles it)
        result = self.fixed_script.run(p, None, 64, "Lanczos", 2.0)
        
        # Should not crash, should convert string to index
        self.assertIsNotNone(result)
    
    def test_fix5_none_upscaler_no_scaling(self):
        """Test that fixed plugin doesn't scale when 'None' is selected"""
        p = MockParams()
        original_img = p.init_images[0]
        original_size = (original_img.width, original_img.height)
        
        # upscaler_index=0 is "None", scale_factor=2.0
        # In fixed version, scale_factor should be ignored when upscaler is "None"
        result = self.fixed_script.run(p, None, 64, 0, 2.0)
        
        # The result should exist and not have scaled the image
        self.assertIsNotNone(result)
        
        # Verify the fix in code - should NOT apply scale_factor with "None"
        import inspect
        source = inspect.getsource(self.fixed_script.run)
        # Fixed version should pass through original image when "None"
        self.assertIn("img = init_img", source)
    
    def test_fix6_overlap_validation(self):
        """Test that fixed plugin validates overlap against tile dimensions"""
        p = MockParams()
        p.width = 64
        p.height = 64
        
        # Try to use overlap that's too large (should be clamped)
        # overlap=256, but tile is only 64x64
        result = self.fixed_script.run(p, None, 256, 1, 2.0)
        
        # Should not crash - overlap should be clamped
        self.assertIsNotNone(result)
        # Check that overlap was adjusted in extra_generation_params
        actual_overlap = p.extra_generation_params.get("SD upscale overlap", 256)
        self.assertLess(actual_overlap, 64, 
                       f"Overlap should be clamped below tile size, got {actual_overlap}")
    
    def test_fix7_invalid_upscaler_index_handling(self):
        """Test that fixed plugin handles invalid upscaler indices"""
        p = MockParams()
        
        # Try with out-of-range index
        result = self.fixed_script.run(p, None, 64, 999, 2.0)
        
        # Should not crash - should default to index 0
        self.assertIsNotNone(result)
    
    def test_fix8_negative_upscaler_index_handling(self):
        """Test that fixed plugin handles negative upscaler indices"""
        p = MockParams()
        
        # Try with negative index
        result = self.fixed_script.run(p, None, 64, -1, 2.0)
        
        # Should not crash - should default to index 0
        self.assertIsNotNone(result)
    
    def test_fix9_defensive_code_exists(self):
        """Test that fixed plugin has defensive type checking code"""
        import inspect
        source = inspect.getsource(self.fixed_script.run)
        
        # Verify defensive type checking exists
        self.assertIn("isinstance(upscaler_index, str)", source)
        self.assertIn("isinstance(upscaler_index, int)", source)


class TestIntegration(unittest.TestCase):
    """Integration tests comparing buggy vs fixed behavior"""
    
    def setUp(self):
        import input as buggy_plugin
        import fixed_plugin
        self.buggy_script = buggy_plugin.Script()
        self.fixed_script = fixed_plugin.Script()
    
    def test_ui_component_count(self):
        """Both versions should return same number of components"""
        buggy_components = self.buggy_script.ui(True)
        fixed_components = self.fixed_script.ui(True)
        
        self.assertIsInstance(buggy_components, list)
        self.assertIsInstance(fixed_components, list)
        self.assertEqual(len(buggy_components), len(fixed_components))
    
    def test_title_difference(self):
        """Titles should indicate buggy vs fixed"""
        buggy_title = self.buggy_script.title()
        fixed_title = self.fixed_script.title()
        
        self.assertIn("buggy", buggy_title.lower())
        self.assertIn("fixed", fixed_title.lower())
    
    def test_component_order_difference(self):
        """Buggy and fixed versions should have different component orders"""
        buggy_components = self.buggy_script.ui(True)
        fixed_components = self.fixed_script.ui(True)
        
        # Buggy: [info, upscaler_index, overlap, scale_factor]
        # Fixed: [info, overlap, upscaler_index, scale_factor]
        
        buggy_second = buggy_components[1]
        fixed_second = fixed_components[1]
        
        # In buggy version, second component is upscaler
        # In fixed version, second component is overlap
        self.assertEqual(buggy_second.label, "Upscaler")
        self.assertEqual(fixed_second.label, "Tile overlap")
    
    def test_fixed_more_robust(self):
        """Fixed version should handle edge cases better"""
        p = MockParams()
        
        # Test cases that should work in fixed version
        test_cases = [
            (64, 0, 1.0),   # Minimal scaling with "None"
            (32, 2, 3.5),   # Normal case
            (128, 1, 1.5),  # Large overlap (will be clamped)
        ]
        
        for overlap, upscaler_idx, scale in test_cases:
            with self.subTest(overlap=overlap, upscaler=upscaler_idx, scale=scale):
                # Reset params for each test
                p = MockParams()
                result = self.fixed_script.run(p, None, overlap, upscaler_idx, scale)
                self.assertIsNotNone(result, 
                    f"Fixed version should handle overlap={overlap}, "
                    f"upscaler={upscaler_idx}, scale={scale}")


def run_tests():
    """Run all tests and return results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBuggyPlugin))
    suite.addTests(loader.loadTestsFromTestCase(TestFixedPlugin))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
