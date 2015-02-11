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

from gbpautomation.heat.engine.resources import grouppolicy
from gbpclient.v2_0 import client as gbpclient
from heat.common import exception
from heat.common import template_format
from heat.tests.common import HeatTestCase

from heat.engine import scheduler
from heat.tests import utils


policy_target_template = '''
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test neutron policy target resource",
  "Parameters" : {},
  "Resources" : {
    "policy_target": {
      "Type": "OS::GroupBasedPolicy::PolicyTarget",
      "Properties": {
        "name": "test-policy-target",
        "policy_target_group_id": "ptg-id",
        "description": "test policy target resource"
      }
    }
  }
}
'''

policy_target_group_template = '''
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test neutron policy target group resource",
  "Parameters" : {},
  "Resources" : {
    "policy_target_group": {
      "Type": "OS::GroupBasedPolicy::PolicyTargetGroup",
      "Properties": {
        "name": "test-policy-target-group",
        "description": "test policy target group resource",
        "l2_policy_id": "l2-policy-id",
        "provided_policy_rule_sets": [
            {"policy_rule_set_id": "policy_rule_set1",
             "policy_rule_set_scope": "scope1"},
            {"policy_rule_set_id": "policy_rule_set2",
             "policy_rule_set_scope": "scope2"}
        ],
        "consumed_policy_rule_sets": [
            {"policy_rule_set_id": "policy_rule_set3",
             "policy_rule_set_scope": "scope3"},
            {"policy_rule_set_id": "policy_rule_set4",
             "policy_rule_set_scope": "scope4"}
        ],
        "shared": True
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
      "Type": "OS::GroupBasedPolicy::L2Policy",
      "Properties": {
        "name": "test-l2-policy",
        "description": "test L2 policy resource",
        "l3_policy_id": "l3-policy-id",
        "shared": True
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
      "Type": "OS::GroupBasedPolicy::L3Policy",
      "Properties": {
        "name": "test-l3-policy",
        "description": "test L3 policy resource",
        "ip_version": "4",
        "ip_pool": "10.20.20.0",
        "external_segments": [
            {"external_segment_id": "es1",
             "allocated_address": "1.1.1.1"},
        ],
        "subnet_prefix_length": 24,
        "shared": True
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
      "Type": "OS::GroupBasedPolicy::PolicyClassifier",
      "Properties": {
                "name": "test-policy-classifier",
                "description": "test policy classifier resource",
                "protocol": "tcp",
                "port_range": "8000-9000",
                "direction": "bi",
                "shared": True
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
      "Type": "OS::GroupBasedPolicy::PolicyAction",
      "Properties": {
                "name": "test-policy-action",
                "description": "test policy action resource",
                "action_type": "redirect",
                "action_value": "7890",
                "shared": True
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
      "Type": "OS::GroupBasedPolicy::PolicyRule",
      "Properties": {
          "name": "test-policy-rule",
          "description": "test policy rule resource",
          "enabled": True,
          "policy_classifier_id": "7890",
          "policy_actions": ['3456', '1234'],
          "shared": True
      }
    }
  }
}
'''

policy_rule_set_template = '''
{
 "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test policy rule set",
  "Parameters" : {},
  "Resources" : {
  "policy_rule_set": {
      "Type": "OS::GroupBasedPolicy::PolicyRuleSet",
      "Properties": {
          "name": "test-policy-rule-set",
          "description": "test policy rule set resource",
          "parent_id": "3456",
          "child_policy_rule_sets": ["7890", "1234"],
          "policy_rules": ["2345", "6789"],
          "shared": True
      }
    }
  }
}
'''

network_service_policy_template = '''
{
 "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test network service policy",
  "Parameters" : {},
  "Resources" : {
  "network_service_policy": {
      "Type": "OS::GroupBasedPolicy::NetworkServicePolicy",
      "Properties": {
          "name": "test-nsp",
          "description": "test NSP resource",
          "network_service_params": [{'type': 'ip_single', 'name': 'vip',
                                      'value': 'self_subnet'}],
          "shared": True
      }
    }
  }
}
'''

external_policy_template = '''
{
 "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test external policy",
  "Parameters" : {},
  "Resources" : {
  "external_policy": {
      "Type": "OS::GroupBasedPolicy::ExternalPolicy",
      "Properties": {
          "name": "test-ep",
          "description": "test EP resource",
          "external_segments": ['1234'],
          "provided_policy_rule_sets": [{
              "policy_rule_set_id": '2345',
              "policy_rule_set_scope": "scope1"
          },
          {
              "policy_rule_set_id": '8901',
              "policy_rule_set_scope": "scope2"
          }],
          "consumed_policy_rule_sets": [{
              "policy_rule_set_id": '9012',
              "policy_rule_set_scope": "scope3"
          },
          {
              "policy_rule_set_id": '9210',
              "policy_rule_set_scope": "scope4"
          }],
          "shared": True
      }
    }
  }
}
'''

