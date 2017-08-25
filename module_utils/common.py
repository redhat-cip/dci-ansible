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


def build_dci_context(module):
    client_id = param_from_module_or_env(module, 'dci_client_id')

    api_secret = param_from_module_or_env(module, 'dci_api_secret')

    url = param_from_module_or_env(module, 'dci_cs_url',
                                   'https://api.distributed-ci.io')

    if client_id is not None and api_secret is not None:
        return dci_context.build_signature_context(url, client_id, api_secret,
                                                   'Ansible')
    else:
        module.fail_json(msg='Missing or incomplete credentials.')


def module_params_empty(module_params):

    for item in module_params:
        if item not in ['state', 'mime'] and module_params[item] is not None:
            return False

    return True
