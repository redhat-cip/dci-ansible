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

import os

try:
    from dciclient.v1.api import context as dci_context
    from dciclient.v1.api import job as dci_job
    from dciclient.v1.api import remoteci as dci_remoteci
    from dciclient.v1.api import topic as dci_topic
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_job
short_description: An ansible module to interact with the /jobs endpoint of DCI
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
  id:
    required: false
    description: ID of the job
  comment:
    required: false
    description: Comment attached to the job
  status:
    required: false
    description: Status the job should be entitled
  metadata:
    required: false
    description: Metadatas attached to the job
  upgrade:
    required: false
    description: Schedule an upgrade job
  components:
    required: false
    description: list of ID to associated to the new job
  team_id:
    required: false
    description: team of the new job
  embed:
    required: false
    description:
      - List of field to embed within the retrieved resource
  where:
    required: false
    description: Specific criterias for search
'''

EXAMPLES = '''
- name: Schedule a new job
  dci_job:
    topic: 'OSP10'

- name: Update job
  dci_job:
    id: '{{ job_id }}'
    comment: 'New comment for my job'

- name: Remove a job
  dci_job:
    state: absent
    id: '{{ job_id }}'

- name: Schedule an upgrade job
  dci_job:
    id: '{{ job_id }}'
    upgrade: true

- name: Manually create a job
  dci_job:
    topic: 'OSP8'
    comment: 'job created manually'
    components: ['4c282108-5086-454b-8d49-4b1d0345acd9', '4c8ec5c8-ec24-4253-abbf-63a4daddba8b']

 - name: Notify for a specific reason
   dci_job:
     notify: "Specific comment"
'''

# TODO
RETURN = '''
'''


class DciJob(DciBase):

    def __init__(self, params):
        super(DciJob, self).__init__(dci_job)
        self.id = params.get('id')
        self.topic = params.get('topic')
        self.comment = params.get('comment')
        self.status = params.get('status')
        self.metadata = params.get('metadata')
        self.notify = params.get('notify')
        self.upgrade = params.get('upgrade')
        self.components = params.get('components')
        self.team_id = params.get('team_id')
        self.search_criterias = {
            'embed': params.get('embed'),
            'where': params.get('where')
        }
        self.deterministic_params = ['topic', 'comment', 'status',
                                     'metadata', 'team_id']

    def do_notify(self, context):
        return dci_job.notify(context, context.last_job_id, mesg=self.notify)

    def do_upgrade(self, context):
        res = dci_job.upgrade(context, job_id=self.id)

        if res.status_code == 201:
            return dci_job.get_full_data(context, context.last_job_id)
        else:
            self.raise_error(res)

    def do_schedule(self, context):
        topic_res = dci_topic.list(context, where='name:' + self.topic)

        if topic_res.status_code == 200:
            topics = topic_res.json()['topics']
            if not len(topics):
                raise DciResourceNotFoundException(
                    'Topic: %s resource not found' % self.name
                )

            topic_id = topics[0]['id']
            res = dci_job.schedule(
                context, remoteci_id=context.session.auth.client_id,
                topic_id=topic_id
            )
            if res.status_code == 201:
                return dci_job.get_full_data(context, context.last_job_id)
            else:
                self.raise_error(res)

        else:
            self.raise_error(res)

    def do_create(self, context):
        topic_res = dci_topic.list(context, where='name:' + self.topic)

        if topic_res.status_code == 200:
            topics = topic_res.json()['topics']
            if not len(topics):
                raise DciResourceNotFoundException(
                    'Topic: %s resource not found' % self.name
                )

            topic_id = topics[0]['id']

            res = dci_job.create(
                context, remoteci_id=context.session.auth.client_id,
                team_id=self.team_id, topic_id=topic_id,
                components=self.components, comment=self.comment
            )
            if res.status_code == 201:
                return dci_job.get_full_data(context, context.last_job_id)
            else:
                self.raise_error(res)

        else:
            self.raise_error(res)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            # Authentication related parameters
            #
            dci_login=dict(required=False, type='str'),
            dci_password=dict(required=False, type='str', no_log=True),
            dci_cs_url=dict(required=False, type='str'),
            dci_client_id=dict(required=False, type='str'),
            dci_api_secret=dict(required=False, type='str', no_log=True),
            # Resource related parameters
            #
            id=dict(type='str'),
            topic=dict(required=False, type='str'),
            comment=dict(type='str'),
            status=dict(type='str'),
            metadata=dict(type='dict'),
            notify=dict(type='dict'),
            upgrade=dict(type='bool'),
            components=dict(type='list', default=[]),
            team_id=dict(type='str'),
            embed=dict(type='list'),
            where=dict(type='str'),
        ),
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    context = build_dci_context(module)
    action_name = get_standard_action(module.params)
    open('/tmp/aguenane', 'w').write(action_name)
    if action_name == 'update':
        if module.params['notify']:
            action_name = 'notify'
        elif module.params['upgrade']:
            action_name = 'upgrade'

    elif action_name == 'create':
        if not module.params['components']:
            action_name = 'schedule'

    job = DciJob(module.params)
    action_func = getattr(job, 'do_%s' % action_name)

    http_response = run_action_func(action_func, context, module)
    result = parse_http_response(http_response, dci_job, context, module)

    if action_name in ['schedule', 'create']:
        result['job_id'] = context.last_job_id
        for k, v in result['job'].items():
            result[k] = v

    module.exit_json(**result)


if __name__ == '__main__':
    main()
