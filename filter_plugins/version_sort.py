from distutils.version import LooseVersion


def version_sort(versions):
    return sorted(versions, key=LooseVersion)


class FilterModule(object):
    def filters(self):
        return {"version_sort": version_sort}
