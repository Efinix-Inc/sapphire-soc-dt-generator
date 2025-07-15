def find_dict_with_key_value(nested_dict, target_key, target_value):
    """Get the dictionary when supply key and value match within nested dictionary"""
    for key, value in nested_dict.items():
        if key == target_key and value == target_value:
            return nested_dict
        elif isinstance(value, dict):
            result = find_dict_with_key_value(value, target_key, target_value)
            if result is not None:
                return result
    return None

