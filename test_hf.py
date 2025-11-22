# test_hf.py
from ai_analyzer import ImageCaptioner

print("Instantiating ImageCaptioner (no model yet)...")
c = ImageCaptioner()
print("captioner.device (before):", c.device)

# 触发模型加载并显示设备；替换下面的路径为你本地一张小图片路径
image_path = "path\\to\\a_small_image.jpg"  # 修改为真实文件路径

try:
    print("Calling generate(...) to load model and run one caption (this may download model and take a while)...")
    text = c.generate(image_path, prompt="Describe the image briefly", max_length=50)
    print("Generated text (first 300 chars):")
    print(text[:300])
except Exception as e:
    print("generate() failed (error):", e)

print("captioner.device (after):", c.device)