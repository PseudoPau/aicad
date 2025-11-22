import json
from openai import OpenAI

def get_ai_parameters(api_key, base64_image, user_prompt):
    """
    调用OpenAI接口，返回仓库参数JSON
    """
    client = OpenAI(api_key=api_key)
    system_prompt = """
    You are an Industrial AI Expert. Analyze the user's warehouse image.
    Output ONLY a valid JSON object matching this exact schema (no markdown, no comments):
    {
      "warehouse_config": {
        "overall_layout": { "rows": "int (count of racks)", "row_spacing": "float (mm)" }
      },
      "racking_system": {
        "dimensions": { "bay_width": "float", "bay_depth": "float", "total_height": "float" },
        "structure": { "levels": "int", "first_beam_height": "float" },
        "components": { "upright_color": "string (blue/orange/gray)", "beam_color": "string", "has_decking": "bool" }
      }
    }
    Estimate dimensions based on standard industrial pallets (1.2m x 1.0m) if not specified.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        response_format={ "type": "json_object" },
        temperature=0.1
    )
    return json.loads(response.choices[0].message.content)
