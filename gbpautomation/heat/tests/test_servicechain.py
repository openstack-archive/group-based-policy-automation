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

from gbpautomation.heat.engine.resources import servicechain
from gbpclient.v2_0 import client as gbpclient
from heat.common import exception
from heat.common import template_format
from heat.tests.common import HeatTestCase

from heat.engine import scheduler
from heat.tests import utils


servicechain_node_template = '''
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test GBP service chain node",
  "Parameters" : {},
  "Resources" : {
    "servicechain_node": {
      "Type": "OS::GroupBasedPolicy::ServiceChainNode",
      "Properties": {
        "name": "test-sc-node",
        "description": "test service chain node resource",
        "shared": True,
        "service_profile_id": "profile-id",
        "config": "{'name': 'sc_node_config'}"
      }
    }
  }
}
'''

servicechain_spec_template = '''
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test GBP service chain spec",
  "Parameters" : {},
  "Resources" : {
    "servicechain_spec": {
      "Type": "OS::GroupBasedPolicy::ServiceChainSpec",
      "Properties": {
        "name": "test-sc-spec",
        "description": "test service chain spec resource",
        "shared": True,
        "nodes": ["1234", "7890"]
      }
    }
  }
}
'''

service_profile_template = '''
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test GBP service profile",
  "Parameters" : {},
  "Resources" : {
    "service_profile": {
      "Type": "OS::GroupBasedPolicy::ServiceProfile",
      "Properties": {
        "name": "test-svc-profile",
        "description": "test service profile resource",
        "vendor": "test vendor",
        "service_type": "test type",
        "insertion_mode": "l2",
        "service_flavor": "test flavor",
        "shared": True
      }
    }
  }
}
'''


