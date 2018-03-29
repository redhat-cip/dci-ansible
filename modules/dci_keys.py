#!/usr/bin/python
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
from ansible.module_utils.common import *
from ansible.module_utils.dci_base import *

try:
    from dciclient.v1.api import remoteci as dci_remoteci
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_keys
short_description: An ansible module to interact with the /remotecis/keys endpoint of DCI
version_added: 2.2
options:
  state:
    required: false
    description: Desired state of the resource

'''

# TODO
RETURN = '''
'''

class DciKeys(DciBase):

    def __init__(self, params):
        super(DciKeys, self).__init__(dci_remoteci)
        self.remoteci_id = params.get('remoteci_id')


    def do_refresh(self, context):
        rci = dci_remoteci.get(context, self.remoteci_id).json()
        res = dci_remoteci.refresh_keys(context,
                                        id=self.remoteci_id,
                                        etag=rci['remoteci']['etag'])

        if res.status_code == 201:
            return res.json()['keys']
        else:
            self.raise_error(res)


def main():

    resource_argument_spec = dict(
        remoteci_id=dict(type='str')
    )
    resource_argument_spec.update(authentication_argument_spec())

    module = AnsibleModule(
        argument_spec=resource_argument_spec,
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    context = build_dci_context(module)

    key = DciKeys(module.params)

    func = getattr(key, "do_refresh")

    result = run_action_func(func, context, module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
