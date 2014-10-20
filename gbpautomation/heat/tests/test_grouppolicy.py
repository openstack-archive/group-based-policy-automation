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

import copy
import six

from gbpautomation.heat.engine.resources.neutron import grouppolicy
from gbpclient.v2_0 import client as gbpclient
from heat.common import exception
from heat.common import template_format
from heat.tests.common import HeatTestCase

from heat.engine import scheduler
from heat.tests import utils


endpoint_template = '''
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test neutron endpoint resource",
  "Parameters" : {},
  "Resources" : {
    "endpoint": {
      "Type": "OS::Neutron::Endpoint",
      "Properties": {
        "name": "test-endpoint",
        "endpoint_group_id": "epg-id",
        "description": "test endpoint resource"
      }
    }
  }
}
'''

endpoint_group_template = '''
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test neutron endpoint group resource",
  "Parameters" : {},
  "Resources" : {
    "endpoint_group": {
      "Type": "OS::Neutron::EndpointGroup",
      "Properties": {
        "name": "test-endpoint-group",
        "description": "test endpoint group resource",
        "l2_policy_id": "l2-policy-id",
        "provided_contracts": [
            {"contract_id": "contract1", "contract_scope": "scope1"},
            {"contract_id": "contract2", "contract_scope": "scope2"}
        ],
        "consumed_contracts": [
            {"contract_id": "contract3", "contract_scope": "scope3"},
            {"contract_id": "contract4", "contract_scope": "scope4"}
        ]
      }
    }
  }
}
'''

l2_policy_template = '''
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test neutron l2 policy",
  "Parameters" : {},
  "Resources" : {
    "l2_policy": {
      "Type": "OS::Neutron::L2Policy",
      "Properties": {
        "name": "test-l2-policy",
        "description": "test L2 policy resource",
        "l3_policy_id": "l3-policy-id"
      }
    }
  }
}
'''

l3_policy_template = '''
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test neutron l3 policy",
  "Parameters" : {},
  "Resources" : {
    "l3_policy": {
      "Type": "OS::Neutron::L3Policy",
      "Properties": {
        "name": "test-l3-policy",
        "description": "test L3 policy resource",
        "ip_version": "4",
        "ip_pool": "10.20.20.0",
        "subnet_prefix_length": 24
      }
    }
  }
}
'''

policy_classifier_template = '''
{
 "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test neutron policy classifier",
  "Parameters" : {},
  "Resources" : {
  "policy_classifier": {
      "Type": "OS::Neutron::PolicyClassifier",
      "Properties": {
                "name": "test-policy-classifier",
                "description": "test policy classifier resource",
                "protocol": "tcp",
                "port_range": "8000-9000",
                "direction": "bi"
      }
    }
  }
}
'''

policy_action_template = '''
{
 "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test neutron policy action",
  "Parameters" : {},
  "Resources" : {
  "policy_action": {
      "Type": "OS::Neutron::PolicyAction",
      "Properties": {
                "name": "test-policy-action",
                "description": "test policy action resource",
                "action_type": "redirect",
                "action_value": "7890"
      }
    }
  }
}
'''

policy_rule_template = '''
{
 "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test neutron policy rule",
  "Parameters" : {},
  "Resources" : {
  "policy_rule": {
      "Type": "OS::Neutron::PolicyRule",
      "Properties": {
          "name": "test-policy-rule",
          "description": "test policy rule resource",
          "enabled": True,
          "policy_classifier_id": "7890",
          "policy_actions": ['3456', '1234']
      }
    }
  }
}
'''

contract_template = '''
{
 "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test contract",
  "Parameters" : {},
  "Resources" : {
  "contract": {
      "Type": "OS::Neutron::Contract",
      "Properties": {
          "name": "test-contract",
          "description": "test contract resource",
          "parent_id": "3456",
          "child_contracts": ["7890", "1234"],
          "policy_rules": ["2345", "6789"]
      }
    }
  }
}
'''


