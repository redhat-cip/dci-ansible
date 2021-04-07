from module_utils.dci_formatter import remove_duplicated_content


def test_remove_duplicated_content_with_shell_command():
    result = {
        "stderr_lines": [],
        "cmd": "/bin/dci-downloader RHEL-8-nightly /var/www/html --arch x86_64 --variant BaseOS --variant AppStream",
        "end": "2021-03-04 21:51:31.753488",
        "_ansible_no_log": False,
        "_ansible_delegated_vars": {
            "ansible_port": None,
            "ansible_host": "10.245.100.47",
            "ansible_user": "root",
        },
        "changed": True,
        "rc": 0,
        "stdout": "Download component RHEL-8.4.0-20210301.n.0\nDownload DCI file list, it may take a few seconds\nComponent size 0 GB\nFree space 646 GB\nDownload component hwcert-1614270265\nDownload DCI file list, it may take a few seconds\nComponent size 0 GB\nFree space 646 GB",
        "start": "2021-03-04 21:27:25.005982",
        "stderr": "",
        "delta": "0:24:06.747506",
        "invocation": {
            "module_args": {
                "creates": None,
                "executable": None,
                "_uses_shell": True,
                "strip_empty_ends": True,
                "_raw_params": "/bin/dci-downloader RHEL-8-nightly /var/www/html --arch x86_64 --variant BaseOS --variant AppStream",
                "removes": None,
                "argv": None,
                "warn": True,
                "chdir": None,
                "stdin_add_newline": True,
                "stdin": None,
            }
        },
        "stdout_lines": [
            "Download component RHEL-8.4.0-20210301.n.0",
            "Download DCI file list, it may take a few seconds",
            "Component size 0 GB",
            "Free space 646 GB",
            "Download component hwcert-1614270265",
            "Download DCI file list, it may take a few seconds",
            "Component size 0 GB",
            "Free space 646 GB",
        ],
    }
    cleaned_content = remove_duplicated_content(result)
    assert "stdout_lines" not in cleaned_content
    assert "stderr_lines" not in cleaned_content


def test_remove_duplicated_content_with_dci_module_command():
    result = {
        "jobstate": {
            "comment": None,
            "created_at": "2021-04-07T07:50:37.131485",
            "id": "6d0fca4a-c4e6-49d1-9956-dfe09e2b7108",
            "job_id": "254aa9a7-6e8d-4117-a1de-8076aa930d7b",
            "status": "new",
        },
        "changed": True,
        "invocation": {
            "module_args": {
                "id": "254aa9a7-6e8d-4117-a1de-8076aa930d7b",
                "status": "new",
                "state": "present",
                "topic": None,
                "comment": None,
                "tags": None,
                "upgrade": None,
                "update": None,
                "components": None,
                "components_by_query": None,
                "team_id": None,
                "embed": None,
                "where": None,
                "get": None,
                "dci_login": None,
                "dci_password": None,
            }
        },
        "_ansible_no_log": False,
    }
    cleaned_content = remove_duplicated_content(result)
    assert cleaned_content == result


def test_remove_duplicated_content_return_original_result_if_not_dict_but_jsonifiable():
    result = ["I'm json dumps valid"]
    cleaned_content = remove_duplicated_content(result)
    assert cleaned_content == result
