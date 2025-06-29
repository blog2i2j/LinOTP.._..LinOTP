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


"""
Testing the set password ability
"""

import logging

from sqlalchemy.exc import ProgrammingError

from linotp.lib.crypto import utils
from linotp.lib.tools.set_password import SetPasswordHandler
from linotp.model import db
from linotp.tests import TestController

log = logging.getLogger(__name__)


class TestSetAdminPassword(TestController):
    def drop_admin_user(self):
        """
        for the tests, we will drop the imported user table
        """

        # we try to delete the table if it exists

        try:
            SetPasswordHandler.AdminUser.__table__.drop(db.engine)
            db.session.commit()
        except (ProgrammingError, Exception) as exx:
            log.info("Drop Table failed %r", exx)
            db.session.rollback()

    def create_admin_user(self):
        """
        for testing we require the admin user to exist
        """

        db_context = None  # not required

        SetPasswordHandler.create_table(db_context)
        SetPasswordHandler.create_admin_user(
            db_context,
            username="admin",
            crypted_password=utils.crypt_password("nimda"),
        )

    def test_set_simple_password(self):
        """
        simple functional test
        - other aspects are covered by the unit test
        """

        self.drop_admin_user()
        self.create_admin_user()

        params = {}
        params["old_password"] = "nimda"
        params["new_password"] = "admin"

        response = self.make_tools_request(
            "setPassword", params=params, auth_user="admin"
        )

        msg = '"detail": "password updated for \'admin\'"'
        assert msg in response


# eof ########################################################################
