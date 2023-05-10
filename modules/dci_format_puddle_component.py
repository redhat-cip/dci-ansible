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
from six.moves.urllib.parse import urlparse

import StringIO
import yaml

try:
    import requests
except ImportError:
    requests_found = False
else:
    requests_found = True

try:  # py27
    import ConfigParser as configparser
except ImportError:
    import configparser

DOCUMENTATION = '''
---
module: dci_format_puddle_component
short_description: module to format the puddle output
description:
  - DCI module to manage the dci puddle component
version_added: 2.2
options:
  state:
    required: false
    description: Desired state of the resource
  url:
    required: true
    description: URL to parse
'''

EXAMPLES = '''
- name: Format puddle component
  dci_format_puddle_component:
    url: 'https://url/mypuddle.repo'
'''

# TODO
RETURN = '''
'''


def get_data(type, repo_name, version, base_url, section_name,
             raw_base_url):
    """Return data. """

    data = {
        'path': urlparse(base_url).path,
        'version': version,
        'dlrn': {
            'commit_hash': None,
            'distro_hash': None,
            'commit_branch': None,
        }
    }

    if 'puddle_osp' in type:
        data['repo_name'] = repo_name
        osp_version = section_name.split('-')[-1]
        commit_information_file_path = '%s/import_data/commit.yaml' % \
            '/'.join(raw_base_url.split('/')[0:-3])
    elif type == 'snapshot_rdo':
        data['repo_name'] = repo_name
        commit_information_file_path = '%s/commit.yaml' % raw_base_url

    if ('puddle_osp' in type and float(osp_version) >= 10.0) or \
       type == 'snapshot_rdo':
        commit_information = yaml.load(requests.get(
            commit_information_file_path).text
        )
        first_commit = commit_information['commits'][0]
        data['dlrn']['commit_hash'] = first_commit['commit_hash']
        data['dlrn']['distro_hash'] = first_commit['distro_hash']
        data['dlrn']['commit_branch'] = first_commit['commit_branch']

    return data


def get_repo_information(url, type):
    repo_file_obj = requests.get(url)
    repo_file = repo_file_obj._content
    output = StringIO.StringIO(repo_file)
    config = configparser.ConfigParser()
    config.readfp(output)
    # we only use the first section
    section_name = config.sections()[0]
    raw_base_url = config.get(section_name, 'baseurl')
    base_url = raw_base_url.replace("$basearch", "x86_64")
    try:
        version = config.get(section_name, 'version')
    except configparser.NoOptionError:
        # extracting the version from the URL
        if 'puddle_osp' in type:
            version = base_url.split('/')[-4]
        elif type == 'snapshot_rdo':
            version = base_url.split('/')[-1]
    repo_name = config.get(section_name, 'name')

    component_informations = {
        'version': version,
        'display_name': repo_name,
        'url': base_url,
        'data': get_data(
            type, repo_name, version, base_url, section_name,
            raw_base_url
        ),
    }

    return component_informations


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                default='present',
                choices=['present', 'absent'],
                type='str'),
            url=dict(required=True, type='str'),
            type=dict(required=True, type='str')
        ),
    )

    if not requests_found:
        module.fail_json(msg='The python requests module is required')

    information = get_repo_information(module.params['url'],
                                       module.params['type'])
    puddle_component = {
        'version': information['version'],
        'display_name': information['display_name'],
        'url': information['url'],
        'data': information['data'],
        'changed': False
    }

    module.exit_json(**puddle_component)


if __name__ == '__main__':
    main()
