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


def get_action(params):
    """
    Return the action that needs to be executed.

    Based on the module parameters specified a given action
    needs to be executed. The process to determine this action
    can be quite verbose. In order to facilitate the reading
    of the modules code, we externalize this decision process.

    """

    non_determistic_params = ['embed', 'mime', 'state', 'where']
    deterministic_params = {k: v for k, v in params.items() if k not in non_determistic_params}
    non_empty_values = [item for item in deterministic_params if deterministic_params[item] is not None]

    if 'state' in params and params['state'] == 'absent':
        return 'delete'

    if not non_empty_values:
        return 'list'

    if non_empty_values == ['id']:
        return 'get'

    if 'id' in non_empty_values:
        return 'update'

    if 'path' in non_empty_values:
        return 'upload'

    if 'dest' in non_empty_values:
        return 'download'

    return 'create'
