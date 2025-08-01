#
#    LinOTP - the open source solution for two factor authentication
#    Copyright (C) 2010-2019 KeyIdentity GmbH
#    Copyright (C) 2019-     netgo software GmbH
#
#    This file is part of LinOTP server.
#
#    This program is free software: you can redistribute it and/or
#    modify it under the terms of the GNU Affero General Public
#    License, version 3, as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the
#               GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#    E-mail: info@linotp.de
#    Contact: www.linotp.org
#    Support: www.linotp.de
#
"""LinOTP Selenium Test that creates UserIdResolvers in the WebUI"""

import integration_data as data
import pytest


class TestCreateRealmDialog:
    """TestCase class that checks basic realm functionality"""

    @pytest.fixture(autouse=True)
    def setUp(self, testcase):
        """
        Takes the test case and sets this class up with the required objects/functions
        """
        self.testcase = testcase

    def test_realm_open(self):
        r = self.testcase.manage_ui.realm_manager
        r.open()

    def test_clear_realms(self):
        r = self.testcase.manage_ui.realm_manager
        r.clear_realms_via_api()

        m = self.testcase.manage_ui.useridresolver_manager
        m.clear_resolvers_via_api()

        resolver_data = data.musicians_ldap_resolver
        m.create_resolver_via_api(resolver_data)

        r.create("test_clear_realm", resolver_data["name"])

        realms = r.get_realms_list()
        assert len(realms) == 2, "Expected 2 realms incl. the admin realm"

        r.clear_realms()

        realms = r.get_realms_list()
        assert len(realms) == 1, "Realm count should be 1 (admin realm)"
