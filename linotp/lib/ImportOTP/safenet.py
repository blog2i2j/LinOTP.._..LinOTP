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
parses XML data of a Aladdin/SafeNet XML
"""

import logging
import xml.etree.ElementTree as etree

from linotp.lib.ImportOTP import ImportException, getTagName

log = logging.getLogger(__name__)


def parseSafeNetXML(xml):
    """
    This function parses XML data of a Aladdin/SafeNet XML
    file for eToken PASS

    It returns a dictionary of
        serial : { hmac_key , counter, type }
    """

    TOKENS = {}
    elem_tokencontainer = etree.fromstring(xml)

    if getTagName(elem_tokencontainer) != "Tokens":
        msg = "No toplevel element Tokens"
        raise ImportException(msg)

    for elem_token in list(elem_tokencontainer):
        SERIAL = None
        COUNTER = None
        HMAC = None
        DESCRIPTION = None
        if getTagName(elem_token) == "Token":
            SERIAL = elem_token.get("serial")
            log.debug("Found token with serial %r", SERIAL)
            for elem_tdata in list(elem_token):
                tag = getTagName(elem_tdata)
                if tag == "ProductName":
                    DESCRIPTION = elem_tdata.text
                    log.debug(
                        "The Token with the serial %s has the productname %s",
                        SERIAL,
                        DESCRIPTION,
                    )
                if tag == "Applications":
                    for elem_apps in elem_tdata:
                        if getTagName(elem_apps) == "Application":
                            for elem_app in elem_apps:
                                tag = getTagName(elem_app)
                                if tag == "Seed":
                                    HMAC = elem_app.text
                                if tag == "MovingFactor":
                                    COUNTER = elem_app.text
            if not SERIAL:
                log.error("Found token without a serial")
            elif HMAC:
                hashlib = "sha1"
                if len(HMAC) == 64:
                    hashlib = "sha256"

                TOKENS[SERIAL] = {
                    "hmac_key": HMAC,
                    "counter": COUNTER,
                    "type": "HMAC",
                    "hashlib": hashlib,
                }
            else:
                log.error("Found token %s without a element 'Seed'", SERIAL)

    return TOKENS
