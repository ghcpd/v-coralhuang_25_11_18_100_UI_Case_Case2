"""
Test harness for SD upscale plugin testing.
Provides mock implementations of SD WebUI modules.
"""
import sys
import os
from unittest.mock import Mock, MagicMock
from PIL import Image
import math

# Mock gradio before any imports that use it
class MockHTML:
    def __init__(self, *args, **kwargs):
        pass

class MockSlider:
    def __init__(self, *args, **kwargs):
        pass

class MockRadio:
    def __init__(self, *args, **kwargs):
        pass

class MockGradio:
    HTML = MockHTML
    Slider = MockSlider
    Radio = MockRadio

sys.modules['gradio'] = MockGradio()
import gradio as gr


# Create mock modules structure
class MockUpscaler:
    def __init__(self, name, scaler=None, data_path=None):
        self.name = name
        self.scaler = scaler or MockScaler()
        self.data_path = data_path or ""


class MockScaler:
    def upscale(self, img, scale_factor, data_path):
        """Mock upscaler that resizes the image"""
        new_w = max(1, int(img.width * scale_factor))
        new_h = max(1, int(img.height * scale_factor))
        return img.resize((new_w, new_h), resample=Image.LANCZOS)


class MockGrid:
    def __init__(self, tiles):
        # tiles should be a list of lists: [y, h, row]
        # where row is a list of lists: [x, w, tile_image]
        # Using lists instead of tuples so they can be modified
        self.tiles = tiles if tiles else [[0, 0, []]]


class MockProcessed:
    def __init__(self, p, images, seed, info):
        self.p = p
        self.images = images
        self.seed = seed
        self.info = info


class MockProcessingParams:
    def __init__(self):
        self.width = 512
        self.height = 512
        self.batch_size = 1
        self.n_iter = 1
        self.seed = 42
        self.init_images = []
        self.extra_generation_params = {}
        self.prompt = "test prompt"
        self.outpath_samples = "/tmp/test_output"


# Mock modules
class MockScript:
    """Mock Script base class that can be instantiated"""
    def __init__(self):
        pass
    
    def elem_id(self, name):
        """Mock elem_id method"""
        return f"mock_{name}"

class MockScriptsModule:
    Script = MockScript


class MockSharedModule:
    class MockOpts:
        img2img_background_color = (0, 0, 0)
        samples_save = False
        samples_format = "png"
    
    class MockState:
        job_count = 0
        job = ""
    
    sd_upscalers = [
        MockUpscaler("None"),
        MockUpscaler("Lanczos", MockScaler()),
        MockUpscaler("ESRGAN", MockScaler()),
    ]
    opts = MockOpts()
    state = MockState()


class MockImagesModule:
    @staticmethod
    def flatten(img, bg_color):
        """Mock flatten - just returns the image"""
        return img
    
    @staticmethod
    def split_grid(img, tile_w, tile_h, overlap):
        """Mock split_grid - creates a simple grid"""
        # Ensure overlap doesn't cause infinite loops
        overlap = max(0, min(overlap, tile_w - 1, tile_h - 1))
        
        # If image is smaller than tile, just return one tile
        # Use lists instead of tuples so they can be modified
        if img.width <= tile_w and img.height <= tile_h:
            return MockGrid([[0, img.height, [[0, img.width, img.copy()]]]])
        
        tiles = []
        y = 0
        max_iterations = 1000  # Safety limit
        iterations = 0
        
        while y < img.height and iterations < max_iterations:
            iterations += 1
            h = min(tile_h, img.height - y)
            if h <= 0:
                break
            row = []
            x = 0
            row_iterations = 0
            while x < img.width and row_iterations < max_iterations:
                row_iterations += 1
                w = min(tile_w, img.width - x)
                if w <= 0:
                    break
                # Create a tile image
                tile_img = img.crop((x, y, x + w, y + h))
                # Use list instead of tuple so tiledata[2] can be modified
                row.append([x, w, tile_img])
                step = max(1, w - overlap)  # Ensure we always advance
                x += step
                if step <= 0 or x >= img.width:  # Safety check
                    break
            
            if row:  # Only add non-empty rows
                # Use list instead of tuple
                tiles.append([y, h, row])
            
            step = max(1, h - overlap)  # Ensure we always advance
            y += step
            if step <= 0 or y >= img.height:  # Safety check
                break
        
        # Ensure we have at least one tile
        if not tiles:
            tiles = [[0, img.height, [[0, img.width, img.copy()]]]]
        
        return MockGrid(tiles)
    
    @staticmethod
    def combine_grid(grid):
        """Mock combine_grid - combines tiles back into an image"""
        if not grid.tiles:
            return Image.new("RGB", (100, 100))
        
        # Calculate total dimensions
        max_w = 0
        max_h = 0
        for y, h, row in grid.tiles:
            max_h = max(max_h, y + h)
            for x, w, tile_img in row:
                max_w = max(max_w, x + w)
        
        result = Image.new("RGB", (max_w, max_h))
        for y, h, row in grid.tiles:
            for x, w, tile_img in row:
                result.paste(tile_img, (x, y))
        
        return result
    
    @staticmethod
    def save_image(img, path, prefix, seed, prompt, fmt, info=None, p=None):
        """Mock save_image - does nothing"""
        pass


class MockDevicesModule:
    @staticmethod
    def torch_gc():
        """Mock torch_gc - does nothing"""
        pass


class MockProcessingModule:
    @staticmethod
    def fix_seed(p):
        """Mock fix_seed - does nothing"""
        pass
    
    @staticmethod
    def process_images(p):
        """Mock process_images - returns processed result with same images"""
        # Return processed images (just pass through for testing)
        processed_images = []
        for img in p.init_images:
            processed_images.append(img.copy())
        
        return MockProcessed(
            p,
            processed_images,
            p.seed,
            "test info"
        )


# Install mocks into sys.modules
sys.modules['modules'] = type(sys)('modules')
sys.modules['modules.scripts'] = MockScriptsModule()
sys.modules['modules.shared'] = MockSharedModule()
sys.modules['modules.images'] = MockImagesModule()
sys.modules['modules.devices'] = MockDevicesModule()
sys.modules['modules.processing'] = MockProcessingModule()
sys.modules['modules.processing'].Processed = MockProcessed

# Set attributes on modules package for easier access
sys.modules['modules'].scripts = sys.modules['modules.scripts']
sys.modules['modules'].shared = sys.modules['modules.shared']
sys.modules['modules'].images = sys.modules['modules.images']
sys.modules['modules'].devices = sys.modules['modules.devices']
sys.modules['modules'].processing = sys.modules['modules.processing']

