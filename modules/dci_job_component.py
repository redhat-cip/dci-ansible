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

try:
    from dciclient.v1.api import job as dci_job
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_job_component
short_description: module to interact with the components of a job
description:
  - DCI module to interact with the components of a job
version_added: 2.2
options:
  state:
    required: false
    default: present
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
    required: true
    description: the job id
  component_id:
    required: true
    description: the component id
'''

EXAMPLES = '''
- name: Associate a component to a job
  dci_job_component:
    job_id: {{ job_id }}
    component_id: {{ component_id }}
'''

# TODO
RETURN = '''
'''


def main():

    resource_argument_spec = dict(
        state=dict(
            default='present',
            choices=['present'],
            type='str'),
        job_id=dict(type='str', required=True),
        component_id=dict(type='str', required=True)
    )
    resource_argument_spec.update(authentication_argument_spec())

    module = AnsibleModule(
        argument_spec=resource_argument_spec
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = build_dci_context(module)
    job_id = module.params['job_id'].strip()
    component_id = module.params['component_id'].strip()

    res = dci_job.add_component(ctx, job_id, component_id)

    result = {'changed': False}
    if res.status_code in (201, 409):
        result = {
            'component_id': component_id,
            'job_id': job_id,
            'changed': True
        }
    else:
        module.fail_json(msg=res.text)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