class ServiceChainNodeTest(HeatTestCase):

    def setUp(self):
        super(ServiceChainNodeTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_servicechain_node')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_servicechain_node')
        self.m.StubOutWithMock(gbpclient.Client, 'show_servicechain_node')
        self.m.StubOutWithMock(gbpclient.Client, 'update_servicechain_node')
        self.stub_keystoneclient()

    def create_servicechain_node(self):
        gbpclient.Client.create_servicechain_node({
            'servicechain_node': {
                "name": "test-sc-node",
                "description": "test service chain node resource",
                "service_profile_id": "profile-id",
                "shared": True,
                "config": "{'name': 'sc_node_config'}"
            }
        }).AndReturn({'servicechain_node': {'id': '5678'}})

        snippet = template_format.parse(servicechain_node_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return servicechain.ServiceChainNode(
            'servicechain_node', resource_defns['servicechain_node'],
            self.stack)

    def test_create(self):
        rsrc = self.create_servicechain_node()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_servicechain_node({
            'servicechain_node': {
                "name": "test-sc-node",
                "description": "test service chain node resource",
                "service_profile_id": "profile-id",
                "shared": True,
                "config": "{'name': 'sc_node_config'}"
            }
        }).AndRaise(servicechain.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(servicechain_node_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = servicechain.ServiceChainNode(
            'servicechain_node', resource_defns['servicechain_node'],
            self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: resources.servicechain_node: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_servicechain_node('5678')
        gbpclient.Client.show_servicechain_node('5678').AndRaise(
            servicechain.NeutronClientException(status_code=404))

        rsrc = self.create_servicechain_node()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_servicechain_node('5678').AndRaise(
            servicechain.NeutronClientException(status_code=404))

        rsrc = self.create_servicechain_node()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_servicechain_node('5678').AndRaise(
            servicechain.NeutronClientException(status_code=400))

        rsrc = self.create_servicechain_node()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: resources.servicechain_node: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_servicechain_node()
        gbpclient.Client.update_servicechain_node(
            '5678', {'servicechain_node': {'name': 'node_update'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template._properties['name'] = 'node_update'
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class ServiceChainSpecTest(HeatTestCase):

    def setUp(self):
        super(ServiceChainSpecTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_servicechain_spec')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_servicechain_spec')
        self.m.StubOutWithMock(gbpclient.Client, 'show_servicechain_spec')
        self.m.StubOutWithMock(gbpclient.Client, 'update_servicechain_spec')
        self.stub_keystoneclient()

    def create_servicechain_spec(self):
        gbpclient.Client.create_servicechain_spec({
            "servicechain_spec": {
                "name": "test-sc-spec",
                "description": "test service chain spec resource",
                "shared": True,
                "nodes": ["1234", "7890"]
            }
        }).AndReturn({'servicechain_spec': {'id': '5678'}})

        snippet = template_format.parse(servicechain_spec_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return servicechain.ServiceChainSpec(
            'servicechain_spec', resource_defns['servicechain_spec'],
            self.stack)

    def test_create(self):
        rsrc = self.create_servicechain_spec()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_servicechain_spec({
            'servicechain_spec': {
                "name": "test-sc-spec",
                "description": "test service chain spec resource",
                "shared": True,
                "nodes": ["1234", "7890"]
            }
        }).AndRaise(servicechain.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(servicechain_spec_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = servicechain.ServiceChainSpec(
            'servicechain_spec', resource_defns['servicechain_spec'],
            self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: resources.servicechain_spec: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_servicechain_spec('5678')
        gbpclient.Client.show_servicechain_spec('5678').AndRaise(
            servicechain.NeutronClientException(status_code=404))

        rsrc = self.create_servicechain_spec()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_servicechain_spec('5678').AndRaise(
            servicechain.NeutronClientException(status_code=404))

        rsrc = self.create_servicechain_spec()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_servicechain_spec('5678').AndRaise(
            servicechain.NeutronClientException(status_code=400))

        rsrc = self.create_servicechain_spec()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: resources.servicechain_spec: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_servicechain_spec()
        gbpclient.Client.update_servicechain_spec(
            '5678', {'servicechain_spec': {'name': 'spec_update'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template._properties['name'] = 'spec_update'
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()


class ServiceProfileTest(HeatTestCase):

    def setUp(self):
        super(ServiceProfileTest, self).setUp()
        self.m.StubOutWithMock(gbpclient.Client, 'create_service_profile')
        self.m.StubOutWithMock(gbpclient.Client, 'delete_service_profile')
        self.m.StubOutWithMock(gbpclient.Client, 'show_service_profile')
        self.m.StubOutWithMock(gbpclient.Client, 'update_service_profile')
        self.stub_keystoneclient()

    def create_service_profile(self):
        gbpclient.Client.create_service_profile({
            'service_profile': {
                "name": "test-svc-profile",
                "description": "test service profile resource",
                "vendor": "test vendor",
                "service_type": "test type",
                "insertion_mode": "l2",
                "service_flavor": "test flavor",
                "shared": True
            }
        }).AndReturn({'service_profile': {'id': '5678'}})

        snippet = template_format.parse(service_profile_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        return servicechain.ServiceProfile(
            'service_profile', resource_defns['service_profile'], self.stack)

    def test_create(self):
        rsrc = self.create_service_profile()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        self.assertEqual((rsrc.CREATE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_create_failed(self):
        gbpclient.Client.create_service_profile({
            'service_profile': {
                "name": "test-svc-profile",
                "description": "test service profile resource",
                "vendor": "test vendor",
                "service_type": "test type",
                "insertion_mode": "l2",
                "service_flavor": "test flavor",
                "shared": True
            }
        }).AndRaise(servicechain.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(service_profile_template)
        self.stack = utils.parse_stack(snippet)
        resource_defns = self.stack.t.resource_definitions(self.stack)
        rsrc = servicechain.ServiceProfile(
            'service_profile', resource_defns['service_profile'],
            self.stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: resources.service_profile: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.CREATE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_delete(self):
        gbpclient.Client.delete_service_profile('5678')
        gbpclient.Client.show_service_profile('5678').AndRaise(
            servicechain.NeutronClientException(status_code=404))

        rsrc = self.create_service_profile()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_already_gone(self):
        gbpclient.Client.delete_service_profile('5678').AndRaise(
            servicechain.NeutronClientException(status_code=404))

        rsrc = self.create_service_profile()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        scheduler.TaskRunner(rsrc.delete)()
        self.assertEqual((rsrc.DELETE, rsrc.COMPLETE), rsrc.state)
        self.m.VerifyAll()

    def test_delete_failed(self):
        gbpclient.Client.delete_service_profile('5678').AndRaise(
            servicechain.NeutronClientException(status_code=400))

        rsrc = self.create_service_profile()
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()
        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.delete))
        self.assertEqual(
            'NeutronClientException: resources.service_profile: '
            'An unknown exception occurred.',
            six.text_type(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_service_profile()
        gbpclient.Client.update_service_profile(
            '5678', {'service_profile': {'name': 'profile_update'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template._properties['name'] = 'profile_update'
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()