class EndpointTest(HeatTestCase):

    def setUp(self):
        super(EndpointTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_endpoint')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_endpoint')
        self.m.StubOutWithMock(gbpclient.Client, 'show_endpoint')
        self.m.StubOutWithMock(gbpclient.Client, 'update_endpoint')
        self.stub_keystoneclient()

    def create_endpoint(self):
        gbpclient.Client.create_endpoint({
            'endpoint': {
                'name': 'test-endpoint',
                'endpoint_group_id': 'epg-id',
                "description": "test endpoint resource"
            }
        }).AndReturn({'endpoint': {'id': '5678'}})

        snippet = template_format.parse(endpoint_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        return grouppolicy.Endpoint(
            'endpoint', resource_defns['endpoint'], stack)

    def test_create(self):
        rsrc = self.create_endpoint()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_endpoint({
            'endpoint': {
                'name': 'test-endpoint',
                'endpoint_group_id': 'epg-id',
                "description": "test endpoint resource"
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(endpoint_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        rsrc = grouppolicy.Endpoint(
            'endpoint', resource_defns['endpoint'], stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_endpoint('5678')
        gbpclient.Client.show_endpoint('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_endpoint()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_endpoint('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_endpoint()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_endpoint('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_endpoint()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_attribute(self):
        rsrc = self.create_endpoint()
        gbpclient.Client.show_endpoint('5678').MultipleTimes(
        ).AndReturn(
            {'endpoint': {'port_id': '1234'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual('1234', rsrc.FnGetAtt('port_id'))
        self.m.VerifyAll()

    def test_attribute_failed(self):
        rsrc = self.create_endpoint()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.InvalidTemplateAttribute,
                                  rsrc.FnGetAtt, 'l2_policy_id')
        self.assertEqual(
            'The Referenced Attribute (endpoint l2_policy_id) is '
            'incorrect.', str(error))
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_endpoint()
        gbpclient.Client.update_endpoint(
            '5678', {'endpoint': {'endpoint_group_id': 'epg_id_update'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['endpoint_group_id'] = 'epg_id_update'
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class EndpointGroupTest(HeatTestCase):

    def setUp(self):
        super(EndpointGroupTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_endpoint_group')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_endpoint_group')
        self.m.StubOutWithMock(gbpclient.Client, 'show_endpoint_group')
        self.m.StubOutWithMock(gbpclient.Client, 'update_endpoint_group')
        self.stub_keystoneclient()

    def create_endpoint_group(self):
        gbpclient.Client.create_endpoint_group({
            "endpoint_group": {
                "name": "test-endpoint-group",
                "description": "test endpoint group resource",
                "l2_policy_id": "l2-policy-id",
                "provided_contracts": {
                    "contract1": "scope1",
                    "contract2": "scope2"
                },
                "consumed_contracts": {
                    "contract3": "scope3",
                    "contract4": "scope4"
                }
            }
        }).AndReturn({'endpoint_group': {'id': '5678'}})

        snippet = template_format.parse(endpoint_group_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        return grouppolicy.EndpointGroup(
            'endpoint_group', resource_defns['endpoint_group'], stack)

    def test_create(self):
        rsrc = self.create_endpoint_group()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_endpoint_group({
            "endpoint_group": {
                "name": "test-endpoint-group",
                "description": "test endpoint group resource",
                "l2_policy_id": "l2-policy-id",
                "provided_contracts": {
                    "contract1": "scope1",
                    "contract2": "scope2"
                },
                "consumed_contracts": {
                    "contract3": "scope3",
                    "contract4": "scope4"
                }
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(endpoint_group_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        rsrc = grouppolicy.EndpointGroup(
            'endpoint_group', resource_defns['endpoint_group'], stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_endpoint_group('5678')
        gbpclient.Client.show_endpoint_group('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_endpoint_group()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_endpoint_group('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_endpoint_group()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_endpoint_group('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_endpoint_group()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_endpoint_group()
        gbpclient.Client.update_endpoint_group(
            '5678', {'endpoint_group': {'l2_policy_id': 'l2_id_update'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['l2_policy_id'] = 'l2_id_update'
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class L2PolicyTest(HeatTestCase):

    def setUp(self):
        super(L2PolicyTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_l2_policy')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_l2_policy')
        self.m.StubOutWithMock(gbpclient.Client, 'show_l2_policy')
        self.m.StubOutWithMock(gbpclient.Client, 'update_l2_policy')
        self.stub_keystoneclient()

    def create_l2_policy(self):
        gbpclient.Client.create_l2_policy({
            'l2_policy': {
                "name": "test-l2-policy",
                "description": "test L2 policy resource",
                "l3_policy_id": "l3-policy-id"
            }
        }).AndReturn({'l2_policy': {'id': '5678'}})

        snippet = template_format.parse(l2_policy_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        return grouppolicy.L2Policy(
            'l2_policy', resource_defns['l2_policy'], stack)

    def test_create(self):
        rsrc = self.create_l2_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_l2_policy({
            'l2_policy': {
                "name": "test-l2-policy",
                "description": "test L2 policy resource",
                "l3_policy_id": "l3-policy-id"
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(l2_policy_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        rsrc = grouppolicy.L2Policy(
            'l2_policy', resource_defns['l2_policy'], stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_l2_policy('5678')
        gbpclient.Client.show_l2_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_l2_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_l2_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_l2_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_l2_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_l2_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_l2_policy()
        gbpclient.Client.update_l2_policy(
            '5678', {'l2_policy': {'l3_policy_id': 'l3_id_update'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['l3_policy_id'] = 'l3_id_update'
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class L3PolicyTest(HeatTestCase):

    def setUp(self):
        super(L3PolicyTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_l3_policy')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_l3_policy')
        self.m.StubOutWithMock(gbpclient.Client, 'show_l3_policy')
        self.m.StubOutWithMock(gbpclient.Client, 'update_l3_policy')
        self.stub_keystoneclient()

    def create_l3_policy(self):
        gbpclient.Client.create_l3_policy({
            'l3_policy': {
                "name": "test-l3-policy",
                "description": "test L3 policy resource",
                "ip_version": "4",
                "ip_pool": "10.20.20.0",
                "subnet_prefix_length": 24
            }
        }).AndReturn({'l3_policy': {'id': '5678'}})

        snippet = template_format.parse(l3_policy_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        return grouppolicy.L3Policy(
            'l3_policy', resource_defns['l3_policy'], stack)

    def test_create(self):
        rsrc = self.create_l3_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_l3_policy({
            'l3_policy': {
                "name": "test-l3-policy",
                "description": "test L3 policy resource",
                "ip_version": "4",
                "ip_pool": "10.20.20.0",
                "subnet_prefix_length": 24
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(l3_policy_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        rsrc = grouppolicy.L3Policy(
            'l3_policy', resource_defns['l3_policy'], stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_l3_policy('5678')
        gbpclient.Client.show_l3_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_l3_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_l3_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_l3_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_l3_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_l3_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_l3_policy()
        gbpclient.Client.update_l3_policy(
            '5678', {'l3_policy': {'subnet_prefix_length': 28}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['subnet_prefix_length'] = 28
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class PolicyClassifierTest(HeatTestCase):

    def setUp(self):
        super(PolicyClassifierTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client,
                               'create_policy_classifier')
        self.m.StubOutWithMock(gbpclient.Client,
                               'delete_policy_classifier')
        self.m.StubOutWithMock(gbpclient.Client,
                               'show_policy_classifier')
        self.m.StubOutWithMock(gbpclient.Client,
                               'update_policy_classifier')
        self.stub_keystoneclient()

    def create_policy_classifier(self):
        gbpclient.Client.create_policy_classifier({
            'policy_classifier': {
                "name": "test-policy-classifier",
                "description": "test policy classifier resource",
                "protocol": "tcp",
                "port_range": "8000-9000",
                "direction": "bi"
            }
        }).AndReturn({'policy_classifier': {'id': '5678'}})

        snippet = template_format.parse(policy_classifier_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        return grouppolicy.PolicyClassifier(
            'policy_classifier', resource_defns['policy_classifier'], stack)

    def test_create(self):
        rsrc = self.create_policy_classifier()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_policy_classifier({
            'policy_classifier': {
                "name": "test-policy-classifier",
                "description": "test policy classifier resource",
                "protocol": "tcp",
                "port_range": "8000-9000",
                "direction": "bi"
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(policy_classifier_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        rsrc = grouppolicy.PolicyClassifier(
            'policy_classifier', resource_defns['policy_classifier'], stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_policy_classifier('5678')
        gbpclient.Client.show_policy_classifier('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_classifier()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_policy_classifier('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_classifier()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_policy_classifier('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_policy_classifier()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_policy_classifier()
        gbpclient.Client.update_policy_classifier(
            '5678', {'policy_classifier': {'protocol': 'udp'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['protocol'] = 'udp'
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class PolicyActionTest(HeatTestCase):

    def setUp(self):
        super(PolicyActionTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_policy_action')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_policy_action')
        self.m.StubOutWithMock(gbpclient.Client, 'show_policy_action')
        self.m.StubOutWithMock(gbpclient.Client, 'update_policy_action')
        self.stub_keystoneclient()

    def create_policy_action(self):
        gbpclient.Client.create_policy_action({
            'policy_action': {
                "name": "test-policy-action",
                "description": "test policy action resource",
                "action_type": "redirect",
                "action_value": "7890"
            }
        }).AndReturn({'policy_action': {'id': '5678'}})

        snippet = template_format.parse(policy_action_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        return grouppolicy.PolicyAction(
            'policy_action', resource_defns['policy_action'], stack)

    def test_create(self):
        rsrc = self.create_policy_action()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_policy_action({
            'policy_action': {
                "name": "test-policy-action",
                "description": "test policy action resource",
                "action_type": "redirect",
                "action_value": "7890"
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(policy_action_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        rsrc = grouppolicy.PolicyAction(
            'policy_action', resource_defns['policy_action'], stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_policy_action('5678')
        gbpclient.Client.show_policy_action('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_action()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_policy_action('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_action()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_policy_action('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_policy_action()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_policy_action()
        gbpclient.Client.update_policy_action(
            '5678', {'policy_action': {'action_type': 'allow'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['action_type'] = 'allow'
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class PolicyRuleTest(HeatTestCase):

    def setUp(self):
        super(PolicyRuleTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_policy_rule')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_policy_rule')
        self.m.StubOutWithMock(gbpclient.Client, 'show_policy_rule')
        self.m.StubOutWithMock(gbpclient.Client, 'update_policy_rule')
        self.stub_keystoneclient()

    def create_policy_rule(self):
        gbpclient.Client.create_policy_rule({
            'policy_rule': {
                "name": "test-policy-rule",
                "description": "test policy rule resource",
                "enabled": True,
                "policy_classifier_id": "7890",
                "policy_actions": ['3456', '1234']
            }
        }).AndReturn({'policy_rule': {'id': '5678'}})

        snippet = template_format.parse(policy_rule_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        return grouppolicy.PolicyRule(
            'policy_rule', resource_defns['policy_rule'], stack)

    def test_create(self):
        rsrc = self.create_policy_rule()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_policy_rule({
            'policy_rule': {
                "name": "test-policy-rule",
                "description": "test policy rule resource",
                "enabled": True,
                "policy_classifier_id": "7890",
                "policy_actions": ['3456', '1234']
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(policy_rule_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        rsrc = grouppolicy.PolicyRule(
            'policy_rule', resource_defns['policy_rule'], stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_policy_rule('5678')
        gbpclient.Client.show_policy_rule('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_rule()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_policy_rule('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_rule()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_policy_rule('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_policy_rule()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_policy_rule()
        gbpclient.Client.update_policy_rule(
            '5678', {'policy_rule': {'enabled': False}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['enabled'] = False
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class ContractTest(HeatTestCase):

    def setUp(self):
        super(ContractTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_contract')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_contract')
        self.m.StubOutWithMock(gbpclient.Client, 'show_contract')
        self.m.StubOutWithMock(gbpclient.Client, 'update_contract')
        self.stub_keystoneclient()

    def create_contract(self):
        gbpclient.Client.create_contract({
            'contract': {
                "name": "test-contract",
                "description": "test contract resource",
                "parent_id": "3456",
                "child_contracts": ["7890", "1234"],
                "policy_rules": ["2345", "6789"]
            }
        }).AndReturn({'contract': {'id': '5678'}})

        snippet = template_format.parse(contract_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        return grouppolicy.Contract(
            'contract', resource_defns['contract'], stack)

    def test_create(self):
        rsrc = self.create_contract()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_contract({
            'contract': {
                "name": "test-contract",
                "description": "test contract resource",
                "parent_id": "3456",
                "child_contracts": ["7890", "1234"],
                "policy_rules": ["2345", "6789"]
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(contract_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        rsrc = grouppolicy.Contract(
            'contract', resource_defns['contract'], stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_contract('5678')
        gbpclient.Client.show_contract('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_contract()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_contract('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_contract()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_contract('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_contract()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_contract()
        gbpclient.Client.update_contract(
            '5678', {'contract': {'child_contracts': ["1234"]}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['child_contracts'] = ["1234"]
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()
