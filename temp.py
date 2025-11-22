"""
图片分析器 - 

支持的方案：
1. 智谱 AI GLM-4V（推荐，在线 API，识别能力强）
2. 硅基流动 Qwen2-VL（开源模型，便宜，计数准确）
3. Ollama + LLaVA（本地运行）
4. Hugging Face Transformers（BLIP，基础功能）
"""

import base64
import requests
import json
from pathlib import Path
import os


class ImageAnalyzer:
    """使用开源模型分析图片内容"""

    def __init__(self, method="zhipu", api_key=None):
        """
        初始化图片分析器

        Args:
            method: 使用的方法，可选:
                   - "zhipu": 智谱 AI GLM-4V（推荐，识别能力强）
                   - "siliconflow": 硅基流动 Qwen2-VL（开源，计数好）
                   - "ollama": Ollama 本地
                   - "huggingface": HF Transformers
            api_key: API 密钥（在线方案需要）
        """
        self.method = method
        self.api_key = api_key or os.getenv(f"{method.upper()}_API_KEY")

    def analyze_with_zhipu(self, image_path, prompt="请详细描述这张图片的内容"):
        """
        使用智谱 AI GLM-4V 模型分析图片（推荐，识别能力强）

        免费注册: https://open.bigmodel.cn/
        每月有免费额度，视觉理解能力强，适合计数和细节识别

        Args:
            image_path: 图片路径
            prompt: 提示词

        Returns:
            分析结果文本
        """
        if not self.api_key:
            return """
错误: 未设置 API Key

获取步骤（1分钟完成）:
1. 访问 https://open.bigmodel.cn/
2. 注册账号（手机号即可）
3. 进入"API Keys"页面创建密钥
4. 每月有免费额度，适合货架识别任务

使用方法:
analyzer = ImageAnalyzer(method="zhipu", api_key="你的密钥")
"""

        # 读取图片并转换为 base64
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "glm-4v",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                return "错误: API Key 无效，请检查密钥是否正确"
            return f"HTTP 错误: {e}\n响应: {response.text}"
        except Exception as e:
            return f"错误: {str(e)}"

    def analyze_with_siliconflow(self, image_path, prompt="请详细描述这张图片的内容"):
        """
        使用硅基流动 Qwen2-VL 模型分析图片（开源模型，计数准确）

        注册: https://siliconflow.cn/
        价格极低，使用 Qwen2-VL 开源模型，对中文和计数支持好

        Args:
            image_path: 图片路径
            prompt: 提示词

        Returns:
            分析结果文本
        """
        if not self.api_key:
            return """
错误: 未设置 API Key

获取步骤:
1. 访问 https://siliconflow.cn/
2. 注册账号
3. 获取 API Key
4. 价格极低，适合批量处理

使用方法:
analyzer = ImageAnalyzer(method="siliconflow", api_key="你的密钥")
"""

        # 读取图片并转换为 base64
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        url = "https://api.siliconflow.cn/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "Pro/Qwen/Qwen2-VL-7B-Instruct",  # Qwen2-VL 对计数和细节识别好
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "stream": False
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"错误: {str(e)}"

    def analyze_with_ollama(self, image_path, prompt="请详细描述这张图片的内容"):
        """
        使用 Ollama + LLaVA 模型分析图片

        需要先安装 Ollama:
        1. 下载: https://ollama.ai/download
        2. 运行: ollama pull llava

        Args:
            image_path: 图片路径
            prompt: 提示词

        Returns:
            分析结果文本
        """
        # 读取图片并转换为 base64
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # 调用 Ollama API
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llava",
            "prompt": prompt,
            "images": [image_data],
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

        except requests.exceptions.ConnectionError:
            return "错误: 无法连接到 Ollama。请确保已安装并运行 Ollama 服务。\n安装步骤:\n1. 访问 https://ollama.ai/download\n2. 安装后运行: ollama pull llava"
        except Exception as e:
            return f"错误: {str(e)}"

    def analyze_with_huggingface(self, image_path, prompt=None):
        """
        使用 Hugging Face Transformers 的 BLIP-2 模型分析图片

        需要安装: pip install transformers pillow torch

        Args:
            image_path: 图片路径
            prompt: 提示词（可选，留空则自动生成完整描述）

        Returns:
            分析结果文本
        """
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            from PIL import Image
            import torch

            print("正在加载模型（首次运行会下载模型，可能需要几分钟）...")

            # 加载模型和处理器
            processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
            model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

            # 读取图片
            image = Image.open(image_path).convert('RGB')

            print("正在分析图片...")

            if prompt:
                # 如果有提示词，使用条件生成（Visual Question Answering）
                inputs = processor(image, return_tensors="pt")
                # out = model.generate(**inputs, max_length=100, num_beams=5)
                out = model.generate(
                    **inputs,
                    max_length=100,           # 增加最大长度
                    # min_length=20,            # 设置最小长度，确保输出完整
                    # num_beams=5,              # 使用束搜索，提高质量
                    length_penalty=1.0,       # 长度惩罚
                    early_stopping=True,
                    temperature=1.0,
                    do_sample=True
                )
            else:
                # 无条件生成（Image Captioning）- 生成完整描述
                inputs = processor(image, return_tensors="pt")
                out = model.generate(
                    **inputs,
                    max_length=100,           # 增加最大长度
                    # min_length=20,            # 设置最小长度，确保输出完整
                    # num_beams=5,              # 使用束搜索，提高质量
                    length_penalty=1.0,       # 长度惩罚
                    early_stopping=True,
                    temperature=1.0,
                    do_sample=True
                )

            description = processor.decode(out[0], skip_special_tokens=True)

            return description

        except ImportError:
            return "错误: 缺少必要的库。请运行: pip install transformers pillow torch"
        except Exception as e:
            return f"错误: {str(e)}"

    def analyze_with_qwen_vl(self, image_path, prompt="请详细描述这张图片的内容"):
        """
        使用 Ollama + Qwen2-VL 模型分析图片（中文效果更好）

        需要先运行: ollama pull qwen2-vl

        Args:
            image_path: 图片路径
            prompt: 提示词

        Returns:
            分析结果文本
        """
        # 读取图片并转换为 base64
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # 调用 Ollama API
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "qwen2-vl",
            "prompt": prompt,
            "images": [image_data],
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

        except requests.exceptions.ConnectionError:
            return "错误: 无法连接到 Ollama。请运行: ollama pull qwen2-vl"
        except Exception as e:
            return f"错误: {str(e)}"

    def analyze(self, image_path, prompt=None):
        """
        分析图片内容

        Args:
            image_path: 图片路径
            prompt: 自定义提示词（可选）
                   - 对于货架识别，建议详细描述需求
                   - 例如："请仔细观察这个货架，告诉我：1. 有多少层 2. 每层的结构"

        Returns:
            分析结果文本
        """
        if not Path(image_path).exists():
            return f"错误: 图片文件不存在: {image_path}"

        # 如果没有提供 prompt，使用货架识别的默认提示词
        if prompt is None:
            prompt = """请仔细分析这张货架图片，重点关注：
1. 货架有多少层？（请数清楚水平的层板）
2. 每层的结构和特征
3. 货架的组装方式和部件（如立柱、层板、连接件等）
4. 任何可见的细节

请给出详细、准确的分析。"""

        print(f"使用方法: {self.method}")
        print(f"分析图片: {image_path}")
        print(f"提示词: {prompt}\n")

        if self.method == "zhipu":
            return self.analyze_with_zhipu(image_path, prompt)
        elif self.method == "siliconflow":
            return self.analyze_with_siliconflow(image_path, prompt)
        elif self.method == "ollama":
            return self.analyze_with_ollama(image_path, prompt)
        elif self.method == "qwen":
            return self.analyze_with_qwen_vl(image_path, prompt)
        elif self.method == "huggingface":
            return self.analyze_with_huggingface(image_path, prompt)
        else:
            return f"不支持的方法: {self.method}"


