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
import yaml

try:
    from dciclient.v1.api import context as dci_context
    from dciclient.v1.api import job as dci_job
    from dciclient.v1.api import jobstate as dci_jobstate
    from dciclient.v1.api import remoteci as dci_remoteci
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_jobstate
short_description: An ansible module to create jobstate
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
  topic:
    required: false
    description: Topic for which the job will be schedule
  remoteci:
    required: false
    description: RemoteCI for which the job will be schedule
  id:
    required: false
    description: ID of the jobstate
  comment:
    required: false
    description: The command to use for the new jobstate
  status:
    required: false
    description: Status the job should be entitled
  msg:
    required: false
    description: Alias for comment
  state:
    required: false
    description: State of the resource
  job_id:
    required: false
    description: The job_id of the jobstate
'''

EXAMPLES = '''
- dci_jobstate: msg='We will do something' status='pre-run'

- name: 'Delete a jobstate_id'
  dci_jobstate:
    id: 'foo'
    state: 'absent'

- name: 'Retrieve a jobstate'
  dci_jobstate:
    id: 'foo'
    state: 'present'

- name: 'List the jobstates of a given job_id'
  dci_jobstate:
    job_id: 'bar'

- name: 'Attach a jobstate to a job_id'
  dci_jobstate:
    msg: 'a message'
    job_id: 'bar'
'''

# TODO
RETURN = '''
'''


def get_config(module):
    from_file = {}
    if os.path.exists('/etc/dci/dci.yaml'):
        with open('/etc/dci/dci.yaml') as fd:
            from_file = yaml.load(fd)

    return {
        'login':
            module.params.get('dci_login')
            or os.getenv('DCI_LOGIN')
            or from_file.get('login'),
        'password':
            module.params.get('dci_password')
            or os.getenv('DCI_PASSWORD')
            or from_file.get('password'),
        'cs_url':
            module.params.get('dci_cs_url')
            or os.getenv('DCI_CS_URL')
            or from_file.get('cs_url')
            or 'https://api.distributed-ci.io',
        'remoteci':
            module.params.get('remoteci')
            or os.getenv('DCI_REMOTECI')
            or from_file.get('remoteci'),
        'topic':
            module.params.get('topic')
            or os.getenv('DCI_TOPIC')
            or from_file.get('topic')
        }


def main():
    module = AnsibleModule(
        argument_spec=dict(
            msg=dict(
                aliases=['comment'],
                type='str',
                required=False),
            status=dict(
                choices=[
                    'new', 'pre-run', 'running', 'post-run',
                    'success', 'failure'],
                type='str',
                required=False),
            state=dict(
                type='str',
                required=False),
            id=dict(
                type='str',
                required=False),
            job_id=dict(
                type='str',
                required=False),
        ),
    )
    config = get_config(module)

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    if not set(['login', 'password']).issubset(config):
        module.fail_json(msg='login and/or password have not been specified')

    ctx = dci_context.build_dci_context(
        config['cs_url'], config['login'],
        config['password'], 'Ansible')

    try:
        remoteci_id = dci_remoteci.list(
            ctx,
            where='name:' + config['remoteci'],
            limit=1).json()['remotecis'][0]['id']
    except KeyError:
        module.exit_json(msg='RemoteCI %s not found!' % config.get('remoteci'))



    if 'msg' in module.params:
        job_id = module.params.get('job_id')
        if not job_id:
            job_id = dci_job.list(
                ctx,
                where='remoteci_id:' + remoteci_id,
                limit=1).json()['jobs'][0]['id']
        res = dci_jobstate.create(
            ctx,
            status=module.params['status'],
            comment=module.params['msg'],
            job_id=job_id)
    elif set(['id', 'state']).issubset(module.params):
        if module.params['state'] == 'absent':
            res = dci_jobstate.delete(
                ctx,
                module.params['id'])
        else:
            res = dci_jobstate.get(
                ctx,
                module.params['id'])
    elif module.params.get('job_id'):
        res = dci_jobstate.list(
            ctx,
            where='jobid:' + module.params['job_id'])

    try:
        result = res.json()
        if res.status_code == 404:
            module.fail_json(msg='The resource does not exist')
        if res.status_code in [400, 401, 409]:
            result['changed'] = False
        else:
            result['changed'] = True
    except AttributeError:
        # Enter here if new job has been schedule, return of get_full_data is already json.
        result = res
        result['changed'] = True
        result['job_id'] = ctx.last_job_id
    except:
        result = {}
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
