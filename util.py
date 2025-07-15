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

def find_key_value(nested_dict, target_key):
    """Return the value with target_key within nested dictionary"""
    for key, value in nested_dict.items():
        if key == target_key:
            return value
        elif isinstance(value, dict):
            result = find_key_value(value, target_key)
            if result is not None:
                return result
    return None

def find_dict_with_key(nested_dict, target_key):
    """Find the key within nested dictionary, if found return the dictionary"""
    if target_key in nested_dict:
        return nested_dict
    for key, value in nested_dict.items():
        if isinstance(value, dict):
            result = find_dict_with_key(value, target_key)
            if result is not None:
                return result
    return None

def update_or_insert_key(d, target_key, new_key, new_value):
    """Update new value of key or insert a new key with new value"""
    if isinstance(d, dict):
        for k, v in d.items():
            if k == target_key:
                d[new_key] = new_value
                return True  # Inserted successfully
            elif isinstance(v, dict):
                if update_or_insert_key(v, target_key, new_key, new_value):
                    return True
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        if update_or_insert_key(item, target_key, new_key, new_value):
                            return True
    return False  # Target key not found

