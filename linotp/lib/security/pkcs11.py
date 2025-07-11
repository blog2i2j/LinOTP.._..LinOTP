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
"""This Security module (hsm) is used to access hardware security modules
via PKCS11 for encrypting and decrypting the data

linotp.ini:
linotpActiveSecurityModule = lunasa
linotpSecurity.lunasa.module = linotp.lib.security.pkcs11.Pkcs11SecurityModule
linotpSecurity.lunasa.library = libCryptoki2_64.so
linotpSecurity.lunasa.tokenHandle =21
linotpSecurity.lunasa.valueHandle =22
linotpSecurity.lunasa.configHandle =23
linotpSecurity.lunasa.defaultHandle =22
linotpSecurity.lunasa.configLabel = config
linotpSecurity.lunasa.tokenLabel = token
linotpSecurity.lunasa.valueLabel = value
linotpSecurity.lunasa.password = 6SNq-L9WL-SSW4-NGNL
linotpSecurity.lunasa.slotid = 1
linotpActiveSecurityModule = lunasa

"""

import binascii
import ctypes
import getpass
import logging
import sys
from getopt import GetoptError, getopt

from linotp.lib.security.default import DefaultSecurityModule
from linotp.lib.security.provider import (
    CONFIG_KEY,
    DEFAULT_KEY,
    TOKEN_KEY,
    VALUE_KEY,
)

log = logging.getLogger(__name__)

CKK_AES = 0x0000001F
CKA_CLASS = 0x00000000
CKO_DATA = 0x00000000
CKO_SECRET_KEY = 0x00000004
CKA_KEY_TYPE = 0x00000100
CKA_TOKEN = 0x00000001
CKA_LABEL = 0x00000003
CKA_ENCRYPT = 0x00000104
CKA_DECRYPT = 0x00000105
CKA_VALUE = 0x00000011
CKA_PRIVATE = 0x00000002

CKA_SENSITIVE = 0x00000103
CKA_VALUE_LEN = 0x00000161
CK_BBOOL = ctypes.c_byte
CKK_AES = 0x0000001F
CK_OBJECT_HANDLE = ctypes.c_ulong
CK_BYTE = ctypes.c_char
CK_ULONG = ctypes.c_ulong
CK_SLOT_ID = CK_ULONG
# AES

CKM_AES_KEY_GEN = 0x00001080
CKM_AES_ECB = 0x00001081
CKM_AES_CBC = 0x00001082
CKM_AES_MAC = 0x00001083
CKM_AES_MAC_GENERAL = 0x00001084
CKM_AES_CBC_PAD = 0x00001085
CKU_USER = 1
CKU_SO = 0

NULL = None

running_as_main = False


class CK_VERSION(ctypes.Structure):
    _fields_ = [
        ("major", ctypes.c_byte),
        ("minor", ctypes.c_byte),
    ]


class CK_TOKEN_INFO(ctypes.Structure):
    _fields_ = [
        ("label", ctypes.c_wchar * 32),  # 0:31   Zeichen = 2byte
        ("manufacturerID", ctypes.c_wchar * 32),  # 32:63
        ("model", ctypes.c_wchar * 16),  # 64:79
        ("serialNumber", ctypes.c_char * 16),  # 80:95
        ("flags", ctypes.c_ulong),  # 96:97     4 byte
        ("ulMaxSessionCount", ctypes.c_ulong),  # 98:99
        ("ulSessionCount", ctypes.c_ulong),  # 100:101
        ("ulMaxRwSessionCount", ctypes.c_ulong),  # 102:103
        ("ulRwSessionCount", ctypes.c_ulong),  # 104:105
        ("ulMaxPinLen", ctypes.c_ulong),  # 106:107
        ("ulMinPinLen", ctypes.c_ulong),  # 108:109
        ("ulTotalPublicMemory", ctypes.c_ulong),  # 110:111
        ("ulFreePublicMemory", ctypes.c_ulong),  # 112:113
        ("ulTotalPrivateMemory", ctypes.c_ulong),  # 114:115
        ("ulFreePrivateMemory", ctypes.c_ulong),  # 116:117
        ("hardwareVersion", CK_VERSION),  # 118
        ("firmwareVersion", CK_VERSION),  # 119
        ("utcTime", ctypes.c_char * 16),  # 120:135
    ]


class CK_ATTRIBUTE(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("pValue", ctypes.c_void_p),
        ("ulValueLen", ctypes.c_ulong),
    ]


