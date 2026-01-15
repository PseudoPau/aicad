import json
import base64
import re
from zhipuai import ZhipuAI

class VisionAgent:
    def __init__(self, api_key):
        self.client = ZhipuAI(api_key=api_key)
        self.model = "glm-4v"

    def extract_params(self, image_path, schema_text, few_shot_text):
        """
        利用 GLM-4V 识别图片，并使用正则表达式强制提取合法 JSON
        """
        # 1. 图片 Base64 处理
        try:
            with open(image_path, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                img_base = f"data:image/jpeg;base64,{encoded_string}"
        except Exception as e:
            raise Exception(f"图片读取失败: {str(e)}")

        # 2. 强化 Prompt：明确 JSON 语法禁忌
        prompt = f"""
        你是一位精准的工业测量员。请根据照片内容提取货架几何参数。
        
        ### 任务核心：
        - 必须输出符合 RFC 8259 标准的合法 JSON。
        - 严禁包含注释、严禁使用单引号、严禁在最后一个元素后添加逗号。
        - 范例仅用于参考【键名】和【结构】，必须识别【图片中】的真实高度、宽度和层数。
        
        ### 约束规范 (Schema):
        {schema_text}
        
        ### 结构范例 (仅参考结构):
        {few_shot_text}
        
        ### 强制输出格式:
        直接以 {{ 开头，以 }} 结尾，中间不要有任何 Markdown 代码块标签或解释文字。
        """

        # 3. 发送请求
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": img_base}}
                    ]
                }
            ]
        )
        
        raw_content = response.choices[0].message.content

        # 4. 稳健提取逻辑：利用正则表达式匹配第一个 { 和最后一个 } 之间的内容
        try:
            # 查找大括号包裹的内容
            match = re.search(r'(\{.*\})', raw_content, re.DOTALL)
            if match:
                json_str = match.group(1)
                # 进一步清理可能存在的换行符或空格
                json_str = json_str.strip()
                return json.loads(json_str)
            else:
                raise ValueError("AI 返回的内容中未找到 JSON 结构")
        except json.JSONDecodeError as e:
            print(f"DEBUG: AI 返回的原始文字为:\n{raw_content}")
            raise Exception(f"JSON 解析失败，语法错误位置: {str(e)}")