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

    def do_delete(self, context):
        """Remove a resource."""

        # NOTE(spredzy): Some resources need their etag in order to be deleted
        # other do not. This needs to be standardized at the control-server
        # level. Meanwhile, the code below allows to handle both scenarios
        # in a single way.
        res = self.resource.get(context, self.id)

        if res.status_code == 200:
            kwargs = {}
            if 'etag' in res.json()[self.resource_name]:
                kwargs = {
                    'etag': res.json()[self.resource_name]['etag']
                }
            return self.resource.delete(context, self.id, **kwargs)

        elif res.status_code in [401, 404]:
            raise DciResourceNotFoundException(
                '%s: %s resource not found' % (self.resource_name, self.id)
            )

        elif res.status_code == 500:
            raise DciServerErrorException

        else:
            raise DciUnexpectedErrorException(res.status_code)

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

            return self.resource.update(context, **kwargs)

        elif res.status_code in [401, 404]:
            raise DciResourceNotFoundException(
                '%s: %s resource not found' % (self.resource_name, self.id)
            )

        elif res.status_code == 500:
            raise DciServerErrorException

        else:
            raise DciUnexpectedErrorException(res.status_code)

    def do_create(self, context):
        """Create a resource."""

        kwargs = {}
        for param in self.deterministic_params:
            kwargs[param] = getattr(self, param)

        return self.resource.create(context, **kwargs)