class CK_MECHANISM(ctypes.Structure):
    _fields_ = [
        ("mechanism", ctypes.c_ulong),
        ("pParameter", ctypes.c_void_p),
        ("usParameterLen", ctypes.c_ulong),
    ]


errormap = {
    182: "Session exists",
    7: "Bad argument",
    19: "Attribute value invalid",
    162: "CKR_PIN_LEN_RANGE",
    112: "Mechanism invalid",
    224: "Token not present",
    209: "Template inconsistent",
    208: "TEMPLATE_INCOMPLETE",
    163: "PIN expired",
    160: "CKR_PIN_INCORRECT",
    0x00000020: "Data invalid",
    0x00000071: "mechanism param invalid",
    0x00000150: "CKR_BUFFER_TOO_SMALL",
    0x00000160: "CKR_SAVED_STATE_INVALID",
    0x00000021: "CKR_DATA_LEN_RANGE",
    0x000000B3: "CKR_SESSION_HANDLE_INVALID",
    0x00000082: "CKR_OBJECT_HANDLE_INVALID",
    0x00000090: "CKR_OPERATION_ACTIVE",
    0x00000091: "CKR_OPERATION_NOT_INITIALIZED",
    0x000000A1: "CKR_PIN_INVALID",
}


def pkcs11error(rv):
    return errormap.get(rv, rv)


def output(loglevel, text):
    if running_as_main:
        print(f"{loglevel.upper()}: {text}")
    elif loglevel == "debug":
        log.debug(text)
    elif loglevel == "info":
        log.info(text)
    elif loglevel == "error":
        log.error(text)


