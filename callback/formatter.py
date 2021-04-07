def remove_duplicated_content(result):
    try:
        new_result = dict(result)
        duplicated_keys = (
            (
                "stdout",
                "stdout_lines",
            ),
            (
                "stderr",
                "stderr_lines",
            ),
        )
        for keys in duplicated_keys:
            key_to_keep = keys[0]
            key_to_remove = keys[1]
            if key_to_keep in new_result and key_to_remove in new_result:
                del new_result[key_to_remove]

        return new_result
    except:  # noqa
        return result
