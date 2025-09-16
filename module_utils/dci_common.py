# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2023 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.dci_base import DciError, DciParameterError
from dciclient.v1.api import context as dci_context
from ansible.release import __version__ as ansible_version
from dciclient.version import __version__ as dciclient_version
from dciauth.version import __version__ as dciauth_version


def authentication_argument_spec():
    return dict(
        dci_login=dict(required=False, type='str',
                       fallback=(env_fallback, ['DCI_LOGIN'])),
        dci_password=dict(required=False, type='str', no_log=True,
                          fallback=(env_fallback, ['DCI_PASSWORD'])),
        dci_cs_url=dict(required=False, type='str',
                        fallback=(env_fallback, ['DCI_CS_URL']),
                        default='https://api.distributed-ci.io'),
        dci_client_id=dict(required=False, type='str',
                           fallback=(env_fallback, ['DCI_CLIENT_ID'])),
        dci_api_secret=dict(required=False, type='str', no_log=True,
                            fallback=(env_fallback, ['DCI_API_SECRET']))
    )


def build_dci_context(module):
    user_agent = ('Ansible/%s (python-dciclient/%s, python-dciauth/%s)'
                  ) % (ansible_version, dciclient_version, dciauth_version)
    if module.params['dci_login'] and module.params['dci_password']:
        return dci_context.build_dci_context(
            module.params['dci_cs_url'],
            module.params['dci_login'],
            module.params['dci_password'],
            user_agent
        )
    elif module.params['dci_client_id'] and module.params['dci_api_secret']:
        return dci_context.build_signature_context(
            module.params['dci_cs_url'],
            module.params['dci_client_id'],
            module.params['dci_api_secret'],
            user_agent
        )
    else:
        module.fail_json(msg='Missing or incomplete credentials.')


def module_params_empty(module_params):

    for item in module_params:
        if item not in ['state', 'mime'] and module_params[item] is not None:
            return False

    return True


def run_action_func(action_func, context, module):
    """
    Run the requested command and catch error when necessary.

    This method is a wrapper to the actual binding being called.
    It allows to catch exception and clean properly when needed.
    """

    try:
        res = action_func(context)
    except (DciError, DciParameterError) as exc:
        module.fail_json(msg=exc.message)

    return res


def get_standard_action(params):
    """
    Return the action that needs to be executed.

    Based on the module parameters specified a given action
    needs to be executed. The process to determine this action
    can be quite verbose. In order to facilitate the reading
    of the modules code, we externalize this decision process.

    """

    non_determistic_params = [
        "dci_login",
        "dci_password",
        "dci_cs_url",
        "dci_client_id",
        "dci_api_secret",
        "embed",
        "mime",
        "state",
        "where",
        "query",
        "active",
        "has_pre_release_access",
    ]
    deterministic_params = {k: v for k, v in params.items()
                            if k not in non_determistic_params}
    non_empty_values = [item for item in deterministic_params
                        if deterministic_params[item] is not None]

    if 'state' in params and params['state'] == 'absent':
        return 'delete'

    elif 'status' in non_empty_values:
        return 'status'

    elif not non_empty_values:
        return 'list'

    elif 'key' in non_empty_values:
        return 'set_key_value'

    elif non_empty_values == ['id']:
        return 'get'

    elif 'id' in non_empty_values:
        return 'update'

    return 'create'


def parse_http_response(response, resource, context, module):
    """
    Properly parse the HTTP response.

    This methods aims to parse the HTTP response received from
    the DCI control-server and act accordingly.

    It raises an error in case of 400, 401, 404 and 500 status code.
    It returns the adecuate value otherwise.
    """

    resource_name = resource.__name__.split('.')[-1]

    if response.status_code == 404:
        module.fail_json(msg='The specified resource does not exist')

    elif response.status_code in [401, 412]:
        module.fail_json(msg='Unauthorized resource access')

    elif response.status_code == 500:
        module.fail_json(msg='Internal Server Error')

    elif response.status_code == 400:
        error = response.json()
        module.fail_json(
            msg='%s - %s' % (error['message'], str(error['payload']))
        )

    elif response.status_code == 204:
        result = {}
        if module.params['state'] != 'absent':
            result = {
                '%s' % resource_name: resource.get(
                    context, module.params['id']
                ).json()[resource_name]
            }
        result['changed'] = True

    elif response.status_code == 409:
        if module.params['name'] is not None:
            result = {
                '%s' % resource_name: resource.list(
                    context, where='name:' + module.params['name']
                ).json()['%ss' % resource_name][0]
            }
        else:
            result = {'%s' % resource_name: resource.get(
                context, module.params['id']).json()[resource_name]
            }
        result['changed'] = False
    else:
        try:
            result = response.json()
        except Exception:
            result = {'text': response.text}
            result['status_code'] = response.status_code
        result['changed'] = True

    return result