class Pkcs11SecurityModule(DefaultSecurityModule):
    """
    Class that handles all AES stuff
    """

    number_or_null = {"anyOf": [{"type": "number"}, {"type": "null"}]}

    # Add schema for validating configuration in settings.py
    schema = {
        "type": "object",
        "properties": {
            "module": {"type": "string"},
            "library": {"type": "string"},
            "password": {"type": "string"},
            "slotid": {"type": "number"},
            "configLabel": {"type": "string"},
            "tokenLabel": {"type": "string"},
            "valueLabel": {"type": "string"},
            "defaultLabel": {"type": "string"},
            "configHandle": number_or_null,
            "tokenHandle": number_or_null,
            "valueHandle": number_or_null,
            "defaultHandle": number_or_null,
            "poolsize": {"type": "number"},
        },
        "required": [
            "module",
            "library",
            "password",
            "slotid",
            "defaultLabel",
        ],
    }

    def __init__(self, config=None, add_conf=None):
        output("debug", "[__init__] Initializing the Pkcs11 Security Module")
        self.hSession = None
        self.is_ready = False
        self.name = "Pkcs11"
        if not config:
            config = {}

        self.password = config.get("password", "")
        self.connectedTokens = []
        library = config.get("library")
        self.slotid = int(config.get("slotid", 0))

        # Accept invalid padding?
        config_entry = config.get("pkcs11.accept_invalid_padding", "False")
        self.accept_invalid_padding = False
        if config_entry and config_entry.lower() == "true":
            self.accept_invalid_padding = True

        # ------------------------------------------------------------------ --

        # load handles and labels

        self.handles = {
            CONFIG_KEY: config.get("configHandle"),
            TOKEN_KEY: config.get("tokenHandle"),
            VALUE_KEY: config.get("valueHandle"),
            DEFAULT_KEY: config.get("defaultHandle"),
        }

        # adjust handle type to int

        for key, value in self.handles.items():
            if value is not None:
                self.handles[key] = int(value)

        self.labels = {
            CONFIG_KEY: config.get("configLabel"),
            TOKEN_KEY: config.get("tokenLabel"),
            VALUE_KEY: config.get("valueLabel"),
            DEFAULT_KEY: config.get("defaultLabel"),
        }

        # adjust label type to bytes

        for key, value in self.labels.items():
            if value is not None and isinstance(value, str):
                self.labels[key] = value.encode("utf-8")

        # ------------------------------------------------------------------ --

        if not library:
            msg = "No .library specified"
            raise Exception(msg)
        self.pkcs11 = ctypes.CDLL(library)

        self.initpkcs11()
        if self.password:
            output("debug", f"[setup_module] logging in to slot {self.slotid!r}")
            self.login(slotid=self.slotid)

    def populate_handles(self):
        """
        In a HA Group of LunaSAs the handle do not exist.
        They first need to be populated

        The Label overwrites the handles!
        """
        for key in [CONFIG_KEY, TOKEN_KEY, VALUE_KEY, DEFAULT_KEY]:
            label = self.labels.get(key)
            if label:
                output(
                    "debug",
                    f"[populate_handles] get handle for label {label}",
                )

                self.handles[key] = self.find_aes_keys(label)

                output(
                    "debug",
                    f"[populate_handles] handle set to {self.handles.get(key)}",
                )

    def isReady(self):
        return self.is_ready

    def setup_module(self, params):
        """
        used to set the password, if the password is not contained
        in the config file
        """

        if "password" not in params:
            output("error", "[setup_module] missing password!")
            msg = "missing password"
            raise Exception(msg)

        slotid = params.get("slotid", None)
        if slotid is None:
            slotid = self.slotid

        slotid = int(slotid)

        # finally initialise the login

        self.login(params.get("password"), slotid=slotid)

    def pad(self, unpadded_str, block=16):
        """
        PKCS7 padding pads the missing bytes with the value of the number
        of the bytes. If 4 bytes are missing, this missing bytes are filled
        with \x04

        :param unpadded_str: The byte string to pad
        :type unpadded_str: bytes

        :param block: Block size
        :type block: int

        :returns: padded byte string
        :rtype: bytes
        """
        l_s = len(unpadded_str)
        missing_num = block - l_s % block
        missing_byte = chr(missing_num)
        padding = missing_byte * missing_num
        return unpadded_str + padding.encode("utf-8")

    def unpad(self, padded_byte_str: bytes, block_size: int = 16) -> bytes:
        """
        PKCS7 padding pads the missing bytes with the value of the number
        of the bytes. If 4 bytes are missing, this missing bytes are filled
        with \x04

        unpad removes and checks the PKCS #7 padding by verifying that the
        padding byte string only contains the pad chars

        :param padded_byte_str: The binary string to unpad

        :param block_size: Block size

        :raises ValueError: If padded_byte_str is not correctly padded a
            ValueError can be raised.
            This depends on the 'pkcs11.accept_invalid_padding' LinOTP config
            option. If set to False (default) ValueError is raised.  The reason
            why the data is sometimes incorrectly padded is because the pad()
            method delivered with LinOTP version < 2.7.1 didn't pad correctly
            when the data-length was a multiple of the block-length.
            Beware that in some cases (statistically about 0.4% of data-chunks
            whose length is a multiple of the block length) the incorrect
            padding can not be detected and incomplete data is returned.  One
            example for this last case is when the data ends with the byte
            0x01. This is recognized as legitimate padding and is removed
            before returning the data, thus removing a legitimate byte from the
            data and making it unusable.
            If you didn't upgrade from a LinOTP version before 2.7.1 (or don't
            use a PKCS#11 HSM) you will not be affected by this in any way.
            ValueError will of course also be raised if you data became corrupt
            for some other reason (e.g. disk failure) and can not be unpadded.
            In this case you should NOT set 'pkcs11.accept_invalid_padding' to
            True because your data will be unusable anyway.

        :returns: unpadded string or sometimes padded string when
            'pkcs11.accept_invalid_padding' is set to True. See above.
        :rtype: str
        """

        last_byte = padded_byte_str[-1]
        padding_length = last_byte

        # ------------------------------------------------------------------ --

        # extract both parts: the unpadded bytes and the padding bytes

        padding_byte_str = padded_byte_str[-padding_length:]
        unpadded_byte_str = padded_byte_str[:-padding_length]

        # ------------------------------------------------------------------ --

        # padding match: verify that the appended padded string contains
        #   only padded value. Therefore compose a string with only
        #   padding bytes and compare it with the truncated padding string

        byte_str_with_padding_byte = (f"{chr(last_byte)}" * padding_length).encode(
            "utf-8"
        )

        padding_match = padding_byte_str == byte_str_with_padding_byte

        # ------------------------------------------------------------------ --

        if 0 < padding_length <= block_size and padding_match:
            return unpadded_byte_str

        elif self.accept_invalid_padding:
            log.warning("[unpad] Input 'padded_str' is not properly padded")
            return padded_byte_str

        else:
            msg = "Input 'padded_str' is not properly padded"
            raise ValueError(msg)

    def initpkcs11(self):
        """
        Initialize the PKCS11 library
        """
        output(
            "debug",
            f"[initpkcs11]  Initialize the PKCS11 library {self.pkcs11}",
        )

        self.pkcs11.C_Initialize(0)
        SlotID = ctypes.c_ulong()
        nSlots = ctypes.c_ulong()
        rv = self.pkcs11.C_GetSlotList(ctypes.c_ulong(1), NULL, ctypes.byref(nSlots))
        if rv:
            # TODO: a second call of C_GetSlotList could
            # fetch the list of the slots
            output(
                "error",
                f"[initpkcs11] Failed to C_GetSlotList ({rv!s}): {pkcs11error(rv)}",
            )
            msg = f"etng::initpkcs11 - Failed to C_GetSlotList ({rv})"
            raise Exception(msg)
        else:
            output(
                "debug",
                f"[initpkcs11] number of connected tokens: {nSlots.value}. "
                f"slotid: {SlotID.value}",
            )

        if nSlots.value == 0:
            output("error", "[initpkcs11] No slots connected!")
            msg = f"initpkcs11 - No slot connected ({nSlots.value})"
            raise Exception(msg)

        if nSlots.value > 1:
            output(
                "info",
                f"[initpkcs11] More than one slot connected: {nSlots.value}",
            )

    def login(self, password=None, slotid=0):
        """
        Open a session on the first token

        After this, we got a self.hSession
        """
        output("debug", f"[login] login on slotid {slotid}")

        if password is None:
            output("debug", "[login] using password from the config file.")
            password = self.password
        if password is None:
            output(
                "info",
                "[login] No password in config file. We have to"
                " wait for it beeing set.",
            )

        prototype = ctypes.CFUNCTYPE(
            ctypes.c_int,
            CK_SLOT_ID,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ulong),
        )
        paramflags = (
            (1, "SlotID", 0),
            (1, "Flags", 6),
            (1, "App", NULL),
            (1, "Notify", NULL),
            (2, "SessionHandle"),
        )
        opensession = prototype(("C_OpenSession", self.pkcs11), paramflags)

        self.hSession = opensession(SlotID=CK_SLOT_ID(slotid))

        output("debug", f"[login] got this session: {self.hSession}")

        pw = password
        if isinstance(password, str):
            pw = password.encode("utf-8")

        rv = self.pkcs11.C_Login(self.hSession, CKU_USER, pw, len(pw))
        if rv:
            output(
                "error",
                f"[login] Failed to login to token ({rv!r}): {pkcs11error(rv)}",
            )
            msg = f"etng::logintoken - Failed to C_Login ({rv!r})"
            raise Exception(msg)
        else:
            output("debug", "[login] login successful")
            self.is_ready = True

        self.populate_handles()

    def logout(self):
        """
        closes the existing session
        """
        rv = self.pkcs11.C_CloseSession(self.hSession)
        if rv:
            output(
                "error",
                f"[logout] Failed to close session ({rv!s}): {pkcs11error(rv)}",
            )
            msg = f"[logout] Failed to C_CloseSession ({rv!s}): {pkcs11error(rv)}"
            raise Exception(msg)
        else:
            output("debug", "[logout] logout successful")

    def find_aes_keys(self, label="testAES", wanted=1):
        """
        Find and AES key with the given label

        The number of keys to be found is restricted by "wanted"
        finding aes keys is done by setting some search attributes when
        searching for objects. the search attributes which describe an aes
        key are:
           type, class, public accessible, belonging to the current token,
           usable for encryption / decryption

        :param label: the label of the aes key
        :param wanted: number of maximum returned key
        :return: if wanted == 1 return 0 or the last in list
                 else return list of aes keys
        """

        klass = ctypes.c_ulong(CKO_SECRET_KEY)
        keytype = ctypes.c_ulong(CKK_AES)
        ck_true = ctypes.c_ubyte(1)
        ck_false = ctypes.c_ubyte(0)

        search_attributes = [
            CK_ATTRIBUTE(CKA_CLASS, ctypes.addressof(klass), ctypes.sizeof(klass)),
            CK_ATTRIBUTE(
                CKA_KEY_TYPE, ctypes.addressof(keytype), ctypes.sizeof(keytype)
            ),
            CK_ATTRIBUTE(
                CKA_PRIVATE,
                ctypes.cast(ctypes.addressof(ck_false), ctypes.c_void_p),
                ctypes.sizeof(ck_false),
            ),
            CK_ATTRIBUTE(
                CKA_TOKEN,
                ctypes.cast(ctypes.addressof(ck_true), ctypes.c_void_p),
                ctypes.sizeof(ck_true),
            ),
            CK_ATTRIBUTE(
                CKA_SENSITIVE,
                ctypes.cast(ctypes.addressof(ck_true), ctypes.c_void_p),
                ctypes.sizeof(ck_true),
            ),
            CK_ATTRIBUTE(
                CKA_ENCRYPT,
                ctypes.cast(ctypes.addressof(ck_true), ctypes.c_void_p),
                ctypes.sizeof(ck_true),
            ),
            CK_ATTRIBUTE(
                CKA_DECRYPT,
                ctypes.cast(ctypes.addressof(ck_true), ctypes.c_void_p),
                ctypes.sizeof(ck_true),
            ),
        ]

        # ---------------------------------------------------------------------

        # if we have a label, we add it to the search attribute filter

        if label:
            search_attributes.append(
                CK_ATTRIBUTE(CKA_LABEL, ctypes.cast(label, ctypes.c_void_p), len(label))
            )

        # ---------------------------------------------------------------------

        # create the list of search attributes

        size = len(search_attributes)
        CK_TEMPLATE = CK_ATTRIBUTE * size

        template = CK_TEMPLATE(*search_attributes)
        template_len = ctypes.c_ulong(size)

        rv = self.pkcs11.C_FindObjectsInit(self.hSession, template, template_len)
        if rv:
            msg = f"Failed to C_FindObjectsInit ({rv}): {pkcs11error(rv)}"
            raise Exception(msg)

        keys = []
        hKey = CK_OBJECT_HANDLE()
        ulKeyCount = ctypes.c_ulong(1)

        while ulKeyCount.value > 0:
            rv = self.pkcs11.C_FindObjects(
                self.hSession, ctypes.byref(hKey), wanted, ctypes.byref(ulKeyCount)
            )
            if rv:
                output(
                    "error",
                    f"[find_aes_keys] Failed to C_FindObjects ({rv}):"
                    f" {pkcs11error(rv)}",
                )
                msg = f"Failed to C_FindObjects ({rv}): {pkcs11error(rv)}"
                raise Exception(msg)

            if ulKeyCount.value > 0:
                keys.append(int(hKey.value))

            output(
                "debug",
                f"[find_aes_keys] searching keys: {ulKeyCount.value}: {hKey.value}",
            )

        rv = self.pkcs11.C_FindObjectsFinal(self.hSession)

        if rv:
            output(
                "debug",
                f"[find_aes_keys] Failed to C_FindObjectsFinal ({rv}): {pkcs11error(rv)}",
            )
            msg = f"Failed to C_FindObjectsFinal ({rv}): {pkcs11error(rv)}"
            raise Exception(msg)

        if wanted == 1:
            if keys:
                return keys[-1]
            else:
                return 0

        return keys

    def gettokeninfo(self, slotid=0):
        """
        This returns a dictionary with the token info
        """
        output("debug", f"[gettokeninfo] for slot {slotid}")
        ti = CK_TOKEN_INFO()
        rv = self.pkcs11.C_GetTokenInfo(ctypes.c_ulong(slotid), ctypes.byref(ti))

        if rv:
            output(
                "error",
                f"[gettokeninfo] Failed to get token info ({rv}): {pkcs11error(rv)}",
            )
            msg = f"Failed to get token info ({rv}): {pkcs11error(rv)}"
            raise Exception(msg)
        else:
            output("debug", f"[gettokeninfo] {ti!s}")
        return ti

    def createAES(self, label: bytes, ks: int = 32) -> CK_OBJECT_HANDLE:
        """
        Creates a new AES key with the given label and the given length

        returns the handle
        """

        mechanism = CK_MECHANISM(CKM_AES_KEY_GEN, NULL, 0)

        keysize = ctypes.c_ulong(ks)
        klass = ctypes.c_ulong(CKO_SECRET_KEY)
        keytype = ctypes.c_ulong(CKK_AES)
        ck_true = ctypes.c_ubyte(1)
        ck_false = ctypes.c_ubyte(0)
        objHandle = CK_OBJECT_HANDLE()

        size = 9
        CK_TEMPLATE = CK_ATTRIBUTE * size

        template = CK_TEMPLATE(
            CK_ATTRIBUTE(CKA_CLASS, ctypes.addressof(klass), ctypes.sizeof(klass)),
            CK_ATTRIBUTE(
                CKA_KEY_TYPE, ctypes.addressof(keytype), ctypes.sizeof(keytype)
            ),
            CK_ATTRIBUTE(CKA_LABEL, ctypes.cast(label, ctypes.c_void_p), len(label)),
            CK_ATTRIBUTE(
                CKA_VALUE_LEN, ctypes.addressof(keysize), ctypes.sizeof(keysize)
            ),
            CK_ATTRIBUTE(
                CKA_PRIVATE,
                ctypes.cast(ctypes.addressof(ck_false), ctypes.c_void_p),
                ctypes.sizeof(ck_false),
            ),
            CK_ATTRIBUTE(
                CKA_TOKEN,
                ctypes.cast(ctypes.addressof(ck_true), ctypes.c_void_p),
                ctypes.sizeof(ck_true),
            ),
            CK_ATTRIBUTE(
                CKA_SENSITIVE,
                ctypes.cast(ctypes.addressof(ck_true), ctypes.c_void_p),
                ctypes.sizeof(ck_true),
            ),
            CK_ATTRIBUTE(
                CKA_ENCRYPT,
                ctypes.cast(ctypes.addressof(ck_true), ctypes.c_void_p),
                ctypes.sizeof(ck_true),
            ),
            CK_ATTRIBUTE(
                CKA_DECRYPT,
                ctypes.cast(ctypes.addressof(ck_true), ctypes.c_void_p),
                ctypes.sizeof(ck_true),
            ),
        )

        template_len = ctypes.c_ulong(size)

        rv = self.pkcs11.C_GenerateKey(
            self.hSession,
            ctypes.byref(mechanism),
            template,
            template_len,
            ctypes.byref(objHandle),
        )

        if rv:
            output(
                "error",
                f"[createAES] Failed to C_GenerateKey ({rv}): {pkcs11error(rv)}",
            )
            msg = f"createAES - Failed to C_GenerateKey ({rv}): {pkcs11error(rv)}"
            raise Exception(msg)
        else:
            output(
                "debug",
                f"[createAES] created key successfully: {objHandle!s}",
            )

        return objHandle

    def random(self, l: int = 32) -> bytes:  # noqa: E741
        """
        create a random value and return it
        l specifies the length of the random data to be created.
        """
        output("debug", f"[random] creating {l} random bytes")
        key = b"0" * l
        rv = self.pkcs11.C_GenerateRandom(self.hSession, key, len(key))
        if rv:
            output(
                "error",
                f"C_GenerateRandom failed ({rv}): {pkcs11error(rv)}",
            )
            msg = f"C_GenerateRandom failed ({rv}): {pkcs11error(rv)}"
            raise Exception(msg)
        return key

    def decrypt(self, value: bytes, iv: bytes, id: int = DEFAULT_KEY) -> bytes:
        """
        decrypts the given data, using the IV and the key specified by
        the handle lookup id

        :param data: the encrypted input data
        :param iv: the initialisation vector
        :param id: id in handle dict - possible id's are: 0,1,2
        :return: the decrypted (unpadded) data
        """

        handle = int(self.handles.get(id))
        output("debug", f"[decrypt] decrypting with handle {handle!r}")

        plaintext = ctypes.create_string_buffer(len(value))
        plaintext_len = ctypes.c_ulong(len(plaintext))

        if len(iv) != 16:
            output(
                "error",
                "[decrypt] Doeing aes requires an IV (block size)"
                f" of 16 bytes. {len(iv)} given",
            )
            msg = (
                f"aes.decrypt: Doeing aes requires an IV (block "
                f"size) of 16 bytes. {len(iv)} given"
            )
            raise Exception(msg)

        mechanism = CK_MECHANISM(
            CKM_AES_CBC, ctypes.cast(ctypes.c_char_p(iv), ctypes.c_void_p), len(iv)
        )

        rv = self.pkcs11.C_DecryptInit(
            self.hSession, ctypes.byref(mechanism), CK_OBJECT_HANDLE(handle)
        )
        if rv:
            output(
                "error",
                f"[decrypt] C_DecryptInit failed ({rv}): {pkcs11error(rv)}",
            )
            msg = f"C_DecryptInit failed ({rv}): {pkcs11error(rv)}"
            raise Exception(msg)

        rv = self.pkcs11.C_Decrypt(
            self.hSession,
            value,
            ctypes.c_ulong(len(value)),
            ctypes.byref(plaintext),
            ctypes.byref(plaintext_len),
        )
        if rv:
            output(
                "error",
                f"[decrypt] C_Decrypt failed ({rv}): {pkcs11error(rv)}",
            )
            msg = f"C_Decrypt failed ({rv}): {pkcs11error(rv)}"
            raise Exception(msg)

        return self.unpad(plaintext.value)

    def encrypt(self, data: bytes, iv: bytes, id: int = DEFAULT_KEY) -> bytes:
        """
        encrypts the given input data

        AES CBC works with a blocksize of 16 byte. Thus data must be a multiple
        of 16 bytes. This is as well required for the IV.

        Note: AES_ECB does not require an IV

        :param data: the to-be-encrypted data
        :param iv: the initialisation vector
        :param id: id in handle dict - possible id's are: 0,1,2
        :return: the encrypted byte string
        """
        handle = CK_OBJECT_HANDLE(self.handles.get(id))
        output("debug", f"[encrypt] encrypting with handle {handle!r}")
        data = self.pad(data)

        encrypted_data = ctypes.create_string_buffer(len(data))
        len_encrypted_data = ctypes.c_ulong(len(encrypted_data))

        if len(iv) != 16:
            output(
                "error",
                "[encrypt] Doing aes requires an IV (block size)"
                f" of 16 bytes. {len(iv)} given",
            )
            msg = (
                f"PKCS11.decrypt: Doeing aes requires an IV (block "
                f"size) of 16 bytes. {len(iv)} given"
            )
            raise Exception(msg)

        mechanism = CK_MECHANISM(
            CKM_AES_CBC, ctypes.cast(ctypes.c_char_p(iv), ctypes.c_void_p), len(iv)
        )

        rv = self.pkcs11.C_EncryptInit(self.hSession, ctypes.byref(mechanism), handle)

        if rv:
            output(
                "error",
                f"[encrypt] C_EncryptInit (slot={self.slotid}, handle={handle}) "
                f"failed ({rv}): {pkcs11error(rv)}",
            )

            msg = f"C_EncryptInit failed ({rv}): {pkcs11error(rv)}"
            raise Exception(msg)

        data_buffer = ctypes.create_string_buffer(data)

        rv = self.pkcs11.C_Encrypt(
            self.hSession,
            data_buffer,
            ctypes.c_ulong(len(data)),
            ctypes.byref(encrypted_data),
            ctypes.byref(len_encrypted_data),
        )
        if rv:
            output(
                "error",
                f"[encrypt] C_Encrypt (slot={self.slotid}, handle={handle}) failed "
                f"({rv}): {pkcs11error(rv)}",
            )

        return encrypted_data.value

    def _encryptValue(
        self, value: bytes, keyNum: int = 2, iv: bytes | None = None
    ) -> bytes:
        """
        _encryptValue - base method to encrypt a value
        - uses one slot id to encrypt a string
        retrurns as string with leading iv, seperated by ':'

        :param value: the to be encrypted value
        :type value: byte string

        :param keyNum: slot of the key array
        :type keyNum: int

        :param iv: initialisation vector (optional)
        :type iv: buffer (20 bytes random)

        :return: encrypted data with leading iv and sepeartor ':'
        :rtype:  byte string
        """
        if not iv:
            iv = self.random(16)

        v = self.encrypt(value, iv, keyNum)

        return binascii.hexlify(iv) + b":" + binascii.hexlify(v)

    def _decryptValue(self, cryptStrValue: str, keyNum=2) -> bytes:
        """
        _decryptValue - base method to decrypt a value
        - used one slot id to encrypt a string
          with leading iv, seperated by ':'

        :param cryptStrValue: the to be encrypted value
        :type cryptStrValue: byte string

        :param keyNum: slot of the key array
        :type keyNum: int

        :return: decrypted data
        :rtype:  byte string
        """
        """ split at : """

        pos = cryptStrValue.find(":")
        bIV = cryptStrValue[:pos]
        bData = cryptStrValue[pos + 1 : len(cryptStrValue)]

        iv = binascii.unhexlify(bIV)
        data = binascii.unhexlify(bData)

        return self.decrypt(data, iv, keyNum)

    def decryptPassword(self, cryptPass: str) -> bytes:
        """
        dedicated security module methods: decryptPassword
        which used one slot id to decryt a string

        :param cryptPassword: the crypted password -
                                  leading iv, seperated by the ':'
        :type cryptPassword: byte string

        :return: decrypted data
        :rtype:  byte string
        """
        return self._decryptValue(cryptPass, 0)

    def decryptPin(self, cryptPin: str) -> bytes:
        """
        dedicated security module methods: decryptPin
        which used one slot id to decryt a string

        :param cryptPin: the crypted pin - - leading iv, seperated by the ':'
        :type cryptPin: byte string

        :return: decrypted data
        :rtype:  byte string
        """

        return self._decryptValue(cryptPin, 1)

    def encryptPassword(self, password: bytes) -> str:
        """
        dedicated security module methods: encryptPassword
        which used one slot id to encrypt a string

        :param password: the to be encrypted password
        :type password: byte string

        :return: encrypted data - leading iv, seperated by the ':'
        :rtype:  byte string
        """

        return self._encryptValue(password, 0).decode("utf-8")

    def encryptPin(self, pin: bytes, iv: bytes | None = None) -> str:
        """
        dedicated security module methods: encryptPin
        which used one slot id to encrypt a string

        :param pin: the to be encrypted pin
        :type pin: byte string

        :param iv: initialisation vector (optional)
        :type iv: buffer (20 bytes random)

        :return: encrypted data - leading iv, seperated by the ':'
        :rtype:  byte string
        """
        return self._encryptValue(pin, 1, iv=iv).decode("utf-8")