external_segment_template = '''
{
 "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test external segment",
  "Parameters" : {},
  "Resources" : {
  "external_segment": {
      "Type": "OS::GroupBasedPolicy::ExternalSegment",
      "Properties": {
          "name": "test-es",
          "description": "test ES resource",
          "ip_version": '6',
          "cidr": "192.168.0.0/24",
          "subnet_id": "some-subnet-id",
          "external_routes": [{
              "destination": "0.0.0.0/0",
              "nexthop": "null"
              }
          ],
          "port_address_translation": True,
          "shared": True
      }
    }
  }
}
'''

nat_pool_template = '''
{
 "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test NAT pool",
  "Parameters" : {},
  "Resources" : {
  "nat_pool": {
      "Type": "OS::GroupBasedPolicy::NATPool",
      "Properties": {
          "name": "test-nat-pool",
          "description": "test NP resource",
          "ip_version": '6',
          "ip_pool": "192.168.0.0/24",
          "external_segment_id": '1234',
          "shared": True
      }
    }
  }
}
'''


class PolicyTargetTest(HeatTestCase):

    def setUp(self):
        super(PolicyTargetTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_policy_target')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_policy_target')
        self.m.StubOutWithMock(gbpclient.Client, 'show_policy_target')
        self.m.StubOutWithMock(gbpclient.Client, 'update_policy_target')
        self.stub_keystoneclient()

    def create_policy_target(self):
        gbpclient.Client.create_policy_target({
            'policy_target': {
                'name': 'test-policy-target',
                'policy_target_group_id': 'ptg-id',
                "description": "test policy target resource"
            }
        }).AndReturn({'policy_target': {'id': '5678'}})

        snippet = template_format.parse(policy_target_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.PolicyTarget(
            'policy_target', resource_defns['policy_target'], self.stack)

    def test_create(self):
        rsrc = self.create_policy_target()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_policy_target({
            'policy_target': {
                'name': 'test-policy-target',
                'policy_target_group_id': 'ptg-id',
                "description": "test policy target resource"
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(policy_target_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.PolicyTarget(
            'policy_target', resource_defns['policy_target'], self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_policy_target('5678')
        gbpclient.Client.show_policy_target('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_target()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_policy_target('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_target()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_policy_target('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_policy_target()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_attribute(self):
        rsrc = self.create_policy_target()
        gbpclient.Client.show_policy_target('5678').MultipleTimes(
        ).AndReturn(
            {'policy_target': {'port_id': '1234'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual('1234', rsrc.FnGetAtt('port_id'))
        self.m.VerifyAll()

    def test_attribute_failed(self):
        rsrc = self.create_policy_target()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.InvalidTemplateAttribute,
                                  rsrc.FnGetAtt, 'l2_policy_id')
        self.assertEqual(
            'The Referenced Attribute (policy_target l2_policy_id) is '
            'incorrect.', six.text_type(error))
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_policy_target()
        gbpclient.Client.update_policy_target(
            '5678', {'policy_target': {'policy_target_group_id':
                                       'ptg_id_update'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['policy_target_group_id'] = (
            'ptg_id_update')
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class PolicyTargetGroupTest(HeatTestCase):

    def setUp(self):
        super(PolicyTargetGroupTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_policy_target_group')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_policy_target_group')
        self.m.StubOutWithMock(gbpclient.Client, 'show_policy_target_group')
        self.m.StubOutWithMock(gbpclient.Client, 'update_policy_target_group')
        self.stub_keystoneclient()

    def create_policy_target_group(self):
        gbpclient.Client.create_policy_target_group({
            "policy_target_group": {
                "name": "test-policy-target-group",
                "description": "test policy target group resource",
                "l2_policy_id": "l2-policy-id",
                "provided_policy_rule_sets": {
                    "policy_rule_set1": "scope1",
                    "policy_rule_set2": "scope2"
                },
                "consumed_policy_rule_sets": {
                    "policy_rule_set3": "scope3",
                    "policy_rule_set4": "scope4"
                },
                "shared": True
            }
        }).AndReturn({'policy_target_group': {'id': '5678'}})

        snippet = template_format.parse(policy_target_group_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.PolicyTargetGroup(
            'policy_target_group', resource_defns['policy_target_group'],
            self.stack)

    def test_create(self):
        rsrc = self.create_policy_target_group()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_policy_target_group({
            "policy_target_group": {
                "name": "test-policy-target-group",
                "description": "test policy target group resource",
                "l2_policy_id": "l2-policy-id",
                "provided_policy_rule_sets": {
                    "policy_rule_set1": "scope1",
                    "policy_rule_set2": "scope2"
                },
                "consumed_policy_rule_sets": {
                    "policy_rule_set3": "scope3",
                    "policy_rule_set4": "scope4"
                },
                "shared": True
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(policy_target_group_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.PolicyTargetGroup(
            'policy_target_group', resource_defns['policy_target_group'],
            self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_policy_target_group('5678')
        gbpclient.Client.show_policy_target_group('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_target_group()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_policy_target_group('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_target_group()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_policy_target_group('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_policy_target_group()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_policy_target_group()
        gbpclient.Client.update_policy_target_group(
            '5678', {'policy_target_group': {'l2_policy_id': 'l2_id_update'}})
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
                "l3_policy_id": "l3-policy-id",
                "shared": True
            }
        }).AndReturn({'l2_policy': {'id': '5678'}})

        snippet = template_format.parse(l2_policy_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.L2Policy(
            'l2_policy', resource_defns['l2_policy'], self.stack)

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
                "l3_policy_id": "l3-policy-id",
                "shared": True
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(l2_policy_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.L2Policy(
            'l2_policy', resource_defns['l2_policy'], self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
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
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
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
                "subnet_prefix_length": 24,
                "external_segments": {"es1": "1.1.1.1"},
                "shared": True
            }
        }).AndReturn({'l3_policy': {'id': '5678'}})

        snippet = template_format.parse(l3_policy_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.L3Policy(
            'l3_policy', resource_defns['l3_policy'], self.stack)

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
                "subnet_prefix_length": 24,
                "external_segments": {"es1": "1.1.1.1"},
                "shared": True
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(l3_policy_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.L3Policy(
            'l3_policy', resource_defns['l3_policy'], self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
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
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_l3_policy()
        gbpclient.Client.update_l3_policy(
            '5678', {'l3_policy': {'subnet_prefix_length': 28,
                                   'external_segments':
                                   {'es2': '2.1.1.1'}}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['subnet_prefix_length'] = 28
        update_template['Properties']['external_segments'] = [
            {'external_segment_id': 'es2',
             'allocated_address': '2.1.1.1'}]
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
                "direction": "bi",
                "shared": True
            }
        }).AndReturn({'policy_classifier': {'id': '5678'}})

        snippet = template_format.parse(policy_classifier_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.PolicyClassifier(
            'policy_classifier', resource_defns['policy_classifier'],
            self.stack)

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
                "direction": "bi",
                "shared": True
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(policy_classifier_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.PolicyClassifier(
            'policy_classifier', resource_defns['policy_classifier'],
            self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
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
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
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
                "action_value": "7890",
                "shared": True
            }
        }).AndReturn({'policy_action': {'id': '5678'}})

        snippet = template_format.parse(policy_action_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.PolicyAction(
            'policy_action', resource_defns['policy_action'], self.stack)

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
                "action_value": "7890",
                "shared": True
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(policy_action_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.PolicyAction(
            'policy_action', resource_defns['policy_action'], self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
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
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
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
                "policy_actions": ['3456', '1234'],
                "shared": True
            }
        }).AndReturn({'policy_rule': {'id': '5678'}})

        snippet = template_format.parse(policy_rule_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.PolicyRule(
            'policy_rule', resource_defns['policy_rule'], self.stack)

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
                "policy_actions": ['3456', '1234'],
                "shared": True
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(policy_rule_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.PolicyRule(
            'policy_rule', resource_defns['policy_rule'], self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
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
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
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


class PolicyRuleSetTest(HeatTestCase):

    def setUp(self):
        super(PolicyRuleSetTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_policy_rule_set')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_policy_rule_set')
        self.m.StubOutWithMock(gbpclient.Client, 'show_policy_rule_set')
        self.m.StubOutWithMock(gbpclient.Client, 'update_policy_rule_set')
        self.stub_keystoneclient()

    def create_policy_rule_set(self):
        gbpclient.Client.create_policy_rule_set({
            'policy_rule_set': {
                "name": "test-policy-rule-set",
                "description": "test policy rule set resource",
                "parent_id": "3456",
                "child_policy_rule_sets": ["7890", "1234"],
                "policy_rules": ["2345", "6789"],
                "shared": True
            }
        }).AndReturn({'policy_rule_set': {'id': '5678'}})

        snippet = template_format.parse(policy_rule_set_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.PolicyRuleSet(
            'policy_rule_set', resource_defns['policy_rule_set'], self.stack)

    def test_create(self):
        rsrc = self.create_policy_rule_set()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_policy_rule_set({
            'policy_rule_set': {
                "name": "test-policy-rule-set",
                "description": "test policy rule set resource",
                "parent_id": "3456",
                "child_policy_rule_sets": ["7890", "1234"],
                "policy_rules": ["2345", "6789"],
                "shared": True
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(policy_rule_set_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.PolicyRuleSet(
            'policy_rule_set', resource_defns['policy_rule_set'], self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_policy_rule_set('5678')
        gbpclient.Client.show_policy_rule_set('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_rule_set()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_policy_rule_set('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_policy_rule_set()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_policy_rule_set('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_policy_rule_set()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_policy_rule_set()
        gbpclient.Client.update_policy_rule_set(
            '5678', {'policy_rule_set': {'child_policy_rule_sets': ["1234"]}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['child_policy_rule_sets'] = ["1234"]
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class NetworkServicePolicyTest(HeatTestCase):

    def setUp(self):
        super(NetworkServicePolicyTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client,
                               'create_network_service_policy')
        self.m.StubOutWithMock(gbpclient.Client,
                               'delete_network_service_policy')
        self.m.StubOutWithMock(gbpclient.Client,
                               'show_network_service_policy')
        self.m.StubOutWithMock(gbpclient.Client,
                               'update_network_service_policy')
        self.stub_keystoneclient()

    def create_network_service_policy(self):
        gbpclient.Client.create_network_service_policy({
            'network_service_policy': {
                "name": "test-nsp",
                "description": "test NSP resource",
                "network_service_params": [
                    {'type': 'ip_single', 'name': 'vip',
                     'value': 'self_subnet'}],
                "shared": True
            }
        }).AndReturn({'network_service_policy': {'id': '5678'}})

        snippet = template_format.parse(network_service_policy_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.NetworkServicePolicy(
            'network_service_policy',
            resource_defns['network_service_policy'], self.stack)

    def test_create(self):
        rsrc = self.create_network_service_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_network_service_policy({
            'network_service_policy': {
                "name": "test-nsp",
                "description": "test NSP resource",
                "network_service_params": [
                    {'type': 'ip_single', 'name': 'vip',
                     'value': 'self_subnet'}],
                "shared": True
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(network_service_policy_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.NetworkServicePolicy(
            'network_service_policy',
            resource_defns['network_service_policy'], self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_network_service_policy('5678')
        gbpclient.Client.show_network_service_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_network_service_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_network_service_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_network_service_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_network_service_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_network_service_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_network_service_policy()
        gbpclient.Client.update_network_service_policy(
            '5678', {'network_service_policy':
                     {'network_service_params': [{'name': 'vip-update'}]}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['network_service_params'] = [
            {'name': 'vip-update'}]
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class ExternalPolicyTest(HeatTestCase):

    def setUp(self):
        super(ExternalPolicyTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client,
                               'create_external_policy')
        self.m.StubOutWithMock(gbpclient.Client,
                               'delete_external_policy')
        self.m.StubOutWithMock(gbpclient.Client,
                               'show_external_policy')
        self.m.StubOutWithMock(gbpclient.Client,
                               'update_external_policy')
        self.stub_keystoneclient()

    def create_external_policy(self):
        gbpclient.Client.create_external_policy({
            'external_policy': {
                "name": "test-ep",
                "description": "test EP resource",
                "external_segments": ['1234'],
                "provided_policy_rule_sets": {
                    '2345': "scope1",
                    '8901': "scope2"
                },
                "consumed_policy_rule_sets": {
                    '9012': "scope3",
                    '9210': "scope4"
                },
                "shared": True
            }
        }).AndReturn({'external_policy': {'id': '5678'}})

        snippet = template_format.parse(external_policy_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.ExternalPolicy(
            'external_policy',
            resource_defns['external_policy'], self.stack)

    def test_create(self):
        rsrc = self.create_external_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_external_policy({
            'external_policy': {
                "name": "test-ep",
                "description": "test EP resource",
                "external_segments": ['1234'],
                "provided_policy_rule_sets": {
                    '2345': "scope1",
                    '8901': "scope2"
                },
                "consumed_policy_rule_sets": {
                    '9012': "scope3",
                    '9210': "scope4"
                },
                "shared": True
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(external_policy_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.ExternalPolicy(
            'external_policy',
            resource_defns['external_policy'], self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_external_policy('5678')
        gbpclient.Client.show_external_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_external_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_external_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_external_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_external_policy('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_external_policy()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_external_policy()
        gbpclient.Client.update_external_policy(
            '5678', {'external_policy':
                     {'external_segments': ['9876']}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['external_segments'] = [
            '9876']
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class ExternalSegmentTest(HeatTestCase):

    def setUp(self):
        super(ExternalSegmentTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client,
                               'create_external_segment')
        self.m.StubOutWithMock(gbpclient.Client,
                               'delete_external_segment')
        self.m.StubOutWithMock(gbpclient.Client,
                               'show_external_segment')
        self.m.StubOutWithMock(gbpclient.Client,
                               'update_external_segment')
        self.stub_keystoneclient()

    def create_external_segment(self):
        gbpclient.Client.create_external_segment({
            'external_segment': {
                "name": "test-es",
                "description": "test ES resource",
                "ip_version": '6',
                "cidr": "192.168.0.0/24",
                "subnet_id": "some-subnet-id",
                "external_routes": [{
                    "destination": "0.0.0.0/0",
                    "nexthop": "null"
                }],
                "port_address_translation": True,
                "shared": True
            }
        }).AndReturn({'external_segment': {'id': '5678'}})

        snippet = template_format.parse(external_segment_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.ExternalSegment(
            'external_segment',
            resource_defns['external_segment'], self.stack)

    def test_create(self):
        rsrc = self.create_external_segment()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_external_segment({
            'external_segment': {
                "name": "test-es",
                "description": "test ES resource",
                "ip_version": '6',
                "cidr": "192.168.0.0/24",
                "subnet_id": "some-subnet-id",
                "external_routes": [{
                    "destination": "0.0.0.0/0",
                    "nexthop": "null"
                }],
                "port_address_translation": True,
                "shared": True
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(external_segment_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.ExternalSegment(
            'external_segment',
            resource_defns['external_segment'], self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_external_segment('5678')
        gbpclient.Client.show_external_segment('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_external_segment()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_external_segment('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_external_segment()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_external_segment('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_external_segment()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_external_segment()
        gbpclient.Client.update_external_segment(
            '5678', {'external_segment':
                     {"port_address_translation": False}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['port_address_translation'] = False
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class NATPoolTest(HeatTestCase):

    def setUp(self):
        super(NATPoolTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client,
                               'create_nat_pool')
        self.m.StubOutWithMock(gbpclient.Client,
                               'delete_nat_pool')
        self.m.StubOutWithMock(gbpclient.Client,
                               'show_nat_pool')
        self.m.StubOutWithMock(gbpclient.Client,
                               'update_nat_pool')
        self.stub_keystoneclient()

    def create_nat_pool(self):
        gbpclient.Client.create_nat_pool({
            'nat_pool': {
                "name": "test-nat-pool",
                "description": "test NP resource",
                "ip_version": '6',
                "ip_pool": "192.168.0.0/24",
                "external_segment_id": '1234',
                "shared": True
            }
        }).AndReturn({'nat_pool': {'id': '5678'}})

        snippet = template_format.parse(nat_pool_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return grouppolicy.NATPool(
            'nat_pool',
            resource_defns['nat_pool'], self.stack)

    def test_create(self):
        rsrc = self.create_nat_pool()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_nat_pool({
            'nat_pool': {
                "name": "test-nat-pool",
                "description": "test NP resource",
                "ip_version": '6',
                "ip_pool": "192.168.0.0/24",
                "external_segment_id": '1234',
                "shared": True
            }
        }).AndRaise(grouppolicy.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(nat_pool_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = grouppolicy.NATPool(
            'nat_pool',
            resource_defns['nat_pool'], self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_nat_pool('5678')
        gbpclient.Client.show_nat_pool('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_nat_pool()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_nat_pool('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=404))

        rsrc = self.create_nat_pool()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_nat_pool('5678').AndRaise(
            grouppolicy.NeutronClientException(status_code=400))

        rsrc = self.create_nat_pool()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_nat_pool()
        gbpclient.Client.update_nat_pool(
            '5678', {'nat_pool':
                     {"external_segment_id": '9876'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['external_segment_id'] = '9876'
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()
