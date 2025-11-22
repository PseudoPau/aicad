def validate_config(config_json):
    """
    简单校验仓库参数结构和类型，可扩展为pydantic等
    """
    if not isinstance(config_json, dict):
        raise ValueError("Config must be a dict")
    if "warehouse_config" not in config_json or "racking_system" not in config_json:
        raise ValueError("Missing required keys in config")
    # 可扩展更多字段和类型校验
    return True
