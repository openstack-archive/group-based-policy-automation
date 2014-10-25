# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from gbpautomation.heat.engine.resources.neutron import gbpresource
from neutronclient.common.exceptions import NeutronClientException

from heat.engine import properties


class ServiceChainNode(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, SERVICE_TYPE, CONFIG
    ) = (
        'tenant_id', 'name', 'description', 'service_type', 'config'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the service chain node.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the service chain node.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the service chain node.'),
            update_allowed=True
        ),
        SERVICE_TYPE: properties.Schema(
            properties.Schema.STRING,
            _('Type of service in the service chain node.'),
            required=True,
            update_allowed=True
        ),
        CONFIG: properties.Schema(
            properties.Schema.STRING,
            _('Configuration of the service chain node.'),
            required=True,
            update_allowed=False
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        sc_node_id = self.resource_id
        return client.show_servicechain_node(sc_node_id)['servicechain_node']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        sc_node = client.create_servicechain_node(
            {'servicechain_node': props})['servicechain_node']

        self.resource_id_set(sc_node['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        sc_node_id = self.resource_id

        try:
            client.delete_servicechain_node(sc_node_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_servicechain_node(
                self.resource_id, {'servicechain_node': prop_diff})


class ServiceChainSpec(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, NODES
    ) = (
        'tenant_id', 'name', 'description', 'nodes'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the service chain spec.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the service chain spec.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the service chain spec.'),
            update_allowed=True
        ),
        NODES: properties.Schema(
            properties.Schema.LIST,
            _('Nodes in the service chain spec.'),
            required=True,
            update_allowed=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        sc_spec_id = self.resource_id
        return client.show_servicechain_spec(sc_spec_id)['servicechain_spec']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        sc_spec = client.create_servicechain_spec(
            {'servicechain_spec': props})['servicechain_spec']

        self.resource_id_set(sc_spec['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        sc_spec_id = self.resource_id

        try:
            client.delete_servicechain_spec(sc_spec_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_servicechain_spec(
                self.resource_id, {'servicechain_spec': prop_diff})


def resource_mapping():
    return {
        'OS::Neutron::ServiceChainNode': ServiceChainNode,
        'OS::Neutron::ServiceChainSpec': ServiceChainSpec,
    }
