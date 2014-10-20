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

from gbpclient.v2_0 import client as gbpc
from neutronclient.common import exceptions

from heat.engine.clients import client_plugin


class GBPClientPlugin(client_plugin.ClientPlugin):

    exceptions_module = exceptions

    def _create(self):

        con = self.context

        endpoint_type = self._get_client_option('grouppolicy', 'endpoint_type')
        endpoint = self.url_for(service_type='network',
                                endpoint_type=endpoint_type)

        args = {
            'auth_url': con.auth_url,
            'service_type': 'network',
            'token': self.auth_token,
            'endpoint_url': endpoint,
            'endpoint_type': endpoint_type,
            'ca_cert': self._get_client_option('grouppolicy', 'ca_file'),
            'insecure': self._get_client_option('grouppolicy', 'insecure')
        }

        return gbpc.Client(**args)

    def is_not_found(self, ex):
        if isinstance(ex, (exceptions.NotFound,
                           exceptions.NetworkNotFoundClient,
                           exceptions.PortNotFoundClient)):
            return True
        return (isinstance(ex, exceptions.NeutronClientException) and
                ex.status_code == 404)

    def is_conflict(self, ex):
        if not isinstance(ex, exceptions.NeutronClientException):
            return False
        return ex.status_code == 409

    def is_over_limit(self, ex):
        if not isinstance(ex, exceptions.NeutronClientException):
            return False
        return ex.status_code == 413
