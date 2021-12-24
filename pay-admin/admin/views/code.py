"""Copyright 2021 Province of British Columbia.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from .secured_view import SecuredView


class CodeConfig(SecuredView):
    """Code config for all generic code tables."""

    column_list = form_columns = column_searchable_list = ('code', 'description')

    # Keep everything sorted, although realistically also we need to sort the values within a row before it is saved.
    column_default_sort = 'code'

    def on_form_prefill(self, form, id):  # pylint:disable=redefined-builtin
        """Set code as readonly."""
        form.code.render_kw = {'readonly': True}
