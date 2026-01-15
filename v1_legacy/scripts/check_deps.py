# check_deps.py
# Quick runtime check for transformers, torch, pillow and GPU visibility
import importlib, sys

print('=== Dependency check start ===')

# transformers
try:
    transformers = importlib.import_module('transformers')
    print('transformers:', getattr(transformers, '__version__', 'unknown'))
except Exception as e:
    print('transformers import failed:', repr(e))

# torch
try:
    import torch
    print('torch:', torch.__version__, 'cuda_available=', torch.cuda.is_available())
    if torch.cuda.is_available():
        try:
            print('cuda device count:', torch.cuda.device_count())
            # print device names (attempt for first 4 devices)
            for i in range(min(4, torch.cuda.device_count())):
                try:
                    print(f'device {i}:', torch.cuda.get_device_name(i))
                except Exception as e:
                    print(f'device name for {i} failed:', repr(e))
        except Exception as e:
            print('cuda info error:', repr(e))
except Exception as e:
    print('torch import failed:', repr(e))

# Pillow
try:
    from PIL import Image
    import PIL
    print('Pillow:', PIL.__version__)
except Exception as e:
    print('Pillow import failed:', repr(e))

print('python:', sys.version.replace('\n', ' '))
print('=== Dependency check end ===')
