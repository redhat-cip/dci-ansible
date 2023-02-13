from callback.dci import CallbackModule
from ansible import constants as C


def test_banner_success():
    cb = CallbackModule()
    cb.banner("a message")

    assert (cb._name == "a message")


def test_banner_error():

    class MyCallback(CallbackModule):
        def __init__(self):
            super(CallbackModule, self).__init__()
            self._color = C.COLOR_ERROR
            self._name = 'a_name'
            self._content = 'this is the content'
            self.filename = ""

        def create_file(self, name, content):
            self.filename = name

    cb = MyCallback()
    cb.banner("a message")

    assert (cb.filename == "failed/a_name")


def test_banner_error_loop():

    class MyCallback(CallbackModule):
        def __init__(self):
            super(CallbackModule, self).__init__()
            self._color = C.COLOR_CHANGED
            self._name = 'a_name'
            self._content = """changed: [localhost] => (item=file1)
changed: [localhost] => (item=file2)
failed: [localhost] (item=file3) => {"ansible_loop_var": "item", "changed": true, "cmd": "stat /tmp/file3.txt", "delta": "0:00:00.002938", "end": "2023-02-10 15:03:46.552211", "item": "file3", "msg": "non-zero return code", "rc": 1, "start": "2023-02-10 15:03:46.549273", "stderr": "stat: cannot statx '/tmp/file3.txt': No such file or directory", "stderr_lines": ["stat: cannot statx '/tmp/file3.txt': No such file or directory"], "stdout": "", "stdout_lines": []}
changed: [localhost] => (item=file4)
changed: [localhost] => (item=file5)"""
            self.filename = ""

        def create_file(self, name, content):
            self.filename = name

    cb = MyCallback()
    cb.banner("a message")

    assert (cb.filename == "failed/a_name")
