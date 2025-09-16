def dot_to_underscore(data):
    """
    Transform all keys and sub-keys of a dictionary by changing '.' to '_'.
    Leaves/values are not modified.

    Args:
        data: Dictionary or any data structure to transform

    Returns:
        Transformed data structure with keys having dots replaced by underscores
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Replace dots with underscores in the key
            new_key = key.replace('.', '_')
            # Recursively transform the value
            result[new_key] = dot_to_underscore(value)
        return result
    elif isinstance(data, list):
        # Handle lists by transforming each item
        return [dot_to_underscore(item) for item in data]
    else:
        # Return leaves/values unchanged
        return data


class FilterModule(object):
    def filters(self):
        return {"dot_to_underscore": dot_to_underscore}
