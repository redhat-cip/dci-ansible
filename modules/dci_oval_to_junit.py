# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ansible.module_utils.basic import *
from ansible.module_utils.dci_common import *

from xml.etree import ElementTree as et


DOCUMENTATION = '''
---
module: dci_oval_to_junit
short_description: module to convert oval file format to junit
description:
  - DCI module to convert oval file format to junit
version_added: 1.0
options:
  oval_result_src:
    required: true
    description: Oval file source path
  junit_dest:
    required: true
    description: Junit file destination path
'''

EXAMPLES = '''
- name: Convert oval file to junit file
  dci_oval_to_junit:
    oval_result_src: {{ oval_src_path }}
    junit_dest: {{ junit_dest_path }}
'''


oval_def_ns = "{http://oval.mitre.org/XMLSchema/oval-definitions-5}"
oval_results_ns = "{http://oval.mitre.org/XMLSchema/oval-results-5}"


def parse_oval_format(fd):
    oval_results = {}
    document = et.parse(fd)
    root = document.getroot()

    # get all oval_definitions
    definitions = root.find(f"{oval_def_ns}oval_definitions/{oval_def_ns}definitions")
    for d in definitions:
        oval_results[d.attrib["id"]] = {
            "id": d.attrib["id"],
            "version": d.attrib["version"],
            "class": d.attrib["class"],
        }
        metadata = d.find(f"{oval_def_ns}metadata")
        title = metadata.find(f"{oval_def_ns}title")
        oval_results[d.attrib["id"]]["title"] = title.text
        description = metadata.find(f"{oval_def_ns}description")
        oval_results[d.attrib["id"]]["description"] = description.text
        references = metadata.findall(f"{oval_def_ns}reference")
        for r in references:
            r_attribs = {
                "source": r.attrib["source"],
                "ref_id": r.attrib["ref_id"],
                "ref_url": r.attrib["ref_url"],
            }
            if "references" not in oval_results[d.attrib["id"]]:
                oval_results[d.attrib["id"]]["references"] = [r_attribs]
            else:
                oval_results[d.attrib["id"]]["references"].append(r_attribs)

    # get all results definition and agregate into oval_results
    results = root.find(f"{oval_results_ns}results")
    system = results.find(f"{oval_results_ns}system")
    definitions = system.find(f"{oval_results_ns}definitions")
    definition_results = definitions.findall(f"{oval_results_ns}definition")
    for dr in definition_results:
        if dr.attrib["definition_id"] in oval_results:
            oval_results[dr.attrib["definition_id"]]["result"] = dr.attrib["result"]
    return oval_results


def _nb_oval_failures(oval_results):
    nb_failures = 0
    for _, v in oval_results.items():
        if v["result"].lower() == "true":
            nb_failures += 1
    return nb_failures


def main():

    resource_argument_spec = dict(
        oval_result_src=dict(type="path", required=True),
        junit_dest=dict(type="path", required=True),
    )

    module = AnsibleModule(argument_spec=resource_argument_spec)

    oval_result_src = module.params["oval_result_src"]
    junit_dest = module.params["junit_dest"]

    result = {}
    result["changed"] = True

    try:
        with open(oval_result_src, "r") as ors_fd:
            oval_results = parse_oval_format(ors_fd)

            with open(junit_dest, "w") as jd_fd:
                jd_fd.write("<testsuites>\n")
                nb_tests = len(oval_results.keys())
                nb_failures = _nb_oval_failures(oval_results)
                jd_fd.write(
                    f'<testsuite tests="{nb_tests}" failures="{nb_failures}" name="Oval">\n'
                )
                for _, v in oval_results.items():
                    name = v["id"]
                    message = ""
                    for r in v["references"]:
                        message = (
                            message
                            + "ref_id: "
                            + r["ref_id"]
                            + "\n ref_url: "
                            + r["ref_url"]
                            + "\n source: "
                            + r["source"]
                            + "\n"
                        )
                    if v["result"].lower() == "false":
                        jd_fd.write(
                            f'<testcase classname="oval" name="{name}">\n{message}</testcase>\n'
                        )
                    if v["result"].lower() == "true":
                        jd_fd.write(
                            f'<testcase classname="oval" name="{name}"><failure message="{message}"></failure></testcase>\n'
                        )
                jd_fd.write("</testsuite>\n</testsuites>")
    except Exception as e:
        e_msg = str(e)
        module.fail_json(
            msg=f"error while parsing {oval_result_src} to generate junit at {junit_dest}: {e_msg}"
        )

    module.exit_json(**result)


if __name__ == "__main__":
    main()
