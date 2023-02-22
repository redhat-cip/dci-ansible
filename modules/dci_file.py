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
from ansible.module_utils.dci_base import *
import os

try:
    from dciclient.v1.api import file as dci_file
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_file
short_description: module to interact with the files endpoint of DCI
description:
  - DCI module to manage the file resources
version_added: 2.2
options:
  state:
    required: false
    description: Desired state of the resource
  dci_login:
    required: false
    description: User's DCI login
  dci_password:
    required: false
    description: User's DCI password
  dci_cs_url:
    required: false
    description: DCI Control Server URL
  job_id:
    required: false
    description: ID of the job to attach the file to
  jobstate_id:
    required: false
    description: ID of the jobstate to attach the file to
  mime:
    required: false
    default: text/plain
    description: mime-type of the document to upload
  path:
    required: true
    description: Path of the document to upload
  name:
    required: false
    description: Name under which the file will be saved on the control-server
  content:
    required: false
    description: Contentn of the file to upload
  embed:
    required: false
    description:
      - List of field to embed within the retrieved resource
  query:
    required: false
    description: query language
'''

EXAMPLES = '''
- name: Attach files to job
  dci_file:
    job_id: '{{ job_id }}'
    path: '{{ item.path }}'
    name: '{{ item.name }}'
  with_items:
    - {'name': 'SSHd config', 'path': '/etc/ssh/sshd_config'}
    - {'name': 'My OpenStack config', 'path': '/etc/myown.conf'}


- name: Get file information
  dci_file:
    id: XXXXX


- name: Attach content to a file to a job
  dci_file:
    job_id: '{{ job_id }}'
    content: 'This is the content of the file I want to create'
    name: 'My test file'


- name: Remove file
  dci_file:
    state: absent
    id: XXXXX


- name: Attach junit result
  dci_file:
    path: '{{ item }}'
    job_id: '{{ job_id }}'
    mime: 'application/junit'
  with_items:
    - '/tmp/result.xml'
'''

# TODO
RETURN = '''
'''


class DciFile(DciBase):

    def __init__(self, params):
        super(DciFile, self).__init__(dci_file)
        self.id = params.get('id')
        self.content = params.get('content')
        self.path = params.get('path')
        self.file_path = params.get('path')
        self.name = params.get('name')
        self.job_id = params.get('job_id')
        self.jobstate_id = params.get('jobstate_id')
        self.mime = params.get('mime')
        self.search_criterias = {
            'embed': params.get('embed'),
            'where': params.get('where'),
            'query': params.get('query')
        }
        self.deterministic_params = ['name', 'mime', 'file_path', 'content',
                                     'job_id', 'jobstate_id']

    def do_create(self, context):
        if not self.job_id and not self.jobstate_id:
            raise DciParameterError(
                'Either job_id or jobstate_id must be specified')
        if not self.content and not self.path:
            raise DciParameterError(
                'Either content or path must be specified')
        if self.content and not self.name:
            raise DciParameterError(
                'name parameter must be specified ',
                'when content has been specified')

        if self.path and not self.name:
            self.name = self.path

        if self.path and not os.path.exists(self.path):
            raise DciParameterError('%s: No such file' % self.path)

        return super(DciFile, self).do_create(context)

    def do_delete(self, context):
        return self.resource.delete(context, self.id)


def main():

    resource_argument_spec = dict(
        state=dict(default='present',
                   choices=['present', 'absent'],
                   type='str'),
        id=dict(type='str'),
        content=dict(type='str'),
        path=dict(type='str'),
        name=dict(type='str'),
        job_id=dict(type='str'),
        jobstate_id=dict(type='str'),
        mime=dict(default='text/plain', type='str'),
        embed=dict(type='str'),
        where=dict(type='str'),
        query=dict(type='str')
    )
    resource_argument_spec.update(authentication_argument_spec())

    module = AnsibleModule(
        argument_spec=resource_argument_spec,
        required_if=[['state', 'absent', ['id']]],
        mutually_exclusive=[['content', 'path']],
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    context = build_dci_context(module)
    action_name = get_standard_action(module.params)

    l_file = DciFile(module.params)
    action_func = getattr(l_file, 'do_%s' % action_name)

    http_response = run_action_func(action_func, context, module)
    result = parse_http_response(http_response, dci_file, context, module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
