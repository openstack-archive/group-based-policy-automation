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

from gbpautomation.heat.engine.resources import gbpresource
from heat.common.i18n import _
from heat.engine import attributes
from heat.engine import constraints
from heat.engine import properties
from neutronclient.common.exceptions import NeutronClientException


class PolicyTarget(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, POLICY_TARGET_GROUP_ID,
        PORT_ID
    ) = (
        'tenant_id', 'name', 'description', 'policy_target_group_id',
        'port_id'
    )

    ATTRIBUTES = (
        PORT_ID_ATTR
    ) = (
        'port_id'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the policy target.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the policy target.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the policy target.'),
            update_allowed=True
        ),
        POLICY_TARGET_GROUP_ID: properties.Schema(
            properties.Schema.STRING,
            _('Policy target group id of the policy target.'),
            required=True,
            update_allowed=True
        ),
        PORT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Neutron port id of the policy target.'),
            update_allowed=False
        )
    }

    attributes_schema = {
        PORT_ID_ATTR: attributes.Schema(
            _('Neutron port id of this policy target.')
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        pt_id = self.resource_id
        return client.show_policy_target(pt_id)['policy_target']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        pt = client.create_policy_target(
            {'policy_target': props})['policy_target']

        self.resource_id_set(pt['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        pt_id = self.resource_id

        try:
            client.delete_policy_target(pt_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_policy_target(
                self.resource_id, {'policy_target': prop_diff})


class PolicyTargetGroup(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, L2_POLICY_ID, PROVIDED_POLICY_RULE_SETS,
        CONSUMED_POLICY_RULE_SETS, NETWORK_SERVICE_POLICY_ID, SHARED
    ) = (
        'tenant_id', 'name', 'description', 'l2_policy_id',
        'provided_policy_rule_sets', 'consumed_policy_rule_sets',
        'network_service_policy_id', 'shared'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the policy target group.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the policy target group.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the policy target group.'),
            update_allowed=True
        ),
        L2_POLICY_ID: properties.Schema(
            properties.Schema.STRING,
            _('L2 policy id of the policy target group.'),
            update_allowed=True
        ),
        PROVIDED_POLICY_RULE_SETS: properties.Schema(
            properties.Schema.LIST,
            _('Provided policy rule set for the policy target group.'),
            update_allowed=True
        ),
        CONSUMED_POLICY_RULE_SETS: properties.Schema(
            properties.Schema.LIST,
            _('Consumed policy rule set for the policy target group.'),
            update_allowed=True
        ),
        NETWORK_SERVICE_POLICY_ID: properties.Schema(
            properties.Schema.STRING,
            _('Network service policy id of the policy target group.'),
            update_allowed=True, default=None
        ),
        SHARED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Shared.'),
            update_allowed=True, required=True
        )

    }

    def _show_resource(self):
        client = self.grouppolicy()
        ptg_id = self.resource_id
        return client.show_policy_target_group(ptg_id)['policy_target_group']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        provided_policy_rule_set_list = {}
        consumed_policy_rule_set_list = {}
        props_provided_policy_rule_sets = props.get(
            'provided_policy_rule_sets', [])
        props_consumed_policy_rule_sets = props.get(
            'consumed_policy_rule_sets', [])

        for prop_prov_policy_rule_set in props_provided_policy_rule_sets:
            policy_rule_set_id = (
                prop_prov_policy_rule_set['policy_rule_set_id'])
            policy_rule_set_scope = (
                prop_prov_policy_rule_set['policy_rule_set_scope'])
            provided_policy_rule_set_list.update({policy_rule_set_id:
                                                  policy_rule_set_scope})

        for prop_cons_policy_rule_set in props_consumed_policy_rule_sets:
            policy_rule_set_id = (
                prop_cons_policy_rule_set['policy_rule_set_id'])
            policy_rule_set_scope = (
                prop_cons_policy_rule_set['policy_rule_set_scope'])
            consumed_policy_rule_set_list.update({policy_rule_set_id:
                                                  policy_rule_set_scope})

        if provided_policy_rule_set_list:
            props['provided_policy_rule_sets'] = provided_policy_rule_set_list
        if consumed_policy_rule_set_list:
            props['consumed_policy_rule_sets'] = consumed_policy_rule_set_list

        ptg = client.create_policy_target_group(
            {'policy_target_group': props})['policy_target_group']

        self.resource_id_set(ptg['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        ptg_id = self.resource_id

        try:
            client.delete_policy_target_group(ptg_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            provided_policy_rule_set_list = {}
            consumed_policy_rule_set_list = {}
            props_provided_policy_rule_sets = prop_diff.get(
                'provided_policy_rule_sets', [])
            props_consumed_policy_rule_sets = prop_diff.get(
                'consumed_policy_rule_sets', [])

            for prop_prov_policy_rule_set in props_provided_policy_rule_sets:
                policy_rule_set_id = (
                    prop_prov_policy_rule_set['policy_rule_set_id'])
                policy_rule_set_scope = (
                    prop_prov_policy_rule_set['policy_rule_set_scope'])
                provided_policy_rule_set_list.update({policy_rule_set_id:
                                                      policy_rule_set_scope})

            for prop_cons_policy_rule_set in props_consumed_policy_rule_sets:
                policy_rule_set_id = (
                    prop_cons_policy_rule_set['policy_rule_set_id'])
                policy_rule_set_scope = (
                    prop_cons_policy_rule_set['policy_rule_set_scope'])
                consumed_policy_rule_set_list.update({policy_rule_set_id:
                                                      policy_rule_set_scope})

            if provided_policy_rule_set_list:
                prop_diff['provided_policy_rule_sets'] = (
                    provided_policy_rule_set_list)
            if consumed_policy_rule_set_list:
                prop_diff['consumed_policy_rule_sets'] = (
                    consumed_policy_rule_set_list)

            self.grouppolicy().update_policy_target_group(
                self.resource_id, {'policy_target_group': prop_diff})


class L2Policy(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, L3_POLICY_ID, SHARED
    ) = (
        'tenant_id', 'name', 'description', 'l3_policy_id', 'shared'
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
        ),
        SHARED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Shared.'),
            update_allowed=True, required=True
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
        SUBNET_PREFIX_LENGTH, EXTERNAL_SEGMENTS, SHARED
    ) = (
        'tenant_id', 'name', 'description', 'ip_version', 'ip_pool',
        'subnet_prefix_length', 'external_segments', 'shared'
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
        ),
        EXTERNAL_SEGMENTS: properties.Schema(
            properties.Schema.LIST,
            _('External segments for L3 policy.'),
            update_allowed=True
        ),
        SHARED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Shared.'),
            update_allowed=True, required=True
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

        external_segments_dict = {}
        props_external_segments = props.get(
            'external_segments', [])

        for prop_external_segment in props_external_segments:
            external_segment_id = (
                prop_external_segment['external_segment_id'])
            allocated_address = (
                prop_external_segment['allocated_address'])
            external_segments_dict.update({external_segment_id:
                                           allocated_address})

        if external_segments_dict:
            props['external_segments'] = external_segments_dict

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
            external_segments_dict = {}
            props_external_segments = prop_diff.get(
                'external_segments', [])

            for prop_external_segment in props_external_segments:
                external_segment_id = (
                    prop_external_segment['external_segment_id'])
                allocated_address = (
                    prop_external_segment['allocated_address'])
                external_segments_dict.update({external_segment_id:
                                               allocated_address})

            if external_segments_dict:
                prop_diff['external_segments'] = external_segments_dict
            self.grouppolicy().update_l3_policy(
                self.resource_id, {'l3_policy': prop_diff})


class PolicyClassifier(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, PROTOCOL, PORT_RANGE,
        DIRECTION, SHARED
    ) = (
        'tenant_id', 'name', 'description', 'protocol', 'port_range',
        'direction', 'shared'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the policy classifier.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the policy classifier.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the policy classifier.'),
            update_allowed=True
        ),
        PROTOCOL: properties.Schema(
            properties.Schema.STRING,
            _('Protocol of traffic described by the policy classifier.'),
            constraints=[
                constraints.AllowedValues(['tcp', 'udp', 'icmp', None])
            ],
            update_allowed=True
        ),
        PORT_RANGE: properties.Schema(
            properties.Schema.STRING,
            _('Port range of traffic described by the policy classifier.'),
            update_allowed=True
        ),
        DIRECTION: properties.Schema(
            properties.Schema.STRING,
            _('Direction of traffic described by the policy classifier.'),
            constraints=[
                constraints.AllowedValues(['in', 'out', 'bi', None])
            ],
            update_allowed=True
        ),
        SHARED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Shared.'),
            update_allowed=True, required=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        pc_id = self.resource_id
        return client.show_policy_classifier(pc_id)['policy_classifier']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        policy_classifier = client.create_policy_classifier(
            {'policy_classifier': props})['policy_classifier']

        self.resource_id_set(policy_classifier['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        pc_id = self.resource_id

        try:
            client.delete_policy_classifier(pc_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_policy_classifier(
                self.resource_id, {'policy_classifier': prop_diff})


class PolicyAction(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, ACTION_TYPE, ACTION_VALUE, SHARED
    ) = (
        'tenant_id', 'name', 'description', 'action_type', 'action_value',
        'shared'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the action.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the action.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the action.'),
            update_allowed=True
        ),
        ACTION_TYPE: properties.Schema(
            properties.Schema.STRING,
            _('Type of action.'),
            constraints=[
                constraints.AllowedValues(['allow', 'redirect', None])
            ],
            update_allowed=True
        ),
        ACTION_VALUE: properties.Schema(
            properties.Schema.STRING,
            _('Value of the action.'),
            update_allowed=True
        ),
        SHARED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Shared.'),
            update_allowed=True, required=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        action_id = self.resource_id
        return client.show_policy_action(action_id)['policy_action']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        policy_action = client.create_policy_action(
            {'policy_action': props})['policy_action']

        self.resource_id_set(policy_action['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        action_id = self.resource_id

        try:
            client.delete_policy_action(action_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_policy_action(
                self.resource_id, {'policy_action': prop_diff})


class PolicyRule(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, ENABLED, POLICY_CLASSIFIER_ID,
        POLICY_ACTIONS, SHARED
    ) = (
        'tenant_id', 'name', 'description', 'enabled', 'policy_classifier_id',
        'policy_actions', 'shared'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the policy rule.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the policy rule.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the policy rule.'),
            update_allowed=True
        ),
        ENABLED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('State of policy rule.'),
            default=True, update_allowed=True
        ),
        POLICY_CLASSIFIER_ID: properties.Schema(
            properties.Schema.STRING,
            _('Classifier id of the policy rule.'),
            required=True, update_allowed=True
        ),
        POLICY_ACTIONS: properties.Schema(
            properties.Schema.LIST,
            _('List of actions of the policy rule.'),
            default=None, update_allowed=True
        ),
        SHARED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Shared.'),
            update_allowed=True, required=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        rule_id = self.resource_id
        return client.show_policy_rule(rule_id)['policy_rule']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        policy_rule = client.create_policy_rule(
            {'policy_rule': props})['policy_rule']

        self.resource_id_set(policy_rule['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        rule_id = self.resource_id

        try:
            client.delete_policy_rule(rule_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_policy_rule(
                self.resource_id, {'policy_rule': prop_diff})


class PolicyRuleSet(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, PARENT_ID, CHILD_POLICY_RULE_SETS,
        POLICY_RULES, SHARED
    ) = (
        'tenant_id', 'name', 'description', 'parent_id',
        'child_policy_rule_sets', 'policy_rules', 'shared'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the policy rule set.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the policy rule set.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the policy rule set.'),
            update_allowed=True
        ),
        PARENT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Parent id of the policy rule set.'),
            update_allowed=False
        ),
        CHILD_POLICY_RULE_SETS: properties.Schema(
            properties.Schema.LIST,
            _('List of child policy rule sets.'),
            default=None, update_allowed=True
        ),
        POLICY_RULES: properties.Schema(
            properties.Schema.LIST,
            _('List of policy rules.'),
            default=None, update_allowed=True
        ),
        SHARED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Shared.'),
            update_allowed=True, required=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        prs_id = self.resource_id
        return client.show_policy_rule_set(prs_id)['policy_rule_set']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        policy_rule_set = client.create_policy_rule_set(
            {'policy_rule_set': props})['policy_rule_set']

        self.resource_id_set(policy_rule_set['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        policy_rule_set_id = self.resource_id

        try:
            client.delete_policy_rule_set(policy_rule_set_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_policy_rule_set(
                self.resource_id, {'policy_rule_set': prop_diff})


class NetworkServicePolicy(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, NETWORK_SERVICE_PARAMS, SHARED
    ) = (
        'tenant_id', 'name', 'description', 'network_service_params', 'shared'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the network service policy.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the network service policy.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the network service policy.'),
            update_allowed=True
        ),
        NETWORK_SERVICE_PARAMS: properties.Schema(
            properties.Schema.LIST,
            _('List of network service policy dicts.'),
            default=None, update_allowed=True
        ),
        SHARED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Shared.'),
            update_allowed=True, required=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        nsp_id = self.resource_id
        nsp = client.show_network_service_policy(nsp_id)
        return nsp['network_service_policy']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        nsp = client.create_network_service_policy(
            {'network_service_policy': props})['network_service_policy']

        self.resource_id_set(nsp['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        nsp_id = self.resource_id

        try:
            client.delete_network_service_policy(nsp_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_network_service_policy(
                self.resource_id, {'network_service_policy': prop_diff})


class ExternalPolicy(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, EXTERNAL_SEGMENTS,
        PROVIDED_POLICY_RULE_SETS, CONSUMED_POLICY_RULE_SETS, SHARED
    ) = (
        'tenant_id', 'name', 'description', 'external_segments',
        'provided_policy_rule_sets', 'consumed_policy_rule_sets', 'shared'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the external policy.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the external policy.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the external policy.'),
            update_allowed=True
        ),
        EXTERNAL_SEGMENTS: properties.Schema(
            properties.Schema.LIST,
            _('External segments of the policy.'),
            update_allowed=True
        ),
        PROVIDED_POLICY_RULE_SETS: properties.Schema(
            properties.Schema.LIST,
            _('Provided policy rule sets.'),
            default=None, update_allowed=True
        ),
        CONSUMED_POLICY_RULE_SETS: properties.Schema(
            properties.Schema.LIST,
            _('Consumed policy rule sets.'),
            default=None, update_allowed=True
        ),
        SHARED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Shared.'),
            update_allowed=True, required=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        ext_policy_id = self.resource_id
        ext_policy = client.show_external_policy(ext_policy_id)
        return ext_policy['external_policy']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        provided_policy_rule_set_list = {}
        consumed_policy_rule_set_list = {}
        props_provided_policy_rule_sets = props.get(
            'provided_policy_rule_sets', [])
        props_consumed_policy_rule_sets = props.get(
            'consumed_policy_rule_sets', [])

        for prop_prov_policy_rule_set in props_provided_policy_rule_sets:
            policy_rule_set_id = (
                prop_prov_policy_rule_set['policy_rule_set_id'])
            policy_rule_set_scope = (
                prop_prov_policy_rule_set['policy_rule_set_scope'])
            provided_policy_rule_set_list.update({policy_rule_set_id:
                                                  policy_rule_set_scope})

        for prop_cons_policy_rule_set in props_consumed_policy_rule_sets:
            policy_rule_set_id = (
                prop_cons_policy_rule_set['policy_rule_set_id'])
            policy_rule_set_scope = (
                prop_cons_policy_rule_set['policy_rule_set_scope'])
            consumed_policy_rule_set_list.update({policy_rule_set_id:
                                                  policy_rule_set_scope})

        if provided_policy_rule_set_list:
            props['provided_policy_rule_sets'] = provided_policy_rule_set_list
        if consumed_policy_rule_set_list:
            props['consumed_policy_rule_sets'] = consumed_policy_rule_set_list

        ext_policy = client.create_external_policy(
            {'external_policy': props})['external_policy']

        self.resource_id_set(ext_policy['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        ext_policy_id = self.resource_id

        try:
            client.delete_external_policy(ext_policy_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            provided_policy_rule_set_list = {}
            consumed_policy_rule_set_list = {}
            props_provided_policy_rule_sets = prop_diff.get(
                'provided_policy_rule_sets', [])
            props_consumed_policy_rule_sets = prop_diff.get(
                'consumed_policy_rule_sets', [])

            for prop_prov_policy_rule_set in props_provided_policy_rule_sets:
                policy_rule_set_id = (
                    prop_prov_policy_rule_set['policy_rule_set_id'])
                policy_rule_set_scope = (
                    prop_prov_policy_rule_set['policy_rule_set_scope'])
                provided_policy_rule_set_list.update({policy_rule_set_id:
                                                      policy_rule_set_scope})

            for prop_cons_policy_rule_set in props_consumed_policy_rule_sets:
                policy_rule_set_id = (
                    prop_cons_policy_rule_set['policy_rule_set_id'])
                policy_rule_set_scope = (
                    prop_cons_policy_rule_set['policy_rule_set_scope'])
                consumed_policy_rule_set_list.update({policy_rule_set_id:
                                                      policy_rule_set_scope})

            if provided_policy_rule_set_list:
                prop_diff['provided_policy_rule_sets'] = (
                    provided_policy_rule_set_list)
            if consumed_policy_rule_set_list:
                prop_diff['consumed_policy_rule_sets'] = (
                    consumed_policy_rule_set_list)

            self.grouppolicy().update_external_policy(
                self.resource_id, {'external_policy': prop_diff})


class ExternalSegment(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, IP_VERSION, CIDR, SUBNET_ID,
        EXTERNAL_ROUTES, PORT_ADDRESS_TRANSLATION, SHARED
    ) = (
        'tenant_id', 'name', 'description', 'ip_version', 'cidr',
        'subnet_id', 'external_routes', 'port_address_translation',
        'shared'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the external segment.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the external segment.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the external segment.'),
            update_allowed=True
        ),
        IP_VERSION: properties.Schema(
            properties.Schema.STRING,
            _('IP version of the external segment.'),
            default='4', update_allowed=False
        ),
        CIDR: properties.Schema(
            properties.Schema.STRING,
            _('CIDR of the external segment.'),
            default=None, update_allowed=False
        ),
        SUBNET_ID: properties.Schema(
            properties.Schema.STRING,
            _('Subnet ID of the neutron external network.'),
            default=None, update_allowed=False
        ),
        EXTERNAL_ROUTES: properties.Schema(
            properties.Schema.LIST,
            _('External routes of the external segment.'),
            default=None, update_allowed=True
        ),
        PORT_ADDRESS_TRANSLATION: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Port address translation required for the external segment.'),
            update_allowed=True, default=False
        ),
        SHARED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Shared.'),
            update_allowed=True, required=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        es_id = self.resource_id
        es = client.show_external_segment(es_id)
        return es['external_segment']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        es = client.create_external_segment(
            {'external_segment': props})['external_segment']

        self.resource_id_set(es['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        es_id = self.resource_id

        try:
            client.delete_external_segment(es_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_external_segment(
                self.resource_id, {'external_segment': prop_diff})


class NATPool(gbpresource.GBPResource):

    PROPERTIES = (
        TENANT_ID, NAME, DESCRIPTION, IP_VERSION, IP_POOL,
        EXTERNAL_SEGMENT_ID, SHARED
    ) = (
        'tenant_id', 'name', 'description', 'ip_version', 'ip_pool',
        'external_segment_id', 'shared'
    )

    properties_schema = {
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id of the NAT pool.')
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the NAT pool.'),
            update_allowed=True
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description of the NET pool.'),
            update_allowed=True
        ),
        IP_VERSION: properties.Schema(
            properties.Schema.STRING,
            _('IP version of the NAT pool.'),
            default='4', update_allowed=False
        ),
        IP_POOL: properties.Schema(
            properties.Schema.STRING,
            _('IP pool of the NAT pool.'),
            default=None, update_allowed=False
        ),
        EXTERNAL_SEGMENT_ID: properties.Schema(
            properties.Schema.STRING,
            _('External segment id of the NAT pool.'),
            update_allowed=True, required=True
        ),
        SHARED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Shared.'),
            update_allowed=True, required=True
        )
    }

    def _show_resource(self):
        client = self.grouppolicy()
        nat_pool_id = self.resource_id
        nat_pool = client.show_nat_pool(nat_pool_id)
        return nat_pool['nat_pool']

    def handle_create(self):
        client = self.grouppolicy()

        props = {}
        for key in self.properties:
            if self.properties.get(key) is not None:
                props[key] = self.properties.get(key)

        nat_pool = client.create_nat_pool(
            {'nat_pool': props})['nat_pool']

        self.resource_id_set(nat_pool['id'])

    def handle_delete(self):

        client = self.grouppolicy()
        nat_pool_id = self.resource_id

        try:
            client.delete_nat_pool(nat_pool_id)
        except NeutronClientException as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return self._delete_task()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        if prop_diff:
            self.grouppolicy().update_nat_pool(
                self.resource_id, {'nat_pool': prop_diff})


def resource_mapping():
    return {
        'OS::GroupBasedPolicy::PolicyTarget': PolicyTarget,
        'OS::GroupBasedPolicy::PolicyTargetGroup': PolicyTargetGroup,
        'OS::GroupBasedPolicy::L2Policy': L2Policy,
        'OS::GroupBasedPolicy::L3Policy': L3Policy,
        'OS::GroupBasedPolicy::PolicyClassifier': PolicyClassifier,
        'OS::GroupBasedPolicy::PolicyAction': PolicyAction,
        'OS::GroupBasedPolicy::PolicyRule': PolicyRule,
        'OS::GroupBasedPolicy::PolicyRuleSet': PolicyRuleSet,
        'OS::GroupBasedPolicy::NetworkServicePolicy': NetworkServicePolicy,
        'OS::GroupBasedPolicy::ExternalPolicy': ExternalPolicy,
        'OS::GroupBasedPolicy::ExternalSegment': ExternalSegment,
        'OS::GroupBasedPolicy::NATPool': NATPool
    }
