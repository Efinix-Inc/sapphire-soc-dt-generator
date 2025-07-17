import os
import json
import sys

def print_node(node):
    print(json.dumps(node, indent=2, sort_keys=False))

def read_file(filename):
    raw_configs = {}
    if not os.path.exists(filename):
        print(f"Error: No such file '{filename}'")
        sys.exit(1)

    with open(filename, "r") as f:
        raw_configs = f.read()

    return raw_configs

def read_json_file(filename):
    if not os.path.exists(filename):
        print(f"Error: No such file '{filename}'")
        sys.exit(1)

    with open(filename, "r") as f:
        return json.load(f)

def save(filename, content, json_format=True):
    with open(filename, "w") as f:
        if json_format:
            json.dump(content, f, indent=4, sort_keys=False)
        else:
            f.write(content)

def merge_json_files(file_paths):
    merge_data = {}
    for file_path in file_paths:
        content = read_json_file(file_path)
        merge_data = merge_dicts(merge_data, content)

    return merge_data

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

def merge_dicts(d1, d2):
    """Merge two dictionaries.
    If a key exists in both and the values are dicts, merge them resursively.
    If a key exists in both and the values are not dicts, replace the value from the second dictionary.
    If a key ends with "_append" in one dictionary, append the values (assuming they are lists or strings).
    """
    result = dict(d1)  # Start with a copy of d1

    for key, value in d2.items():
        if key.endswith("_append"):
            base_key = key[:-7]
            if base_key in result:
                if isinstance(result[base_key], list) and isinstance(value, list):
                    result[base_key] += value
                elif isinstance(result[base_key], str) and isinstance(value, str):
                    result[base_key] += value
                else:
                    result[base_key] = value  # fallback: replace
            else:
                result[base_key] = value
        elif key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value  # replace non-dict values
        else:
            result[key] = value  # new key

    return result

def convert_to_int(s):
    """Convert string to integer"""
    if isinstance(s, str) and s.startswith("0x"):
        return int(s, 16)
    else:
        return int(s)

def convert_to_hex(s):
    """Convert string to hex"""
    if isinstance(s, str):
        if s.startswith("0x"):
            value = int(s, 16)
        else:
            value = int(s)
    else:
        value = s # assume it's already an int

    return hex(value)
