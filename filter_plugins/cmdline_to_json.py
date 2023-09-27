from json import dumps


def cmdline_to_json(cmdline=""):
    kernel = {}
    for item in cmdline.split():
        if "=" in item:
            k, v = item.split("=", 1)
            if "," in v and k != "BOOT_IMAGE":
                v = v.split(",")
        else:
            k = item
            v = ""

        kernel[k] = v

    return dumps(kernel)


class FilterModule(object):
    def filters(self):
        return {"cmdline_to_json": cmdline_to_json}
