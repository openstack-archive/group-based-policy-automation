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

from gbpautomation.heat.engine.resources.neutron import servicechain
from gbpclient.v2_0 import client as gbpclient
from heat.common import exception
from heat.common import template_format
from heat.tests.common import HeatTestCase

from heat.engine import scheduler
from heat.tests import utils


servicechain_node_template = '''
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test neutron service chain node",
  "Parameters" : {},
  "Resources" : {
    "servicechain_node": {
      "Type": "OS::Neutron::ServiceChainNode",
      "Properties": {
        "name": "test-sc-node",
        "description": "test service chain node resource",
        "service_type": "TAP",
        "config": "{'name': 'sc_node_config'}"
      }
    }
  }
}
'''

servicechain_spec_template = '''
{
  "AWSTemplateFormatVersion" : "2010-09-09",
  "Description" : "Template to test neutron service chain spec",
  "Parameters" : {},
  "Resources" : {
    "servicechain_spec": {
      "Type": "OS::Neutron::ServiceChainSpec",
      "Properties": {
        "name": "test-sc-spec",
        "description": "test service chain spec resource",
        "nodes": ["1234", "7890"]
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
                "service_type": "TAP",
                "config": "{'name': 'sc_node_config'}"
            }
        }).AndReturn({'servicechain_node': {'id': '5678'}})

        snippet = template_format.parse(servicechain_node_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        return servicechain.ServiceChainNode(
            'servicechain_node', resource_defns['servicechain_node'], stack)

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
                "service_type": "TAP",
                "config": "{'name': 'sc_node_config'}"
            }
        }).AndRaise(servicechain.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(servicechain_node_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        rsrc = servicechain.ServiceChainNode(
            'servicechain_node', resource_defns['servicechain_node'], stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
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
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_servicechain_node()
        gbpclient.Client.update_servicechain_node(
            '5678', {'servicechain_node': {'name': 'node_update'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['name'] = 'node_update'
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
                "nodes": ["1234", "7890"]
            }
        }).AndReturn({'servicechain_spec': {'id': '5678'}})

        snippet = template_format.parse(servicechain_spec_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        return servicechain.ServiceChainSpec(
            'servicechain_spec', resource_defns['servicechain_spec'], stack)

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
                "nodes": ["1234", "7890"]
            }
        }).AndRaise(servicechain.NeutronClientException())
        self.m.ReplayAll()

        snippet = template_format.parse(servicechain_spec_template)
        stack = utils.parse_stack(snippet)
        resource_defns = stack.t.resource_definitions(stack)
        rsrc = servicechain.ServiceChainSpec(
            'servicechain_spec', resource_defns['servicechain_spec'], stack)

        error = self.assertRaises(exception.ResourceFailure,
                                  scheduler.TaskRunner(rsrc.create))
        self.assertEqual(
            'NeutronClientException: An unknown exception occurred.',
            str(error))
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
            'NeutronClientException: An unknown exception occurred.',
            str(error))
        self.assertEqual((rsrc.DELETE, rsrc.FAILED), rsrc.state)
        self.m.VerifyAll()

    def test_update(self):
        rsrc = self.create_servicechain_spec()
        gbpclient.Client.update_servicechain_spec(
            '5678', {'servicechain_spec': {'name': 'spec_update'}})
        self.m.ReplayAll()
        scheduler.TaskRunner(rsrc.create)()

        update_template = copy.deepcopy(rsrc.t)
        update_template['Properties']['name'] = 'spec_update'
        scheduler.TaskRunner(rsrc.update, update_template)()

        self.m.VerifyAll()
