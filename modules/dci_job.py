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
    from dciclient.v1.api import job as dci_job
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
  update:
    required: false
    description: Schedule an update job
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

- name: Schedule an update job
  dci_job:
    id: '{{ job_id }}'
    update: true

- name: Manually create a job
  dci_job:
    topic: 'OSP8'
    comment: 'job created manually'
    components: ['4c282108-5086-454b-8d49-4b1d0345acd9', '4c8ec5c8-ec24-4253-abbf-63a4daddba8b']

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
        self.update = params.get('update')
        self.upgrade = params.get('upgrade')
        self.components = params.get('components', [])
        self.team_id = params.get('team_id')
        self.search_criterias = {
            'embed': params.get('embed'),
            'where': params.get('where')
        }
        self.deterministic_params = ['topic', 'comment', 'status',
                                     'metadata', 'team_id']

    def do_set_metadata(self, context):
        for k, v in self.metadata.items():
            res = dci_job.set_meta(context, self.id, k, str(v))
            if res.status_code != 201:
                self.raise_error(res)

        res = dci_job.list_metas(context, self.id)

        if res.status_code == 200 and res.json()['metas'] > 0:
            return dci_job.get(context, self.id, embed='metas')
        else:
            self.raise_error(res)

    def do_job_update(self, context):
        res = dci_job.job_update(context, job_id=self.id)

        if res.status_code == 201:
            return dci_job.get(context, context.last_job_id,
                               embed='topic,remoteci,components,rconfiguration')
        else:
            self.raise_error(res)

    def do_upgrade(self, context):
        res = dci_job.upgrade(context, job_id=self.id)

        if res.status_code == 201:
            return dci_job.get(context, context.last_job_id,
                               embed='topic,remoteci,components,rconfiguration')
        else:
            self.raise_error(res)

    def do_schedule(self, context):
        topic_res = dci_topic.list(context, where='name:' + self.topic)

        if topic_res.status_code == 200:
            topics = topic_res.json()['topics']
            if not len(topics):
                raise DciResourceNotFoundException(
                    'Topic: %s resource not found' % self.topic
                )

            topic_id = topics[0]['id']
            res = dci_job.schedule(context, topic_id=topic_id)
            if res.status_code == 201:
                return dci_job.get(context, context.last_job_id,
                                   embed='topic,remoteci,components,rconfiguration')
            else:
                self.raise_error(res)

        else:
            self.raise_error(topic_res)

    def do_create(self, context):
        topic_res = dci_topic.list(context, where='name:' + self.topic)

        if topic_res.status_code == 200:
            topics = topic_res.json()['topics']
            if not len(topics):
                raise DciResourceNotFoundException(
                    'Topic: %s resource not found' % self.topic
                )

            topic_id = topics[0]['id']

            res = dci_job.create(
                context, team_id=self.team_id, topic_id=topic_id,
                components=self.components, comment=self.comment
            )
            if res.status_code == 201:
                return dci_job.get_full_data(context, context.last_job_id)
            else:
                self.raise_error(res)

        else:
            self.raise_error(topic_res)


def main():

    resource_argument_spec = dict(
        state=dict(default='present', choices=['present', 'absent'], type='str'),
        id=dict(type='str'),
        topic=dict(required=False, type='str'),
        comment=dict(type='str'),
        status=dict(type='str'),
        metadata=dict(type='dict'),
        upgrade=dict(type='bool'),
        update=dict(type='bool'),
        components=dict(type='list'),
        team_id=dict(type='str'),
        embed=dict(type='str'),
        where=dict(type='str'),
    )
    resource_argument_spec.update(authentication_argument_spec())

    module = AnsibleModule(
        argument_spec=resource_argument_spec,
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    context = build_dci_context(module)
    action_name = get_standard_action(module.params)

    if action_name == 'update':
        # for readability
        if module.params['update']:
            action_name = 'job_update'
        if module.params['upgrade']:
            action_name = 'upgrade'
        if module.params['metadata']:
            action_name = 'set_metadata'

    elif action_name == 'create':
        if not module.params['components']:
            action_name = 'schedule'

    job = DciJob(module.params)
    action_func = getattr(job, 'do_%s' % action_name)

    http_response = run_action_func(action_func, context, module)
    result = parse_http_response(http_response, dci_job, context, module)

    # TODO (spredzy): The struct is nested into dict['job'] when it
    #                 should be at the dict level like the other modules.
    #                 This will requires agent rewritte and hence needs
    #                 to be communicated first
    #
    # Before: dict['job']['job_id']
    # After: dict['job_id']
    #
    if action_name in ['schedule', 'create']:
        result['job_id'] = context.last_job_id
        for k, v in result['job'].items():
            result[k] = v

    module.exit_json(**result)


if __name__ == '__main__':
    main()
