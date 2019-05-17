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
from pay_api.services.paybc_service import PaybcService
from .payment import Payment
from .fee_schedule import FeeSchedule


class PaymentSystemFactory:
    """Factory to manage the creation of payment system object."""

    @staticmethod
    def create(payment_method:str=None, corp_type:str=None):
        """Create a subclass of PaymentSystemService based on input params."""
        current_app.logger.debug('<create')
        _instance = None
        if not payment_method and not corp_type:
            raise BusinessException(Error.PAY003)
        if payment_method == 'CC' and corp_type == 'CP':
            _instance = PaybcService()
        else:
            raise BusinessException(Error.PAY003)

        return _instance
