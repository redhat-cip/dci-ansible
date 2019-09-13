# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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


class DciResourceNotFoundException(Exception):
    pass


class DciServerErrorException(Exception):

    def __init__(self):
        self.message = 'Internal Server Error'


class DciUnexpectedErrorException(Exception):

    def __init__(self, status_code):
        self.message = 'Unexpected Error: %s' % status_code


class DciParameterError(Exception):
    pass


class DciBase(object):
    """A Base DCI resource."""

    def __init__(self, resource):
        self.resource = resource
        self.resource_name = resource.__name__.split('.')[-1]
        self.deterministic_params = []

    def raise_error(self, res):
        """Parse the http response and raise the appropriate error."""

        if res.status_code in [401, 404]:
            raise DciResourceNotFoundException(
                '%s: %s resource not found' % (self.resource_name, self.id)
            )

        elif res.status_code == 500:
            raise DciServerErrorException(res.status_code)
        else:
            try:
                message = res.json()['message']
            except Exception:
                message = res.text
            raise DciUnexpectedErrorException(
                "Status Code: %d: %s" % (res.status_code, message))

    def do_delete(self, context):
        """Remove a resource."""

        res = self.resource.get(context, self.id)
        if res.status_code == 200:
            kwargs = {}
            if 'etag' in res.json()[self.resource_name]:
                kwargs = {
                    'etag': res.json()[self.resource_name]['etag']
                }
            return self.resource.delete(context, self.id, **kwargs)

        else:
            self.raise_error(res)

    def do_list(self, context):
        """List all resources."""

        return self.resource.list(context, **self.search_criterias)

    def do_get(self, context):
        """Retrieve a resource."""

        return self.resource.get(context, self.id, **self.search_criterias)

    def do_update(self, context):
        """Update a resource."""

        res = self.resource.get(context, self.id)

        if res.status_code == 200:
            kwargs = {
                'id': self.id,
                'etag': res.json()[self.resource_name]['etag']
            }
            for param in self.deterministic_params:
                kwargs[param] = getattr(self, param)

            if hasattr(self, 'active'):
                kwargs['state'] = 'active' if self.active else 'inactive'
                del kwargs['active']

            return self.resource.update(context, **kwargs)
        else:
            self.raise_error(res)

    def do_create(self, context):
        """Create a resource."""

        kwargs = {}
        for param in self.deterministic_params:
            kwargs[param] = getattr(self, param)

        if hasattr(self, 'active'):
            kwargs['state'] = 'active' if self.active else 'inactive'
            del kwargs['active']

        return self.resource.create(context, **kwargs)
