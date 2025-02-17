#!/usr/bin/env python3
#
# Copyright (C) 2025 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

'''
Generate Markdown documentation from DCI modules.

DCI Ansible modules have 2 variables: DOCUMENTATION and EXAMPLES that are triple single quoted. These variables are used to generate the documentation. They are YAML formatted. The DOCUMENTATION variable contains the module name, description, options, and other information. The EXAMPLES variable contains example usage of the module.
'''

import re
import sys
import yaml


def generate_markdown_docs(module_path, output_file):
    """Generate Markdown documentation from DCI modules."""

    with open(output_file, "w") as f:
        with open(module_path) as module_file:
            module_data = module_file.read()
            documentation = re.search(
                r"DOCUMENTATION = '''\n(.*?)\n'''", module_data, re.DOTALL
            ).group(1)
            examples = re.search(
                r"EXAMPLES = '''\n(.*?)\n'''", module_data, re.DOTALL
            ).group(1)
            # parse as YAML
            doc = yaml.safe_load(documentation)
            # write the documentation
            f.write(f"# {doc['module']} module\n\n")
            desc = '\n'.join(doc['description'])
            f.write(f"{desc}\n\n")
            f.write("## Options\n\n")
            f.write("| Parameter | Required | Default | Description |\n")
            f.write("| --------- | -------- | ------- | ----------- |\n")
            options = doc["options"]
            for name in sorted(options.keys()):
                param = options[name]
                f.write(
                    f"| {name} | {param.get('required', 'false')} | {param.get('default', '')} | {param['description']} |\n"
                )
            f.write("\n")
            f.write("## Examples\n\n")
            f.write("```yaml\n")
            f.write(examples)
            f.write("\n```\n")
            print(f"  * [{doc['module']}: {doc['short_description']}]({output_file})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <module_path> <output_file>")
        sys.exit(1)

    generate_markdown_docs(sys.argv[1], sys.argv[2])

# generate_doc.py ends here
