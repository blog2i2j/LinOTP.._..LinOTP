# -*- coding: utf-8 -*-
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
"""module for SecurityModules / devices like hsms"""

import logging

log = logging.getLogger(__name__)


class FatalHSMException(Exception):
    pass


class SecurityModule(object):
    @classmethod
    def getAdditionalClassConfig(cls):
        return []

    def __init__(self, config=None, add_conf=None):
        self.name = "SecurityModule"

    def isReady(self):
        fname = "isReady"
        raise NotImplementedError("Should have been implemented %s" % fname)

    def setup_module(self, params):
        fname = "setup_module"
        raise NotImplementedError("Should have been implemented %s" % fname)

    ### base methods ###

    def random(self, len: int) -> bytes:
        fname = "random"
        raise NotImplementedError("Should have been implemented %s" % fname)

    def encrypt(self, data: bytes, iv: bytes, id: int = 0) -> bytes:
        fname = "encrypt"
        raise NotImplementedError("Should have been implemented %s" % fname)

    def decrypt(self, value: bytes, iv: bytes, id: int = 0) -> bytes:
        fname = "decrypt"
        raise NotImplementedError("Should have been implemented %s" % fname)

    ### higer level methods ###

    def encryptPassword(self, cryptPass: bytes) -> str:
        fname = "decrypt"
        raise NotImplementedError("Should have been implemented %s" % fname)

    def encryptPin(self, cryptPin, iv=None) -> str:
        fname = "decrypt"
        raise NotImplementedError("Should have been implemented %s" % fname)

    def decryptPassword(self, cryptPass: str) -> bytes:
        fname = "decrypt"
        raise NotImplementedError("Should have been implemented %s" % fname)

    def decryptPin(self, cryptPin: str) -> bytes:
        fname = "decrypt"
        raise NotImplementedError("Should have been implemented %s" % fname)

    def signMessage(self, message, method=None, slot_id=3):
        fname = "signMessage"
        raise NotImplementedError("Should have been implemented %s" % fname)

    def verfiyMessageSignature(self, message, hex_mac, method=None, slot_id=3):
        fname = "verfiyMessageSignature"
        raise NotImplementedError("Should have been implemented %s" % fname)
