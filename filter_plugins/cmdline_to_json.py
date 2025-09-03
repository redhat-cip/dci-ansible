from json import dumps


def cmdline_to_json(cmdline=""):
    kernel = {}

    for item in cmdline.split():
        if "=" in item:
            k, v = item.split("=", 1)
            # Handle comma-separated values for specific keys
            if "," in v and k not in ["BOOT_IMAGE"]:
                v = v.split(",")
        else:
            k = item
            v = ""

        # Handle nested keys - any key with dots creates nested structure
        if "." in k:
            parts = k.split(".")
            current = kernel
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = v
        else:
            kernel[k] = v

    return dumps(kernel)


class FilterModule(object):
    def filters(self):
        return {"cmdline_to_json": cmdline_to_json}
