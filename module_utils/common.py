# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Red Hat, Inc
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

from dciclient.v1.api import context as dci_context
from ansible.module_utils.dci_base import *

import os


def param_from_module_or_env(module, name, default=None):
    return module.params[name.lower()] or os.getenv(name.upper())


def get_details(module):
    """Method that retrieves the appropriate credentials. """

    login = param_from_module_or_env(module, 'dci_login')
    password = param_from_module_or_env(module, 'dci_password')

    client_id = param_from_module_or_env(module, 'dci_client_id')
    api_secret = param_from_module_or_env(module, 'dci_api_secret')

    url = param_from_module_or_env(module, 'dci_cs_url',
                                   'https://api.distributed-ci.io')

    return login, password, url, client_id, api_secret


def build_dci_context(module):
    login, password, url, client_id, api_secret = get_details(module)

    if login is not None and password is not None:
        return dci_context.build_dci_context(url, login, password, 'Ansible')
    elif client_id is not None and api_secret is not None:
        return dci_context.build_signature_context(url, client_id, api_secret,
                                                   'Ansible')
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
    except DciResourceNotFoundException as exc:
        module.fail_json(msg=exc.message)
    except DciServerErrorException as exc:
        module.fail_json(msg=exc.message)
    except DciUnexpectedErrorException as exc:
        module.fail_json(msg=exc.message)
    except DciParameterError as exc:
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

    non_determistic_params = ['embed', 'mime', 'state', 'where']
    deterministic_params = {k: v for k, v in params.items() if k not in non_determistic_params}
    non_empty_values = [item for item in deterministic_params if deterministic_params[item]]

    if 'state' in params and params['state'] == 'absent':
        return 'delete'

    elif not non_empty_values:
        return 'list'

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

    elif response.status_code == 401:
        module.fail_json(msg='Unauthorized credentials')

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
                ).json()[resource_name],
            }
        result['changed'] = True

    elif response.status_code == 409:
        result = response.json()
        result = {
            '%s' % resource_name: resource.list(
                context, where='name:' + module.params['name']
             ).json()['%ss' % resource_name][0],
        }
        result['changed'] = False
    else:
        if not response._content:
            result = {}
        else:
            result = response.json()
        result['changed'] = True

    return result
