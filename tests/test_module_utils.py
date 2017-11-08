# Copyright 2017 Yanis Guenane  <yanis@guenane.org>
# Author: Yanis Guenane  <yanis@guenane.org>
#
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

from ansible.module_utils.common import get_action


def test_get_action():
    """Ensure the get_action() returns the adecuate action."""

    params = {'id': 'uuid', 'state': 'absent'}
    action = get_action(params)
    assert action == 'delete'

    params = {}
    action = get_action(params)
    assert action == 'list'

    params = {'where': 'label:PRODUCT_OWNER'}
    action = get_action(params)
    assert action == 'list'

    params = {'id': 'uuid'}
    action = get_action(params)
    assert action == 'get'

    params = {'id': 'uuid', 'name': 'newname'}
    action = get_action(params)
    assert action == 'update'

    params = {'name': 'newname'}
    action = get_action(params)
    assert action == 'create'
