# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Service to manage Payment."""

from datetime import date

from flask import current_app

from pay_api.exceptions import BusinessException
from pay_api.models import FeeSchedule as FeeScheduleModel
from pay_api.utils.errors import Error
from typing import Any, Dict, Tuple

from pay_api.services.base_payment_system import PaymentSystemService
from pay_api.services.oauth_service import OAuthService
import base64
import datetime
from typing import Any, Dict

from flask import current_app

from pay_api.utils.enums import AuthHeaderType, ContentType

from .oauth_service import OAuthService


class PaybcService(PaymentSystemService, OAuthService):
    """Service to manage Payment related operations."""

    def create_account(self, name: str, account_request: Dict[str, Any]):
        access_token = self.__get_token().json().get('access_token')
        party = self.__create_party(access_token, name)
        account = self.__create_paybc_account(access_token, party)
        site = self.__create_site(access_token, party, account, account_request)
        return party.get('party_number'), account.get('account_number'), site.get('site_number')

    def is_valid_account(self, party_number: str = None, account_number: str = None, site_number: str = None):
        current_app.logger.debug('<is_valid_account')
        is_valid: bool = False
        if party_number and account_number and site_number:
            site_url = current_app.config.get('PAYBC_BASE_URL') + '/cfs/parties/{}/accs/{}/sites/' \
                .format(party_number, account_number, site_number)
            access_token = self.__get_token().json().get('access_token')
            site_response = self.get(site_url, access_token, AuthHeaderType.BEARER, ContentType.JSON).json()
            is_valid = site_response.get('party_number') == party_number and site_response.get(
                'account_number') == account_number and site_response.get('site_number') == site_number
        current_app.logger.debug('>is_valid_account')
        return is_valid

    def create_invoice(self, account_details: Tuple[str], line_items: [Dict[str, Any]], invoice_number: int):
        current_app.logger.debug('<create_invoice')
        now = datetime.datetime.now()
        curr_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        invoice_url = current_app.config.get('PAYBC_BASE_URL') + '/cfs/parties/{}/accs/{}/sites/{}/invs/' \
            .format(account_details[0], account_details[1], account_details[2])

        invoice = dict(
            batch_source='BC REG MANUAL_OTHER',
            cust_trx_type='BC_REG_CO_OP',
            transaction_date=curr_time,
            transaction_number=invoice_number,
            gl_date=curr_time,
            term_name='IMMEDIATE',
            comments='',
            lines=[]
        )

        for index, line_item in line_items:
            invoice['lines'].append(
                {
                    'line_number': index,
                    'line_type': 'LINE',
                    'memo_line_name': 'Test Memo Line',
                    'description': line_item.get('description', None),
                    'unit_price': line_item.get('total', None),
                    'quantity': 1
                }
            )

        access_token = self.__get_token().json().get('access_token')
        invoice_response = self.post(invoice_url, access_token, AuthHeaderType.BEARER, ContentType.JSON, invoice)

        current_app.logger.debug('>create_invoice')
        return invoice_response.json()

    def update_invoice(self):
        return None

    def get_receipt(self):
        return None

    def __create_party(self, access_token: str = None, party_name: str = None):
        """Create a party record in PayBC."""
        current_app.logger.debug('<Creating party Record')
        party_url = current_app.config.get('PAYBC_BASE_URL') + '/cfs/parties/'
        party: Dict[str, Any] = {
            'customer_name': party_name
        }

        party_response = self.post(party_url, access_token, AuthHeaderType.BEARER, ContentType.JSON, party)
        current_app.logger.debug('>Creating party Record')
        return party_response.json()

    def __create_paybc_account(self, access_token, party):
        """Create account record in PayBC."""
        current_app.logger.debug('<Creating account')
        account_url = current_app.config.get('PAYBC_BASE_URL') + '/cfs/parties/{}/accs/' \
            .format(party.get('party_number'), None)
        account: Dict[str, Any] = {
            'party_number': party.get('party_number'),
            'account_description': party.get('customer_name')
        }

        account_response = self.post(account_url, access_token, AuthHeaderType.BEARER, ContentType.JSON, account)
        current_app.logger.debug('>Creating account')
        return account_response.json()

    def __create_site(self, access_token, party, account, account_request):
        """Create site in PayBC."""
        current_app.logger.debug('<Creating site ')
        site_url = current_app.config.get('PAYBC_BASE_URL') + '/cfs/parties/{}/accs/{}/sites/' \
            .format(account.get('party_number', None), account.get('account_number', None))
        site: Dict[str, Any] = {
            'party_number': account.get('party_number', None),
            'account_number': account.get('account_number', None),
            'site_name': party.get('customer_name') + ' Site',
            'city': account_request.get('city', None),
            'address_line_1': account_request.get('address_line_1', None),
            'postal_code': account_request.get('postal_code', None),
            'province': account_request.get('province', None),
            'country': account_request.get('country', 'CA'),
            'customer_site_id': '1'
        }

        site_response = self.post(site_url, access_token, AuthHeaderType.BEARER, ContentType.JSON, site)

        current_app.logger.debug('>Creating site ')
        return site_response.json()

    def __get_token(self):
        """Generate oauth token from payBC which will be used for all communication."""
        current_app.logger.debug('<Getting token')
        token_url = current_app.config.get('PAYBC_BASE_URL') + '/oauth/token'
        basic_auth_encoded = base64.b64encode(
            bytes(current_app.config.get('PAYBC_CLIENT_ID') + ':' + current_app.config.get('PAYBC_CLIENT_SECRET'),
                  'utf-8')).decode('utf-8')
        data = 'grant_type=client_credentials'
        token_response = self.post(token_url, basic_auth_encoded, AuthHeaderType.BASIC, ContentType.FORM_URL_ENCODED,
                                   data)
        current_app.logger.debug('>Getting token')
        return token_response
