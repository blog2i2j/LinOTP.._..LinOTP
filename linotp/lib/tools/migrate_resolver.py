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
migration handler -
  migration of assigned tokens to a different resolver
"""

import logging
from datetime import datetime

from flask import g
from flask_babel import gettext as _
from sqlalchemy import and_

from linotp.lib.resolver import getResolverClassName, getResolverObject
from linotp.lib.tools import ToolsHandler
from linotp.lib.user import getUserInfo
from linotp.model import Token, db

log = logging.getLogger(__name__)


class MigrateResolverHandler(ToolsHandler):
    def migrate_resolver(self, src=None, target=None, filter_serials=None):
        """
        support the migration of owned tokens from one resolver to a new one

        the idea is:
        - get all tokens from one resolver
        - for each token, the the owner
        - from the owner get the login name
        - with the login name get the uid from the target resolver
        - update the new_id in the token

        """

        ret = {}

        if not src or not target:
            msg = "Missing src or target resolver defintion!"
            raise Exception(msg)

        now = datetime.now()
        stime = now.strftime("%s")

        g.audit["action_detail"] = "migration from {} to {}".format(
            src["resolvername"],
            target["resolvername"],
        )

        ret["src"] = src
        ret["target"] = target
        ret["value"] = False
        ret["message"] = ""

        search = getResolverClassName(src["type"], src["resolvername"])
        target_resolver = getResolverClassName(target["type"], target["resolvername"])

        # get all tokens of src resolver
        tokens = self._get_tokens_for_resolver(search, serials=filter_serials)

        num_migration = 0
        serials = set()
        for token in tokens:
            serial = token.get("LinOtpTokenSerialnumber")
            userid = token.get("LinOtpUserid")
            resolverC = token.get("LinOtpIdResClass")
            # now do the lookup of the uid in the
            # src resolver to get the login
            uInfo = getUserInfo(userid, "", resolverC)

            login = uInfo.get("username")
            try:
                y = getResolverObject(target_resolver)
                uid = y.getUserId(login)
                if not uid:
                    log.warning(
                        "User %s not found in target resolver %r",
                        login,
                        target_resolver,
                    )
                    continue

                token.LinOtpIdResClass = target_resolver
                token.LinOtpUserid = uid
                # TODO: adjust
                token.LinOtpIdResolver = target["type"]
                db.session.add(token)

                num_migration += 1
                serials.add(serial)

            except Exception as exx:
                log.error(
                    "Faild to set new resolver data for token %s: %r",
                    serial,
                    exx,
                )

        ret["value"] = True
        ret["message"] = _("%d tokens of %d migrated") % (
            num_migration,
            len(tokens),
        )
        g.audit["info"] = "[{}] {}".format(stime, ret["message"])
        g.audit["serial"] = ",".join(list(serials))
        g.audit["success"] = True

        return ret

    def _get_tokens_for_resolver(self, resolverClass, serials=None):
        """
        get the tokens of the src resolver

        :param resolverClass: the resolver class defintions as in the tokendb
        :param serials: the set of serials, which should be worked out
                        - if None, all tokens of the resolvers are searched
        """

        rcondition = and_(Token.LinOtpIdResClass.like(resolverClass))
        scondition = None
        if serials:
            # filter token serials
            serials = ",".join(serials.split(","))
            scondition = and_(Token.LinOtpTokenSerialnumber.in_(serials))

        #  create the final condition as AND of all conditions
        condTuple = ()
        for conn in (scondition, rcondition):
            if type(conn).__name__ != "NoneType":
                condTuple += (conn,)

        tokens = Token.query.filter(*condTuple).all()

        return tokens
