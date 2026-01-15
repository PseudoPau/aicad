import json
import os
from jsonschema import validate, ValidationError, SchemaError

def validate_cad_data(instance_path, schema_path):
    """
    核心验证函数：比较 Agent 输出的 JSON 与 技术协议 Schema
    """
    # 1. 检查物理文件是否存在
    if not os.path.exists(schema_path):
        print(f"❌ 错误：找不到 Schema 协议文件: {schema_path}")
        return False
    if not os.path.exists(instance_path):
        print(f"❌ 错误：找不到待测数据文件: {instance_path}")
        return False

    try:
        # 2. 加载协议与数据
        with open(schema_path, 'r', encoding='utf-8') as s_file:
            schema = json.load(s_file)
        with open(instance_path, 'r', encoding='utf-8') as i_file:
            instance = json.load(i_file)

# 3. 执行比较验证
        # 这是 Agent 1 (视觉提取) 与 Agent 2 (逻辑映射) 之间的关键屏障
        validate(instance=instance, schema=schema)
        
        # 提取元数据用于打印显示
        metadata = instance.get('metadata', {})
        project_name = metadata.get('project_name', '未命名项目')
        
        print("-" * 50)
        print("✅ 验证通过：数据结构符合 AI CAD 协议规范。")
        print(f"项目名称: {project_name}")
        print(f"组件数量: {len(instance.get('components', []))}")
        print("-" * 50)
        return True

    except ValidationError as e:
        print("-" * 50)
        print("❌ 验证失败：AI 输出的数据与协议冲突！")
        # 精准定位错误位置，方便你调试 Agent 的 Prompt
        error_path = " -> ".join([str(p) for p in e.path])
        print(f"错误位置: {error_path}")
        print(f"详细原因: {e.message}")
        print("-" * 50)
        return False
    except SchemaError as e:
        print(f"❌ 协议文件本身存在语法错误: {e.message}")
        return False
    except json.JSONDecodeError:
        print("❌ 错误：JSON 文件格式损坏，无法解析。")
        return False

if __name__ == "__main__":
    # 执行握手测试
    # 默认路径指向你之前的标准文件
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    DEFAULT_SCHEMA = os.path.join("schema", "assembly_schema.json")
    DEFAULT_INSTANCE = os.path.join("tests", "shelf_instance.json")
    
    validate_cad_data(DEFAULT_INSTANCE, DEFAULT_SCHEMA)