def main():
    """主函数 - 货架识别示例"""

    # 配置你的货架图片路径
    image_path = "./input_img/img_test_03.jpg"  # 修改为你的图片路径

    # ========== 方案1: 智谱 AI GLM-4V（推荐）==========
    # 识别能力强，适合计数和细节分析
    # 注册: https://open.bigmodel.cn/
    analyzer = ImageAnalyzer(
        method="zhipu", 
        api_key="c1a1c3a1ee394b4c88a2b138f2d01af6.GOiAiXgVVUsFbI7P"  # 替换为你的密钥
    )

    # ========== 方案2: 硅基流动 Qwen2-VL（开源模型，便宜）==========
    # Qwen2-VL 对计数和中文支持好
    # 注册: https://siliconflow.cn/
    # analyzer = ImageAnalyzer(
    #     method="siliconflow",
    #     api_key="你的API密钥"
    # )

    # ========== 方案3: 本地 Ollama（需下载 4GB）==========
    # analyzer = ImageAnalyzer(method="ollama")

    # 分析货架 - 自动使用优化的提示词
    result = analyzer.analyze(image_path=image_path)

    print("=" * 60)
    print("分析结果:")
    print("=" * 60)
    print(result)
    print("=" * 60)

    # 如果需要自定义提问：
    # result = analyzer.analyze(
    #     image_path=image_path,
    #     prompt="请告诉我这个货架有几层，每层之间的连接方式是什么？"
    # )


if __name__ == "__main__":
    # 安装说明
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║        货架智能识别系统 - 视觉模型分析                        ║
    ╚════════════════════════════════════════════════════════════╝

    🎯 任务目标: 识别货架层数、部件和组装方式

    ⭐ 方案 1: 智谱 AI GLM-4V（推荐）
    ----------------------------------------
    ✅ 优点: 识别能力强，计数准确，中文支持好
    📝 注册: https://open.bigmodel.cn/
    💰 费用: 有免费额度

    ⭐ 方案 2: 硅基流动 Qwen2-VL（开源模型）
    ----------------------------------------
    ✅ 优点: Qwen2-VL 对计数和细节识别好，价格低
    📝 注册: https://siliconflow.cn/
    💰 费用: 极低价格

    方案 3: Ollama 本地运行（需下载 4GB）
    -------------------------------------
    ✅ 优点: 完全本地，隐私安全
    ❌ 缺点: 需要下载模型
    📝 安装: ollama pull llava 或 ollama pull qwen2-vl

    ════════════════════════════════════════════════════════════
    💡 推荐: 智谱 AI 或硅基流动，识别准确，即刻可用！
    ════════════════════════════════════════════════════════════
    """)

    main()