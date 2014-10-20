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

from heat.engine import attributes
from heat.engine import properties


class Endpoint(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, ENDPOINT_GROUP_ID
    ) = (
        'tenant_id', 'name', 'description', 'endpoint_group_id'
    )

    ATTRIBUTES = (
        NEUTRON_PORT_ID
    ) = (
        'neutron_port_id'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the endpoint.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the endpoint.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the endpoint.'),
            update_allowed=True
        ),
        ENDPOINT_GROUP_ID: properties.Schema(
            properties.Schema.STRING,
            _('Endpoint group id of the endpoint.'),
            required=True,
            update_allowed=True
        )
    }

    attributes_schema = {
        NEUTRON_PORT_ID: attributes.Schema(
            _("Neutron port id of this endpoint")
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        ep_id = self.resource_id
        return client.show_endpoint(ep_id)['endpoint']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        ep = client.create_endpoint({'endpoint': props})['endpoint']

        self.resource_id_set(ep['id'])

    def _resolve_attribute(self, name):
        client = self.grouppolicy()
        ep_id = self.resource_id
        if name == 'neutron_port_id':
            return client.show_endpoint(ep_id)['endpoint']['neutron_port_id']
        return super(Endpoint, self)._resolve_attribute(name)

    def handle_delete(self):

        client = self.grouppolicy()
        ep_id = self.resource_id

        try:
            client.delete_endpoint(ep_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_endpoint(
                self.resource_id, {'endpoint': prop_diff})


class EndpointGroup(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, L2_POLICY_ID,
        PROVIDED_CONTRACTS, CONSUMED_CONTRACTS
    ) = (
        'tenant_id', 'name', 'description', 'l2_policy_id',
        'provided_contracts', 'consumed_contracts'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the endpoint group.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the endpoint group.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the endpoint group.'),
            update_allowed=True
        ),
        L2_POLICY_ID: properties.Schema(
            properties.Schema.STRING,
            _('L2 policy id of the endpoint group.'),
            update_allowed=True
        ),
        PROVIDED_CONTRACTS: properties.Schema(
            properties.Schema.LIST,
            _('Provided contracts for the endpoint group.'),
            update_allowed=True
        ),
        CONSUMED_CONTRACTS: properties.Schema(
            properties.Schema.LIST,
            _('Consumed contracts for the endpoint group.'),
            update_allowed=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        epg_id = self.resource_id
        return client.show_endpoint_group(epg_id)['endpoint_group']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        provided_contracts_list = {}
        consumed_contracts_list = {}
        props_provided_contracts = props.get('provided_contracts', [])
        props_consumed_contracts = props.get('consumed_contracts', [])

        for prop_prov_contract in props_provided_contracts:
            contract_id = prop_prov_contract['contract_id']
            contract_scope = prop_prov_contract['contract_scope']
            provided_contracts_list.update({contract_id: contract_scope})

        for prop_cons_contract in props_consumed_contracts:
            contract_id = prop_cons_contract['contract_id']
            contract_scope = prop_cons_contract['contract_scope']
            consumed_contracts_list.update({contract_id: contract_scope})

        if provided_contracts_list:
            props['provided_contracts'] = provided_contracts_list
        if consumed_contracts_list:
            props['consumed_contracts'] = consumed_contracts_list

        epg = client.create_endpoint_group(
            {'endpoint_group': props})['endpoint_group']

        self.resource_id_set(epg['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        epg_id = self.resource_id

        try:
            client.delete_endpoint_group(epg_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_endpoint_group(
                self.resource_id, {'endpoint_group': prop_diff})


class L2Policy(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, L3_POLICY_ID
    ) = (
        'tenant_id', 'name', 'description', 'l3_policy_id'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the L2 policy.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the L2 policy.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the L2 policy.'),
            update_allowed=True
        ),
        L3_POLICY_ID: properties.Schema(
            properties.Schema.STRING,
            _('L3 policy id associated with l2 policy.'),
            required=True,
            update_allowed=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        l2_policy_id = self.resource_id
        return client.show_l2_policy(l2_policy_id)['l2_policy']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        l2_policy = client.create_l2_policy(
            {'l2_policy': props})['l2_policy']

        self.resource_id_set(l2_policy['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        l2_policy_id = self.resource_id

        try:
            client.delete_l2_policy(l2_policy_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_l2_policy(
                self.resource_id, {'l2_policy': prop_diff})


class L3Policy(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, IP_VERSION, IP_POOL,
        SUBNET_PREFIX_LENGTH
    ) = (
        'tenant_id', 'name', 'description', 'ip_version', 'ip_pool',
        'subnet_prefix_length'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the L3 policy.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the L3 policy.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the L3 policy.'),
            update_allowed=True
        ),
        IP_VERSION: properties.Schema(
            properties.Schema.STRING,
            _('IP version of the L3 policy.'),
            update_allowed=False
        ),
        IP_POOL: properties.Schema(
            properties.Schema.STRING,
            _('IP pool of the L3 policy.'),
            update_allowed=False
        ),
        SUBNET_PREFIX_LENGTH: properties.Schema(
            properties.Schema.INTEGER,
            _('Subnet prefix length of L3 policy.'),
            update_allowed=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        l3_policy_id = self.resource_id
        return client.show_l3_policy(l3_policy_id)['l3_policy']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        l3_policy = client.create_l3_policy(
            {'l3_policy': props})['l3_policy']

        self.resource_id_set(l3_policy['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        l3_policy_id = self.resource_id

        try:
            client.delete_l3_policy(l3_policy_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_l3_policy(
                self.resource_id, {'l3_policy': prop_diff})


def resource_mapping():
    return {
        'OS::Neutron::Endpoint': Endpoint,
        'OS::Neutron::EndpointGroup': EndpointGroup,
        'OS::Neutron::L2Policy': L2Policy,
        'OS::Neutron::L3Policy': L3Policy,
    }
