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

import os
from dciclient.v1.api import context as dci_context
from dciclient.v1.api import job as dci_job
from dciclient.v1.api import remoteci as dci_remoteci
from dciclient.v1.api import topic as dci_topic

try:
    import requests
except ImportError:
    requests_found = False
else:
    requests_found = True


DOCUMENTATION = '''
---
module: dci_new_job
short_description: An ansible module to schedule a new job with DCI
version_added: 2.2
options:
  login:
    required: false
    description: User's DCI login
  password:
    required: false
    description: User's DCI password
  url:
    required: false
    description: DCI Control Server URL
  topic:
    required: false
    description: Topic's to get a job to
  remoteci:
    required: true
    description: RemoteCI to get a job for
'''

EXAMPLES = '''
- name: Schedule a new job for DCI
  dci_new_job:
    login: john.doe
    password: 4r4nd0mP4ss
    topic: RDO-Ocata
    remoteci: dci-env-ovb1

- name: Schedule a new job for DCI
  dci_new_job:
    topic: OSP-8
    remoteci: dci-env-ovb1
'''

# TODO
RETURN = '''
'''


def get_details(module):
    """Method that retrieves the appropriate credentials. """

    login_list = [module.params['login'], os.getenv('DCI_LOGIN')]
    login = next((item for item in login_list if item is not None), None)

    password_list = [module.params['password'], os.getenv('DCI_PASSWORD')]
    password = next((item for item in password_list if item is not None), None)

    url_list = [module.params['url'], os.getenv('DCI_CS_URL')]
    url = next((item for item in url_list if item is not None), 'https://api.distributed-ci.io')

    return login, password, url


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            login=dict(required=False, type='str'),
            password=dict(required=False, type='str'),
            topic=dict(required=False, type='str'),
            remoteci=dict(type='str'),
            url=dict(required=False, type='str'),
        ),
    )

    if not requests_found:
        module.fail_json(msg='The python requests module is required')

    topic_list = [module.params['topic'], os.getenv('DCI_TOPIC')]
    topic = next((item for item in topic_list if item is not None), None)

    login, password, url = get_details(module)
    if not login or not password:
        module.fail_json(msg='login and/or password have not been specified')

    ctx = dci_context.build_dci_context(url, login, password, 'ansible')

    topic_id = dci_topic.get(ctx, topic).json()['topic']['id']
    remoteci = dci_remoteci.get(ctx, module.params['remoteci']).json()
    remoteci_id = remoteci['remoteci']['id']

    dci_job.schedule(ctx, remoteci_id, topic_id=topic_id)
    jb = dci_job.get_full_data(ctx, ctx.last_job_id)
    jb['job_id'] = ctx.last_job_id

    module.exit_json(**jb)


if __name__ == '__main__':
    main()
