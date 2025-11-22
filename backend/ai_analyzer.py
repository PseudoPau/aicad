"""
ai_analyzer.py

A lightweight wrapper for Hugging Face image captioning (BLIP) with caching.
This module exposes ImageCaptioner which loads the processor+model once and
provides a .generate(image_path, prompt) method that returns text.

Dependencies:
  pip install transformers pillow torch

"""
from functools import lru_cache
from pathlib import Path
from typing import Optional


class HFModelLoadError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _load_blip_model():
    try:
        from transformers import BlipProcessor, BlipForConditionalGeneration
    except Exception as e:
        raise HFModelLoadError("Failed to import transformers. Please install 'transformers'.") from e

    try:
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
    except Exception as e:
        raise HFModelLoadError(f"Failed to load BLIP model: {e}") from e

    return processor, model


class ImageCaptioner:
    def __init__(self, device: Optional[str] = None):
        # device can be "cpu" or e.g. "cuda:0"
        self.device = device
        self._processor = None
        self._model = None

    def _ensure_model(self):
        if self._processor is None or self._model is None:
            processor, model = _load_blip_model()
            # move to device if needed
            try:
                import torch
                if self.device is None:
                    # choose CUDA if available
                    self.device = "cuda" if torch.cuda.is_available() else "cpu"
                # prefer specifying torch.device for clarity
                try:
                    torch_device = torch.device(self.device)
                except Exception:
                    torch_device = torch.device("cpu")
                model.to(torch_device)
                # record canonical device string
                self.device = str(torch_device)
            except Exception:
                # if torch import/move fails, continue and let model run on default
                pass

            self._processor = processor
            self._model = model

    def generate(self, image_path: str, prompt: Optional[str] = None, max_length: int = 100) -> str:
        """Generate caption / description for image_path."""
        self._ensure_model()
        processor = self._processor
        model = self._model

        try:
            from PIL import Image
            import torch
        except Exception as e:
            raise HFModelLoadError("Missing dependency: pillow or torch") from e

        image = Image.open(image_path).convert("RGB")

        # processor handles prompts; if prompt is None, pass empty string
        inputs = processor(images=image, text=prompt or "", return_tensors="pt")

        # move tensors to device if model on GPU
        try:
            device = next(model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
        except Exception:
            pass

        out = model.generate(**inputs, max_length=max_length)
        description = processor.decode(out[0], skip_special_tokens=True)
        return description