def main():
    """
    This module can be called to create an AES key.

    Parameters are:

        -p / --password=  The Passwort of the partition. Can be ommitted.
                          Then you are asked
        -s / --slot=      The Slot number (default 0)
        -n / --name=      The name of the AES key.
        -f / --find=      Find the AES key
        -h / --help
        -e / --encrypt=   Encrypt this data (also need slot and handle)
        -l / --label=     Specify the label of the object for encryption

    example:
        create a key:
            pkcs11 -s 1335299873-p 1234-n dummy
        find aes key:
            pkcs11 -s 1335299873-p 1234-f dummy
        encryption:
            pkcs11 -s 1335299873-p 1234-l dummy -e 'this is a test'

    """

    import os  # noqa: PLC0415

    try:
        opts, _args = getopt(
            sys.argv[1:],
            "hp:s:n:f:e:l:",
            [
                "help",
                "password=",
                "slot=",
                "name=",
                "find=",
                "encrypt=",
                "label=",
            ],
        )

    except GetoptError:
        print("There is an error in your parameter syntax:")
        print(main.__doc__)
        sys.exit(1)

    password = None
    slot = 0
    name = None
    listing = False
    label = "default"
    encrypt = None
    l_handle = None

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(main.__doc__)
            sys.exit(0)
        if opt in ("-p", "--password"):
            password = str(arg)
        if opt in ("-s", "--slot"):
            slot = arg
        if opt in ("-n", "--name"):
            name = arg
        if opt in ("-f", "--find"):
            listing = True
            label = arg
        if opt in ("-l", "--label"):
            l_handle = arg
        if opt in ("-e", "--encrypt"):
            encrypt = arg

    if not name and not listing and not encrypt:
        print("Parameter <name> required or list the AES keys.")
        print(main.__doc__)
        sys.exit(1)

    if not password:
        password = getpass.getpass(
            prompt=f"Please enter password for slot {int(slot)}:"
        )

    config = {
        "password": password,
        "slotid": int(slot),
        "library": os.environ.get("PKCS11_DLL", "libCryptoki2_64.so"),
    }

    if l_handle:
        config["defaultLabel"] = l_handle.encode("utf-8")

    P11 = Pkcs11SecurityModule(config)

    if listing:
        keys = P11.find_aes_keys(label=label.encode("utf-8"), wanted=100)
        print(f"Found these AES keys: {keys!r}")

    elif encrypt:
        print(
            f"Encrypting data {encrypt!r} with label {l_handle!r} from slot {slot!r}."
        )

        iv = P11.random(16)

        handle = P11.find_aes_keys(label=l_handle.encode("utf-8"))
        if handle == 0:
            print(
                f"Enryption failed: no handle for aes key found for label {l_handle!r}!"
            )
            return

        crypttext = P11.encrypt(encrypt.encode("utf-8"), iv, DEFAULT_KEY)
        print("Encrypted Text : ", binascii.hexlify(crypttext))

        plaintext = P11.decrypt(crypttext, iv, DEFAULT_KEY)
        print("Decrypted Text >>{}<< ".format(plaintext.decode("utf-8")))

    else:
        handle = P11.find_aes_keys(label=name.encode("utf-8"))

        if not handle:
            handle_object = P11.createAES(label=name.encode("utf-8"))
            print(f"Created AES key {name} with handle {handle_object.value!r}")

    P11.logout()


if __name__ == "__main__":
    running_as_main = True
    main()
