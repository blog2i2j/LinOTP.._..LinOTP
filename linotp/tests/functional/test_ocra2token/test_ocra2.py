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


""" """

import binascii
import json
import logging
import random
import urllib.parse
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from Cryptodome.Hash import SHA256

from linotp.lib.crypto.utils import check, createActivationCode, kdf2
from linotp.lib.ext.pbkdf2 import PBKDF2
from linotp.lib.reply import create_img
from linotp.tests import TestController
from linotp.tokens.ocra2token import OcraSuite

from . import OcraOtp

log = logging.getLogger(__name__)

CHALLLENGE_RUNS = 4


@pytest.mark.nightly
class OcraTest(TestController):
    """
    ocra2 test class:

    TODO: test ocra token with otppi=1 and otppin=2
    """

    fkey = bytes.fromhex("a74f89f9251eda9a5d54a9955be4569f9720abe8")
    key20h = "3132333435363738393031323334353637383930"
    key20 = bytes.fromhex(key20h)

    key32h = "3132333435363738393031323334353637383930313233343536373839303132"
    key32 = bytes.fromhex(key32h)
    key64h = (
        "313233343536373839303132333435363738393031323334353637383930"
        "313233343536373839303132333435363738393031323334353637383930"
        "31323334"
    )
    key64 = bytes.fromhex(key64h)

    pin = "1234"
    pin_sha1 = bytes.fromhex("7110eda4d09e062aa5e4a390b0a572ac0d2c0220")

    testsnp = [
        {
            "ocrasuite": "OCRA-1:HOTP-SHA1-6:QN08",
            "key": key20,
            "keyh": key20h,
            "vectors": [
                {"params": {"Q": "00000000"}, "result": "237653"},
                {"params": {"Q": "11111111"}, "result": "243178"},
                {"params": {"Q": "22222222"}, "result": "653583"},
                {"params": {"Q": "33333333"}, "result": "740991"},
                {"params": {"Q": "44444444"}, "result": "608993"},
                {"params": {"Q": "55555555"}, "result": "388898"},
                {"params": {"Q": "66666666"}, "result": "816933"},
                {"params": {"Q": "77777777"}, "result": "224598"},
                {"params": {"Q": "88888888"}, "result": "750600"},
                {"params": {"Q": "99999999"}, "result": "294470"},
            ],
        },
        {
            "ocrasuite": "OCRA-1:HOTP-SHA512-8:C-QN08",
            "key": key64,
            "keyh": key64h,
            "vectors": [
                {
                    "params": {"C": "00000", "Q": "00000000"},
                    "result": "07016083",
                },
                {
                    "params": {"C": "00001", "Q": "11111111"},
                    "result": "63947962",
                },
                {
                    "params": {"C": "00002", "Q": "22222222"},
                    "result": "70123924",
                },
                {
                    "params": {"C": "00003", "Q": "33333333"},
                    "result": "25341727",
                },
                {
                    "params": {"C": "00004", "Q": "44444444"},
                    "result": "33203315",
                },
                {
                    "params": {"C": "00005", "Q": "55555555"},
                    "result": "34205738",
                },
                {
                    "params": {"C": "00006", "Q": "66666666"},
                    "result": "44343969",
                },
                {
                    "params": {"C": "00007", "Q": "77777777"},
                    "result": "51946085",
                },
                {
                    "params": {"C": "00008", "Q": "88888888"},
                    "result": "20403879",
                },
                {
                    "params": {"C": "00009", "Q": "99999999"},
                    "result": "31409299",
                },
            ],
        },
        {
            "ocrasuite": "OCRA-1:HOTP-SHA512-8:QN08-T1M",
            "key": key64,
            "keyh": key64h,
            "vectors": [
                {
                    "params": {
                        "Q": "00000000",
                        "T_precomputed": int("132d0b6", 16),
                    },
                    "result": "95209754",
                },
                {
                    "params": {
                        "Q": "11111111",
                        "T_precomputed": int("132d0b6", 16),
                    },
                    "result": "55907591",
                },
                {
                    "params": {
                        "Q": "22222222",
                        "T_precomputed": int("132d0b6", 16),
                    },
                    "result": "22048402",
                },
                {
                    "params": {
                        "Q": "33333333",
                        "T_precomputed": int("132d0b6", 16),
                    },
                    "result": "24218844",
                },
                {
                    "params": {
                        "Q": "44444444",
                        "T_precomputed": int("132d0b6", 16),
                    },
                    "result": "36209546",
                },
            ],
        },
    ]

    tests = [
        {
            "ocrasuite": "OCRA-1:HOTP-SHA1-6:QN08",
            "key": key20,
            "keyh": key20h,
            "vectors": [
                {"params": {"Q": "00000000"}, "result": "237653"},
                {"params": {"Q": "11111111"}, "result": "243178"},
                {"params": {"Q": "22222222"}, "result": "653583"},
                {"params": {"Q": "33333333"}, "result": "740991"},
                {"params": {"Q": "44444444"}, "result": "608993"},
                {"params": {"Q": "55555555"}, "result": "388898"},
                {"params": {"Q": "66666666"}, "result": "816933"},
                {"params": {"Q": "77777777"}, "result": "224598"},
                {"params": {"Q": "88888888"}, "result": "750600"},
                {"params": {"Q": "99999999"}, "result": "294470"},
            ],
        },
        {
            "ocrasuite": "OCRA-1:HOTP-SHA256-8:C-QN08-PSHA1",
            "key": key32,
            "keyh": key32h,
            "vectors": [
                {"params": {"C": 0, "Q": "12345678"}, "result": "65347737"},
                {"params": {"C": 1, "Q": "12345678"}, "result": "86775851"},
                {"params": {"C": 2, "Q": "12345678"}, "result": "78192410"},
                {"params": {"C": 3, "Q": "12345678"}, "result": "71565254"},
                {"params": {"C": 4, "Q": "12345678"}, "result": "10104329"},
                {"params": {"C": 5, "Q": "12345678"}, "result": "65983500"},
                {"params": {"C": 6, "Q": "12345678"}, "result": "70069104"},
                {"params": {"C": 7, "Q": "12345678"}, "result": "91771096"},
                {"params": {"C": 8, "Q": "12345678"}, "result": "75011558"},
                {"params": {"C": 9, "Q": "12345678"}, "result": "08522129"},
            ],
        },
        {
            "ocrasuite": "OCRA-1:HOTP-SHA256-8:QN08-PSHA1",
            "key": key32,
            "keyh": key32h,
            "vectors": [
                {"params": {"Q": "00000000"}, "result": "83238735"},
                {"params": {"Q": "11111111"}, "result": "01501458"},
                {"params": {"Q": "22222222"}, "result": "17957585"},
                {"params": {"Q": "33333333"}, "result": "86776967"},
                {"params": {"Q": "44444444"}, "result": "86807031"},
            ],
        },
        {
            "ocrasuite": "OCRA-1:HOTP-SHA512-8:C-QN08",
            "key": key64,
            "keyh": key64h,
            "vectors": [
                {
                    "params": {"C": "00000", "Q": "00000000"},
                    "result": "07016083",
                },
                {
                    "params": {"C": "00001", "Q": "11111111"},
                    "result": "63947962",
                },
                {
                    "params": {"C": "00002", "Q": "22222222"},
                    "result": "70123924",
                },
                {
                    "params": {"C": "00003", "Q": "33333333"},
                    "result": "25341727",
                },
                {
                    "params": {"C": "00004", "Q": "44444444"},
                    "result": "33203315",
                },
                {
                    "params": {"C": "00005", "Q": "55555555"},
                    "result": "34205738",
                },
                {
                    "params": {"C": "00006", "Q": "66666666"},
                    "result": "44343969",
                },
                {
                    "params": {"C": "00007", "Q": "77777777"},
                    "result": "51946085",
                },
                {
                    "params": {"C": "00008", "Q": "88888888"},
                    "result": "20403879",
                },
                {
                    "params": {"C": "00009", "Q": "99999999"},
                    "result": "31409299",
                },
            ],
        },
        {
            "ocrasuite": "OCRA-1:HOTP-SHA512-8:QN08-T1M",
            "key": key64,
            "keyh": key64h,
            "vectors": [
                {
                    "params": {
                        "Q": "00000000",
                        "T_precomputed": int("132d0b6", 16),
                    },
                    "result": "95209754",
                },
                {
                    "params": {
                        "Q": "11111111",
                        "T_precomputed": int("132d0b6", 16),
                    },
                    "result": "55907591",
                },
                {
                    "params": {
                        "Q": "22222222",
                        "T_precomputed": int("132d0b6", 16),
                    },
                    "result": "22048402",
                },
                {
                    "params": {
                        "Q": "33333333",
                        "T_precomputed": int("132d0b6", 16),
                    },
                    "result": "24218844",
                },
                {
                    "params": {
                        "Q": "44444444",
                        "T_precomputed": int("132d0b6", 16),
                    },
                    "result": "36209546",
                },
            ],
        },
    ]

    def setUp(self):
        TestController.setUp(self)

        self.create_common_resolvers()
        self.create_common_realms()
        self.removeTokens()
        self.setupPolicies()
        self.setupOcraPolicy()

    def tearDown(self):
        self.delete_all_policies()
        self.delete_all_realms()
        self.delete_all_resolvers()
        TestController.tearDown(self)

    def setupOcraPolicy(self):
        """
        This sets up the ocra policy right
        """
        params = {
            "name": "ocra_allowance",
            "realm": "mydefrealm",
            "user": "ocra_admin",
            "scope": "ocra",
            "action": "request, status, activationcode, calcOTP",
        }
        response = self.make_system_request("setPolicy", params=params)
        assert '"setPolicy ocra_allowance"' in response, response
        assert '"status": true' in response, response

    def setupPolicies(self, check_url="http://127.0.0.1/validate/check_t"):
        self.delete_all_policies()

        params = {
            "name": "CheckURLPolicy",
            "scope": "authentication",
            "realm": "mydefrealm",
        }
        params["action"] = (
            "qrtanurl.one=https://<user>:<password>@my.one.de/callback/<serial>/<transactionid>/, "
            f"qrtanurl={check_url!s}, "
            "qrtanurl_init=https://<user>:<password>@my.default.de/ini/callback/<serial>/,"
            "qrtanurl_init.one=https://<user>:<password>@my.one.de/ini/callback/<serial>/,"
        )

        response = self.make_system_request("setPolicy", params=params)

        assert '"setPolicy CheckURLPolicy"' in response, response
        assert '"status": true' in response, response
        return response

    def check_otp(self, transid, otp, pin="pin", params=None):
        """-3.a- verify the otp value to finish the rollout"""
        parameters = {}
        if params:
            parameters.update(params)
        parameters["transactionid"] = transid
        parameters["pass"] = "" + pin + otp
        response = self.make_validate_request("check_t", params=parameters)
        return response

    def gen_challenge_data(self):
        testchall = [
            {
                "ocrasuite": "OCRA-1:HOTP-SHA256-6:C-QA64",
                "key": "12345678901234567890",
                "app_import1": (
                    "lseqr://init?sh=12345678901234567890&"
                    "os=OCRA-1%3AHOTP-SHA256-6%3AC-QA64&"
                    "se=LSOC00000001"
                ),
                "app_import2": (
                    "lseqr://nonce?me=abcdefg+1234567+%2B-"
                    "%2A%23+%C3%B6%C3%A4%C3%BC%C3%9F&"
                    "ch=abcdefg12345670000Xch3tNAkIWpmj6d"
                    "u0PVBSvFOmJqWu0wq9AL9BKYxGjGkVg&"
                    "no=492321549d56446d31682adabe64efc4bc"
                    "6d7f0e31202ebdd75335b550a87690a1a3fcaf"
                    "c9e52a04e4dde40dea5634ad0c7becfe9d3961"
                    "690b95d135844b866d&tr=954472011597&"
                    "u=http%253A%252F%252F127.0.0.1%252Focra"
                    "%252Fcheck_t&se=LSOC00000001&"
                    "si=790eb52b398c5b37aaeba56b374947e0b31"
                    "93ff98e2553c04ac15ae49440abb9"
                ),
                "vectors": [
                    {"param": {"data": "irgendwas"}, "otp": "12345"},
                    {"param": {"data": "DasisteinTest"}, "otp": "12345"},
                    {"param": {"data": "Irgendwas"}, "otp": "12345"},
                    {"param": {"data": "1234567890123"}, "otp": "12345"},
                    {"param": {"data": "Dasisteintest"}, "otp": "12345"},
                    {"param": {"data": "Dasisteintest"}, "otp": "12345"},
                    {"param": {"data": "Dasist"}, "otp": "12345"},
                    {"param": {"data": "EinTestdasist"}, "otp": "12345"},
                    {"param": {"data": "ss"}, "otp": "12345"},
                    {"param": {"data": "SS"}, "otp": "12345"},
                    {
                        "param": {"data": "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS"},
                        "otp": "12345",
                    },
                    {"param": {"data": "DasisteinTExt"}, "otp": "12345"},
                    {"param": {"data": "Das"}, "otp": "12345"},
                    {"param": {"data": "EinLeerzeichen"}, "otp": "12345"},
                    {"param": {"data": "Ein Leerzeichen"}, "otp": "12345"},
                    {"param": {"data": "Ein+Leerzeichen"}, "otp": "12345"},
                ],
            },
        ]

        self.setupPolicies(check_url="https://ebanking.1882.de")

        tt = []
        for test in testchall:
            testdata = {}

            ocra = OcraOtp()
            response1 = self.init_0_QR_Token(user="root", ocrasuite=test["ocrasuite"])
            ocra.init_1(response1)

            jresp = json.loads(response1.body)
            assert "detail" in jresp, response1.body
            app_import_1 = str(jresp.get("detail", {}).get("app_import"))

            message = "abc"
            (response2, activationkey) = self.init_1_QR_Token(
                user="root",
                message=message,
                activationkey="GEZDGNBVGY3TQOJQ01",
                ocrasuite=test["ocrasuite"],
            )
            (challenge, transid) = ocra.init_2(response2, activationkey)

            jresp = json.loads(response2.body)
            assert "detail" in jresp, response2.body
            app_import_2 = str(jresp.get("detail", {}).get("app_import"))

            testdata["ocrasuite"] = ocra.ocrasuite
            testdata["nonce"] = ocra.nonce
            testdata["activationcode"] = ocra.activationkey
            testdata["sharedsecret"] = ocra.sharedsecret
            testdata["app_import_1"] = app_import_1
            testdata["app_import_2"] = app_import_2

            counter = 0
            # finish rollout
            otp = ocra.callcOtp(challenge, counter=counter)

            bkey = ocra.bkey
            key = binascii.hexlify(bkey)
            testdata["key"] = key

            response = self.check_otp(transid, otp)
            assert '"value": true' in response, response

            testv = []

            # initial challenge
            test_set = {}
            test_set["message"] = message
            test_set["data"] = app_import_2
            test_set["challenge"] = challenge
            test_set["otp"] = otp
            testv.append(test_set)

            for v in test.get("vectors"):
                param = v.get("param")
                # get next challenge
                (response, challenge, transid) = self.get_challenge(
                    ocra.serial, challenge_data=param.get("data")
                )

                jresp = json.loads(response.body)
                assert "detail" in jresp, response.body
                app_import = str(jresp.get("detail", {}).get("data"))
                challenge = str(jresp.get("detail", {}).get("challenge"))

                counter += 1
                otp = ocra.callcOtp(challenge, counter=counter)

                # correct response
                response = self.check_otp(transid, otp)
                assert '"value": true' in response, response

                # push test data in our test set
                test_set = {}
                test_set["message"] = param.get("data")
                test_set["data"] = app_import
                test_set["challenge"] = challenge
                test_set["otp"] = otp
                testv.append(test_set)

            testdata["vectors"] = testv
            tt.append(testdata)

        self.removeTokens(serial=ocra.serial)

        with open("/tmp/challengeTestSet", "w+", encoding="utf-8") as f:
            testStr = json.dumps(tt, indent=4)
            f.write(testStr)

    def randOTP(self, otp):
        """randomly change the chars in an otp - to gen a wrong otp"""
        rotp = otp
        text = list(otp)

        while rotp == otp:
            random.shuffle(text)
            rotp = "".join(text)

        return rotp

    def init_0_QR_Token(
        self,
        tokentype="ocra2",
        ocrapin="",
        pin="pin",
        user=None,
        serial=None,
        description="QRTestToken",
        sharedsecret="1",
        genkey="1",
        otpkey=None,
        ocrasuite="OCRA-1:HOTP-SHA256-8:C-QA64",
        realm=None,
        params=None,
    ):
        """-1- create an ocra token"""

        parameters = {}
        if params:
            parameters.update(params)

        if tokentype is not None:
            parameters["type"] = tokentype

        if pin is not None:
            parameters["pin"] = pin

        if genkey is not None:
            parameters["genkey"] = genkey

        if otpkey is not None:
            parameters["otpkey"] = otpkey

        if sharedsecret is not None:
            parameters["sharedsecret"] = sharedsecret

        if ocrapin is not None:
            parameters["ocrapin"] = ocrapin

        if ocrasuite is not None:
            parameters["ocrasuite"] = ocrasuite

        if user is not None:
            parameters["user"] = user

        if serial is not None:
            parameters["serial"] = serial

        if realm:
            parameters["realm"] = realm

        response = self.make_admin_request("init", params=parameters)
        return response

    def init_1_QR_Token(
        self,
        activationkey=None,
        tokentype="ocra2",
        serial=None,
        user=None,
        pin="pin",
        message="Message",
        ocrapin="",
        genkey="1",
        ocrasuite=None,
        realm=None,
        params=None,
    ):
        # -2- acivate ocra token
        parameters = {}
        if params:
            parameters.update(params)

        if tokentype is not None:
            parameters["type"] = tokentype

        if pin is not None:
            parameters["pin"] = pin

        if message is not None:
            parameters["message"] = message

        if genkey is not None:
            parameters["genkey"] = genkey

        if ocrapin is not None:
            parameters["ocrapin"] = ocrapin

        if user is not None:
            parameters["user"] = user
        elif serial is not None:
            parameters["serial"] = serial

        if realm:
            parameters["realm"] = realm

        if activationkey is None:
            activationkey = createActivationCode("1234567890")
        parameters["activationcode"] = activationkey

        if ocrasuite is not None:
            parameters["ocrasuite"] = ocrasuite

        response = self.make_admin_request("init", params=parameters)
        return (response, activationkey)

    def test_ocrasuite(self):
        """
        test_ocrasuite: test the given ocra suite test set
        """
        for test in self.tests:
            ocra = OcraSuite(test["ocrasuite"])
            key = test["key"]
            for vector in test["vectors"]:
                params = vector["params"]
                result = vector["result"]
                if ocra.P is not None:
                    params["P"] = self.pin
                if ocra.T is not None:
                    pass
                data = ocra.combineData(**params)
                otp = ocra.compute(data, key)
                assert otp == result

    def test_feitan_ocrasuite(self):
        """
        test_feitan_ocrasuite: test feitan ocra token
        """
        # Feitians OCRA suite:
        ocrasuite = "OCRA-1:HOTP-SHA1-6:QN06-T1M"
        key = "a74f89f9251eda9a5d54a9955be4569f9720abe8"
        ocrapin = "myocrapin"
        serial = "QR_One1"

        ocra = OcraSuite(ocrasuite)
        params = {"Q": "000000"}
        result = "335862"
        now = datetime.utcnow()
        nowtime = now
        for t in range(1, 24 * 60 * 60):
            nowtime = now - timedelta(minutes=t)
            stime = nowtime.strftime("%s")
            itime = int(stime)
            params["T"] = itime

            data = ocra.combineData(**params)
            otp = ocra.compute(data, binascii.unhexlify(key))
            if otp == result:
                print(f" time for otp {result} : {nowtime!s}")
                break

        # -1- create an ocra token
        parameters = {
            "serial": serial,
            "user": "root",
            "pin": "pin",
            "description": "first QRToken",
            "type": "ocra2",
            # 'genkey':   '1',
            "otpkey": key,
            "ocrapin": ocrapin,
            "ocrasuite": ocrasuite,
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        # -2- fetch the challenge
        p = {"serial": serial, "data": ""}

        response = self.make_validate_request("check_s", params=p)
        assert '"value": false' in response, response

        # -3.a- calculate the otp response from the challenge
        jresp = json.loads(response.body)
        assert "detail" in jresp, response.body
        challenge = str(jresp.get("detail", {}).get("challenge"))
        transid = str(jresp.get("detail", {}).get("transactionid"))

        ocra = OcraSuite(ocrasuite)

        param = {}
        param["C"] = 0
        param["Q"] = challenge
        param["P"] = ocrapin
        param["S"] = ""
        if ocra.T is not None:
            # Default value for G is 1M, i.e., time-step size is one minute and
            # the T represents the number of minutes since epoch time [UT].
            now = datetime.utcnow()
            stime = now.strftime("%s")
            itime = int(stime)
            param["T"] = itime
            date = datetime.fromtimestamp(itime)
            log.debug("Start for challenge %r", date)

        ocra = OcraSuite(ocrasuite)
        data = ocra.combineData(**param)
        otp = ocra.compute(data, binascii.unhexlify(key))

        # -3.b- verify the otp value
        parameters = {
            "transactionid": transid,
            "pass": "pin" + otp,
        }
        response = self.make_validate_request("check_t", params=parameters)
        assert '"value": true' in response, response

        # -1- create an ocra token
        parameters = {
            "serial": serial,
        }
        response = self.make_admin_request("remove", params=parameters)
        assert '"value": 1' in response, response

    def removeTokens(self, user=None, serial=None):
        serials = []

        if user is not None:
            p = {"user": user}
            response = self.make_admin_request("remove", params=p)
            assert '"value": 1' in response, response

        if serial is not None:
            p = {"serial": serial}
            response = self.make_admin_request("remove", params=p)
            assert '"value": 1' in response, response

        if serial is None and user is None:
            parameters = {}
            response = self.make_admin_request("show", params=parameters)
            assert '"status": true' in response, response

            jresp = json.loads(response.body)
            assert "result" in jresp, response.body
            d_root = jresp.get("result", {}).get("value", {}).get("data")
            for tok in d_root:
                serial = tok.get("LinOtp.TokenSerialnumber")
                serials.append(serial)

            for serial in serials:
                p = {"serial": serial}
                response = self.make_admin_request("remove", params=p)
                assert '"value": 1' in response, response

    def test_QR_token(self):
        """
        test_QR_rollout_wrong_activation: enroll an QR Token

        0. request for an token
        1a. fetch the output and generate an AKTIVIERUNGSCODE
        1b. send second init request with Activation code
        2. finish token creation  and return first transaction Id
        3. reply the challenge

        @summary: this test is the first simple positive test, which uses
                  the serial number of the token, to identify the
                  transaction

        @todo:     more tests,
                - which uses the user who could have multiple tokens, but
                  only one QR-Token
                - check OCRA Token and TOTP tests
                - check OCRA with HOTP counter token
                - check OCRA Token with user pin
        """
        ocrasuite = "OCRA-1:HOTP-SHA256-8:QA64"
        log.info("##################### %s", ocrasuite)
        ocrapin = "myocrapin"

        # -1- create an ocra token
        parameters = {
            "user": "root",
            "pin": "pin",
            "description": "first QRToken",
            "type": "ocra2",
            "sharedsecret": "1",
            "genkey": "1",
            "ocrapin": ocrapin,
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        # on the return we get the shared secret
        jresp = json.loads(response.body)
        assert "detail" in jresp, response.body
        app_import = str(jresp.get("detail", {}).get("app_import"))
        sharedsecret = str(jresp.get("detail", {}).get("sharedsecret"))
        serial = str(jresp.get("detail", {}).get("serial"))

        # now parse the appurl for the ocrasuite
        uri = urlparse(app_import.replace("lseqr://", "http://"))
        qs = uri.query
        qdict = parse_qs(qs)

        ocrasuite = qdict.get("os", None)
        if ocrasuite is not None and len(ocrasuite) > 0:
            ocrasuite = ocrasuite[0]

        activationcode = createActivationCode()
        parameters = {
            "user": "root",
            "pin": "pin",
            "description": "first QRToken",
            "type": "ocra2",
            "message": "MESSAGE&",
            "genkey": "1",
            "ocrapin": ocrapin,
        }

        parameters["activationcode"] = activationcode
        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        # -3.a- we got on the return side a transactionId and a challenge

        jresp = json.loads(response.body)
        assert "detail" in jresp, response.body
        _nonce = str(jresp.get("detail", {}).get("nonce"))
        transid = str(jresp.get("detail", {}).get("transactionid"))
        app_import = str(jresp.get("detail", {}).get("app_import"))

        # now parse the appurl for the ocrasuite
        uri = urlparse(app_import.replace("lseqr://", "http://"))
        qs = uri.query
        qdict = parse_qs(qs)
        nonce = qdict.get("no", None)
        if nonce is not None and len(nonce) > 0:
            nonce = nonce[0]

        challenge = qdict.get("ch", None)
        if challenge is not None and len(challenge) > 0:
            challenge = challenge[0]

        # now we have all in place for the key derivation to create the new key
        #  sharedsecret, activationcode and nonce

        key_len = 20
        if ocrasuite.find("-SHA256"):
            key_len = 32
        elif ocrasuite.find("-SHA512"):
            key_len = 64

        newkey = kdf2(sharedsecret, nonce, activationcode, len=key_len)

        ocra = OcraSuite(ocrasuite)

        param = {}
        param["C"] = 0
        param["Q"] = challenge
        param["P"] = ocrapin
        param["S"] = ""
        if ocra.T is not None:
            # Default value for G is 1M, i.e., time-step size is one minute and
            # the T represents the number of minutes since epoch time [UT].
            now = datetime.utcnow()
            stime = now.strftime("%s")
            itime = int(stime)
            param["T"] = itime

        data = ocra.combineData(**param)
        otp = ocra.compute(data, newkey)

        # -2- finalize enrollment
        p = {"transactionid": transid, "pass": "pin" + otp}

        response = self.make_validate_request("check_t", params=p)
        assert '"value": true' in response, response

        for count in range(1, 20):
            # -2- fetch the challenge
            p = {"serial": serial, "data": ""}

            response = self.make_validate_request("check_s", params=p)
            assert '"value": false' in response, response

            # -3.a- calculate the otp response from the challenge
            jresp = json.loads(response.body)
            assert "detail" in jresp, response.body
            challenge = str(jresp.get("detail", {}).get("challenge"))
            transid = str(jresp.get("detail", {}).get("transactionid"))

            ocra = OcraSuite(ocrasuite)

            param = {}
            param["C"] = count
            param["Q"] = challenge
            param["P"] = ocrapin
            param["S"] = ""
            if ocra.T is not None:
                #  Default value for G is 1M, i.e., time-step size is one
                # minute and the T represents the number of minutes since
                # epoch time [UT].

                now = datetime.utcnow()
                stime = now.strftime("%s")
                itime = int(stime)
                param["T"] = itime
                date = datetime.fromtimestamp(itime)
                log.info("Start for challenge %r", date)

            data = ocra.combineData(**param)
            otp = ocra.compute(data, newkey)

            # -3.b- verify the otp value
            parameters = {
                "transactionid": transid,
                "pass": "pin" + otp,
            }
            response = self.make_validate_request("check_t", params=parameters)
            assert '"value": true' in response, response

        # -remove the ocra token
        parameters = {
            "serial": serial,
        }
        response = self.make_admin_request("remove", params=parameters)
        assert '"value": 1' in response, response

    def test_QR_token_4_Markus(self):
        """
        enroll an QR Token - 4 Markus, with a given input key

        0. request for an token
        1a. fetch the output and generate an AKTIVIERUNGSCODE
        1b. send second init request with Activation code
        2. finish token creation  and return first transaction Id
        3. reply the challenge
        4. challenge / reply multiple times (20)

        """
        ocrasuite = "OCRA-1:HOTP-SHA256-8:QA64"
        log.info("##################### %s", ocrasuite)
        ocrapin = "myocrapin"
        key = self.key32h

        # -1- create an ocra token
        parameters = {
            "user": "root",
            "pin": "pin",
            "description": "first QRToken",
            "type": "ocra2",
            "sharedsecret": "1",
            "otpkey": key,
            "ocrapin": ocrapin,
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        # on the return we get the shared secret
        jresp = json.loads(response.body)
        assert "detail" in jresp, response.body
        app_import = str(jresp.get("detail", {}).get("app_import"))
        sharedsecret = str(jresp.get("detail", {}).get("sharedsecret"))
        serial = str(jresp.get("detail", {}).get("serial"))

        # now parse the appurl for the ocrasuite
        uri = urlparse(app_import.replace("lseqr://", "http://"))
        qs = uri.query
        qdict = parse_qs(qs)

        ocrasuite = qdict.get("os", None)
        if ocrasuite is not None and len(ocrasuite) > 0:
            ocrasuite = ocrasuite[0]

        # activationcode = createActivationCode()
        # activationcode ='4XQRSVTKUNH7ETQYTVNXKWFUB4EZ4NC3C1'
        # taken from my iPhone, line 1189 was sometimes failing
        activationcode = "3U6X422SYZXLV6HSBF"

        parameters = {
            "user": "root",
            "pin": "pin",
            "description": "first QRToken",
            "type": "ocra2",
            "message": "MESSAGE",
            "ocrapin": ocrapin,
        }

        parameters["activationcode"] = activationcode
        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        # -3.a- we got on the return side a transactionId and a challenge
        jresp = json.loads(response.body)
        assert "detail" in jresp, response.body
        _nonce = str(jresp.get("detail", {}).get("nonce"))
        transid = str(jresp.get("detail", {}).get("transactionid"))
        app_import = str(jresp.get("detail", {}).get("app_import"))

        # now parse the appurl for the ocrasuite
        uri = urlparse(app_import.replace("lseqr://", "http://"))
        qs = uri.query
        qdict = parse_qs(qs)
        nonce = qdict.get("no", None)
        if nonce is not None and len(nonce) > 0:
            nonce = nonce[0]

        challenge = qdict.get("ch", None)
        if challenge is not None and len(challenge) > 0:
            challenge = challenge[0]

        # now we have all in place for the key derivation to create the new key
        #   sharedsecret, activationcode and nonce
        key_len = 20
        if ocrasuite.find("-SHA256"):
            key_len = 32
        elif ocrasuite.find("-SHA512"):
            key_len = 64

        newkey = kdf2(sharedsecret, nonce, activationcode, len=key_len)
        hnewkey = binascii.hexlify(newkey)
        ocra = OcraSuite(ocrasuite)

        log.debug("%r", hnewkey)

        param = {}
        param["C"] = 0
        param["Q"] = challenge
        param["P"] = ocrapin
        param["S"] = ""
        if ocra.T is not None:
            # Default value for G is 1M, i.e., time-step size is one minute and
            # the T represents the number of minutes since epoch time [UT].

            now = datetime.utcnow()
            stime = now.strftime("%s")
            itime = int(stime)
            param["T"] = itime

        data = ocra.combineData(**param)
        otp = ocra.compute(data, newkey)

        # -2- finalize enrollment
        p = {"transactionid": transid, "pass": "pin" + otp}

        response = self.make_validate_request("check_t", params=p)
        assert '"value": true' in response, response

        for count in range(1, 20):
            # -2- fetch the challenge
            p = {"serial": serial, "data": ""}

            response = self.make_validate_request("check_s", params=p)
            assert '"value": false' in response, response

            # -3.a- calculate the otp response from the challenge
            jresp = json.loads(response.body)
            assert "detail" in jresp, response.body
            challenge = str(jresp.get("detail", {}).get("challenge"))
            transid = str(jresp.get("detail", {}).get("transactionid"))

            ocra = OcraSuite(ocrasuite)

            param = {}
            param["C"] = count
            param["Q"] = challenge
            param["P"] = ocrapin
            param["S"] = ""
            if ocra.T is not None:
                # Default value for G is 1M, i.e., time-step size is one minute
                # and the T represents the number of minutes since
                # epoch time [UT].
                now = datetime.utcnow()
                stime = now.strftime("%s")
                itime = int(stime)
                param["T"] = itime
                date = datetime.fromtimestamp(itime)
                log.info("Start for challenge %r", date)

            data = ocra.combineData(**param)
            otp = ocra.compute(data, newkey)

            # -3.b- verify the otp value
            parameters = {"transactionid": transid, "pass": "pin" + otp}
            response = self.make_validate_request("check_t", params=parameters)
            assert '"value": true' in response, f"Response 3.b\n{response}"

        # -remove the ocra token
        parameters = {
            "serial": serial,
        }
        response = self.make_admin_request("remove", params=parameters)
        assert '"value": 1' in response, response

    def test_QR_token_init_fail(self):
        """
        test_QR_token_init_fail: enroll an QR Token - while check_t fails
        - should switch back to rollout 1 state

        0. request for an token
        1a. fetch the output and generate an AKTIVIERUNGSCODE
        1b. send second init request with Activation code
        2. finish token creation  and return first transaction Id
        3. reply the challenge

        @summary: this test is the first simple positive test, which uses
                  the serial number of the token, to identify the
                  transaction

        @todo:     more tests,
                - which uses the user who could have multiple tokens, but
                  only one QR-Token
                - check OCRA Token and TOTP tests
                - check OCRA with HOTP counter token
                - check OCRA Token with user pin
        """
        ocrasuite = "OCRA-1:HOTP-SHA256-8:QA64"
        log.info("##################### %s", ocrasuite)
        ocrapin = "myocrapin"

        # -1- create an ocra token
        parameters = {
            "user": "root",
            "pin": "pin",
            "description": "first QRToken",
            "type": "ocra2",
            "sharedsecret": "1",
            "genkey": "1",
            "ocrapin": ocrapin,
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        # on the return we get the shared secret
        jresp = json.loads(response.body)
        assert "detail" in jresp, response.body
        app_import = str(jresp.get("detail", {}).get("app_import"))
        sharedsecret = str(jresp.get("detail", {}).get("sharedsecret"))
        serial = str(jresp.get("detail", {}).get("serial"))

        # now parse the appurl for the ocrasuite
        uri = urlparse(app_import.replace("lseqr://", "http://"))
        qs = uri.query
        qdict = parse_qs(qs)

        ocrasuite = qdict.get("os", None)
        if ocrasuite is not None and len(ocrasuite) > 0:
            ocrasuite = ocrasuite[0]

        activationcode = createActivationCode("12345678")

        parameters = {
            "user": "root",
            "pin": "pin",
            "description": "first QRToken",
            "type": "ocra2",
            "message": "MESSAGE&",
            "genkey": "1",
            "ocrapin": ocrapin,
        }

        parameters["activationcode"] = activationcode

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        # -3.a- we got on the return side a transactionId and a challenge

        jresp = json.loads(response.body)
        assert "detail" in jresp, response.body
        _nonce = str(jresp.get("detail", {}).get("nonce"))
        transid = str(jresp.get("detail", {}).get("transactionid"))
        app_import = str(jresp.get("detail", {}).get("app_import"))

        # now parse the appurl for the ocrasuite
        uri = urlparse(app_import.replace("lseqr://", "http://"))
        qs = uri.query
        qdict = parse_qs(qs)
        nonce = qdict.get("no", None)
        if nonce is not None and len(nonce) > 0:
            nonce = nonce[0]

        challenge = qdict.get("ch", None)
        if challenge is not None and len(challenge) > 0:
            challenge = challenge[0]

        # now we have all in place for the key derivation to create the new key
        #  sharedsecret, activationcode and nonce
        key_len = 20
        if ocrasuite.find("-SHA256"):
            key_len = 32
        elif ocrasuite.find("-SHA512"):
            key_len = 64

        newkey = kdf2(sharedsecret, nonce, activationcode, len=key_len)

        ocra = OcraSuite(ocrasuite)

        param = {}
        param["C"] = 0
        param["Q"] = challenge
        param["P"] = ocrapin
        param["S"] = ""
        if ocra.T is not None:
            # Default value for G is 1M, i.e., time-step size is one minute and
            # the T represents the number of minutes since epoch time [UT].
            now = datetime.utcnow()
            stime = now.strftime("%s")
            itime = int(stime)
            param["T"] = itime

        data = ocra.combineData(**param)
        otp = ocra.compute(data, newkey)

        otp_f = otp.replace("8", "9")
        otp_f = otp_f.replace("7", "8")
        otp_f = otp_f.replace("6", "7")
        otp_f = otp_f.replace("5", "6")
        otp_f = otp_f.replace("4", "5")
        otp_f = otp_f.replace("3", "4")
        otp_f = otp_f.replace("2", "3")
        otp_f = otp_f.replace("1", "2")
        otp_f = otp_f.replace("0", "1")

        # -2- finalize enrollment
        p = {"transactionid": transid, "pass": "pin" + otp_f}

        response = self.make_validate_request("check_t", params=p)
        assert '"value": false' in response, response

        parameters = {
            "user": "root",
            "pin": "pin",
            "description": "first QRToken",
            "type": "ocra2",
            "message": "MESSAGE&",
            "genkey": "1",
            "ocrapin": ocrapin,
        }

        parameters["activationcode"] = activationcode
        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        # -3.a- we got on the return side a transactionId and a challenge

        jresp = json.loads(response.body)
        assert "detail" in jresp, response.body
        try:
            nonce = str(jresp.get("detail", {}).get("nonce"))
            transid = str(jresp.get("detail", {}).get("transactionid"))
            app_import = str(jresp.get("detail", {}).get("app_import"))
        except Exception as e:
            log.debug(" %r", e)

        # now parse the appurl for the ocrasuite
        uri = urlparse(app_import.replace("lseqr://", "http://"))
        qs = uri.query
        qdict = parse_qs(qs)
        nonce = qdict.get("no", None)
        if nonce is not None and len(nonce) > 0:
            nonce = nonce[0]

        challenge = qdict.get("ch", None)
        if challenge is not None and len(challenge) > 0:
            challenge = challenge[0]

        # now we have all in place for the key derivation to create the new key
        #  sharedsecret, activationcode and nonce
        key_len = 20
        if ocrasuite.find("-SHA256"):
            key_len = 32
        elif ocrasuite.find("-SHA512"):
            key_len = 64

        newkey = kdf2(sharedsecret, nonce, activationcode, len=key_len)

        ocra = OcraSuite(ocrasuite)

        param = {}
        param["C"] = 0
        param["Q"] = challenge
        param["P"] = ocrapin
        param["S"] = ""
        if ocra.T is not None:
            # Default value for G is 1M, i.e., time-step size is one minute and
            # the T represents the number of minutes since epoch time [UT].
            now = datetime.utcnow()
            stime = now.strftime("%s")
            itime = int(stime)
            param["T"] = itime

        data = ocra.combineData(**param)
        otp = ocra.compute(data, newkey)

        # -2- finalize enrollment
        p = {"transactionid": transid, "pass": "pin" + otp}

        response = self.make_validate_request("check_t", params=p)
        assert '"value": true' in response, response

        # -1- create an ocra token
        parameters = {"serial": serial}
        response = self.make_admin_request("remove", params=parameters)
        assert '"value": 1' in response, response

    def test_OCRA_token(self):
        """
        test_OCRA_token: simple token test for OCRA token

        1. create an ocra token
        2. fetch the challange
        3.a. calculate the OTP response from the challenge
        3.b. submit the response

        @summary: this test is the first simple positive test, which uses
                  the serial number of the token, to identify the
                  transaction

        @todo:     more tests,
                - which uses the user who could have multiple tokens, but
                  only on QR-Token
                - check OCRA Token and TOTP tests
                - check OCRA with HOTP counter token
                - check OCRA Token with user pin
        """
        ocrasuite = "OCRA-1:HOTP-SHA256-8:QA64"
        for t_count, test in enumerate(self.tests[0:1], 1):
            ocrasuite = test["ocrasuite"]

            key = test["keyh"]
            bkey = test["key"]

            log.info("##################### %s", ocrasuite)
            ocrapin = "myocrapin"
            serial = f"OCRA_TOKEN_{t_count}"

            # -1- create an ocra token
            parameters = {
                "serial": serial,
                "user": "root",
                "pin": "pin",
                "description": "first QRToken",
                "type": "ocra2",
                "otpkey": key,
                "ocrapin": ocrapin,
                "ocrasuite": ocrasuite,
            }

            response = self.make_admin_request("init", params=parameters)
            assert '"value": true' in response, response

            for count in range(CHALLLENGE_RUNS):
                # -2- fetch the challenge
                p = {
                    "serial": serial,
                    "data": "0105037311 Konto 50150850 BLZ 1752,03 Eur",
                }

                response = self.make_validate_request("check_s", params=p)
                assert '"value": false' in response, response

                # -3.a- calculate the otp response from the challenge
                jresp = json.loads(response.body)
                assert "detail" in jresp, response.body
                challenge = str(jresp.get("detail", {}).get("challenge"))
                transid = str(jresp.get("detail", {}).get("transactionid"))

                ocra = OcraSuite(ocrasuite)

                param = {}
                param["C"] = count
                param["Q"] = challenge
                param["P"] = ocrapin
                param["S"] = ""
                if ocra.T is not None:
                    # Default value for G is 1M, i.e., time-step size is one
                    # minute and the T represents the number of minutes since
                    # epoch time [UT].
                    now = datetime.utcnow()
                    stime = now.strftime("%s")
                    itime = int(stime)
                    param["T"] = itime

                ocra = OcraSuite(ocrasuite)
                data = ocra.combineData(**param)
                otp = ocra.compute(data, bkey)

                # -3.b- verify the otp value
                parameters = {
                    "transactionid": transid,
                    "pass": "pin" + otp,
                }
                response = self.make_validate_request("check_t", params=parameters)
                # TB Fixed
                if '"value": true' not in response:
                    log.info("response %s\n", response)
                    log.error("test: failed for otp context: %r ", param)
                    log.error("datainput: %s", binascii.hexlify(data))

                    _response2 = self.make_validate_request(
                        "check_t", params=parameters
                    )

                    assert '"value": true' in response, response

                # -4- check the transaction status
                parameters = {"transactionid": transid}
                response = self.make_admin_request("checkstatus", params=parameters)
                assert '"status": true' in response, response

            # delete the ocra token
            parameters = {
                "serial": serial,
            }
            response = self.make_admin_request("remove", params=parameters)
            assert '"value": 1' in response, response

    def test_OCRA_token_validate_check(self):
        """
        test_OCRA_token_validate_check: verify the OCRA token from the challenge with the standard check

        1. create an ocra token
        2. fetch the challange
        3.a. calculate the OTP response from the challenge
        3.b. submit the response


        """
        ocrasuite = "OCRA-1:HOTP-SHA256-8:QA64"
        for test in self.tests[1:2]:
            ocrasuite = test["ocrasuite"]
            key = test["keyh"]
            bkey = test["key"]

            log.info("##################### %s", ocrasuite)
            ocrapin = "myocrapin"
            serial = "QR_One1b"
            # -1- create an ocra token
            parameters = {
                "serial": serial,
                "user": "root",
                "pin": "pin",
                "description": "first QRToken",
                "type": "ocra2",
                "ocrapin": ocrapin,
                "otpkey": key,
                "ocrasuite": ocrasuite,
            }

            response = self.make_admin_request("init", params=parameters)
            assert '"value": true' in response, response

            for count in range(3):
                log.error("fetching challenge %d for %s ", count, ocrasuite)
                # -2- fetch the challenge
                p = {
                    "serial": serial,
                    # "user": 'root',
                    "data": "0105037311 Konto 50150850 BLZ 1752,03 Eur",
                }

                response = self.make_validate_request("check_s", params=p)
                assert '"value": false' in response, response

                # -3.a- calculate the otp response from the challenge
                jresp = json.loads(response.body)
                assert "detail" in jresp, response.body
                challenge = str(jresp.get("detail", {}).get("challenge"))
                transid = str(jresp.get("detail", {}).get("transactionid"))

                ocra = OcraSuite(ocrasuite)

                param = {}
                param["C"] = count
                param["Q"] = challenge
                param["P"] = ocrapin
                param["S"] = ""
                if ocra.T is not None:
                    # Default value for G is 1M, i.e., time-step size is one
                    # minute and the T represents the number of minutes since
                    # epoch time [UT].
                    now = datetime.utcnow()
                    stime = now.strftime("%s")
                    itime = int(stime)
                    param["T"] = itime

                ocra = OcraSuite(ocrasuite)
                data = ocra.combineData(**param)
                otp = ocra.compute(data, bkey)

                # -3.b- verify the otp value
                parameters = {
                    # "serial": serial,
                    "user": "root",
                    "pass": "pin" + otp,
                }
                response = self.make_validate_request("check", params=parameters)
                assert '"value": true' in response, f"{ocrasuite} {count} \n {response}"

                # -4- check the transaction status
                #
                # https://linotpserver/ocra/checkstatus
                #                                 ?transactionid=TRANSACTIONID
                # https://linotpserver/ocra/checkstatus?serial=SERIENNUMMER
                # https://linotpserver/ocra/checkstatus?user=BENUTZER

                parameters = {"transactionid": transid + "1"}
                response = self.make_admin_request("checkstatus", params=parameters)
                assert '"status": true' in response, response

                parameters = {"transactionid": transid}
                response = self.make_admin_request("checkstatus", params=parameters)
                assert '"status": true' in response, response

                parameters = {"serial": serial}
                response = self.make_admin_request("checkstatus", params=parameters)
                assert '"status": true' in response, response

                parameters = {"serial": "F" + serial}
                response = self.make_admin_request("checkstatus", params=parameters)
                assert '"status": true' in response, response

                parameters = {
                    "user": "roor",
                }
                response = self.make_admin_request("checkstatus", params=parameters)
                assert '"status": true' in response, response

                parameters = {"user": "root"}
                response = self.make_admin_request("checkstatus", params=parameters)
                assert '"status": true' in response, response

            # -1- create an ocra token
            parameters = {"serial": serial}
            response = self.make_admin_request("remove", params=parameters)
            assert '"value": 1' in response, response

    def test_OCRA_token_falseResponse(self):
        """
        test_OCRA_token_falseResponse: wrong response, new challenge - correct response - failcount == 0

        1. create an ocra token
        2. fetch the challange
        3. submit wrong response
        4. fetch new challange
        5. check status
        6.a. calculate the OTP response from the challenge
        6.b. submit the response
        7. check status

        @summary: this test is the first simple positive test, which uses
                  the serial number of the token, to identify the
                  transaction

        @todo:     more tests,
                - which uses the user who could have multiple tokens, but
                  only on QR-Token
                - check OCRA Token and TOTP tests
                - check OCRA with HOTP counter token
                - check OCRA Token with user pin
        """
        ocrasuite = "OCRA-1:HOTP-SHA256-8:QA64"
        serial = "QR_One2"
        for test in self.tests[2:3]:
            ocrasuite = test["ocrasuite"]
            key = test["keyh"]
            bkey = test["key"]
            ocrapin = "myocrapin"

            log.info("##################### %s", ocrasuite)

            # -1- create an ocra token
            parameters = {
                "serial": serial,
                "user": "root",
                "pin": "pin",
                "description": "first QRToken",
                "type": "ocra2",
                "ocrapin": ocrapin,
                "otpkey": key,
                "ocrasuite": ocrasuite,
            }

            response = self.make_admin_request("init", params=parameters)
            assert '"value": true' in response, response

            for count in range(3):
                # -2- fetch the challenge
                p = {
                    "serial": serial,
                    "data": "0105037311 Konto 50150850 BLZ 1752,03 Eur",
                }
                response = self.make_validate_request("check_s", params=p)
                assert '"value": false' in response, response

                # -3.a- calculate the otp response from the challenge
                jresp = json.loads(response.body)
                assert "detail" in jresp, response.body
                challenge = str(jresp.get("detail", {}).get("challenge"))
                transid = str(jresp.get("detail", {}).get("transactionid"))

                # -3- verify the wrong otp value
                parameters = {
                    "transactionid": transid,
                    "pass": "pinTest1234",
                }
                response = self.make_validate_request("check_t", params=parameters)
                assert '"value": false' in response, response

                # -4- check the transaction status
                parameters = {"transactionid": transid}
                response = self.make_admin_request("checkstatus", params=parameters)
                assert '"status": true' in response, response

                # -5- fetch a new challenge
                p = {
                    "serial": serial,
                    "data": "0105037311 Konto 50150850 BLZ 1752,03 Eur",
                }
                response = self.make_validate_request("check_s", params=p)
                assert '"value": false' in response, response

                # -6.a- calculate the otp response from the challenge
                jresp = json.loads(response.body)
                assert "detail" in jresp, response.body
                challenge = str(jresp.get("detail", {}).get("challenge"))
                transid = str(jresp.get("detail", {}).get("transactionid"))

                ocra = OcraSuite(ocrasuite)

                param = {}
                param["C"] = count
                param["Q"] = challenge
                param["P"] = ocrapin
                param["S"] = ""

                if ocra.T is not None:
                    # Default value for G is 1M, i.e., time-step size is one
                    # minute and the T represents the number of minutes since
                    # epoch time [UT].
                    now = datetime.utcnow()
                    stime = now.strftime("%s")
                    itime = int(stime)
                    param["T"] = itime

                data = ocra.combineData(**param)
                otp = ocra.compute(data, bkey)

                # -6.b- verify the otp value
                parameters = {
                    "transactionid": transid,
                    "pass": "pin" + otp,
                }
                response = self.make_validate_request("check_t", params=parameters)
                assert '"value": true' in response, response

                # -7- check the transaction status
                parameters = {
                    "transactionid": transid,
                }
                response = self.make_admin_request("checkstatus", params=parameters)
                log.info("response %s\n", response)
                assert '"status": true' in response, response
                assert '"values": {}' in response, response

            # -remove the ocra token
            parameters = {"serial": serial}
            response = self.make_admin_request("remove", params=parameters)
            assert '"value": 1' in response, response

    def test_OCRA_token_failcounterInc(self):
        """
        test_OCRA_token_failcounterInc: failcounter increment

        1. create an ocra token
        2. fetch the challange
        3. submit wrong respnse
        3. submit wrong respnse
        5. check status and if fail counter has incremented

        """

        ocrasuite = "OCRA-1:HOTP-SHA256-8:QA64"
        for test in self.tests[3:4]:
            ocrasuite = test["ocrasuite"]
            key = test["keyh"]
            bkey = test["key"]
            ocrapin = "myocrapin"
            serial = "QR_One3"

            log.debug(" %r", bkey)

            ocra = OcraSuite(ocrasuite)
            pinlen = ocra.truncation
            # -1- create an ocra token
            parameters = {
                "serial": serial,
                "user": "root",
                "pin": "pin",
                "description": "first QRToken",
                "type": "ocra2",
                "ocrapin": ocrapin,
                "otpkey": key,
                "ocrasuite": ocrasuite,
            }

            response = self.make_admin_request("init", params=parameters)
            assert '"value": true' in response, response

            fcount = 0
            for _count in range(CHALLLENGE_RUNS):
                # -2- fetch the challenge
                p = {
                    "serial": serial,
                    "data": "0105037311 Konto 50150850 BLZ 1752,03 Eur",
                }
                response = self.make_validate_request("check_s", params=p)
                assert '"value": false' in response, response

                # -3.a- from the response get the challenge
                jresp = json.loads(response.body)
                assert "detail" in jresp, response.body
                challenge = str(jresp.get("detail", {}).get("challenge"))
                transid = str(jresp.get("detail", {}).get("transactionid"))

                log.debug(" %r", challenge)

                ppin = "pin" + "a" * pinlen

                # -3- verify the wrong otp value
                parameters = {
                    "transactionid": transid,
                    "pass": ppin,
                }
                response = self.make_validate_request("check_t", params=parameters)
                assert '"value": false' in response, response
                fcount += 1

                ppin = "pin" + "4" * pinlen

                # -4- verify the wrong otp value
                parameters = {
                    "transactionid": transid,
                    "pass": ppin,
                }
                response = self.make_validate_request("check_t", params=parameters)
                assert '"value": false' in response, response
                fcount += 1

                # -5- check if the failcounter has incremented
                parameters = {
                    "transactionid": transid,
                }
                response = self.make_admin_request("checkstatus", params=parameters)

                assert '"status": true' in response, response
                assstring = f'"LinOtp.FailCount": {fcount},'
                assert assstring in response, response

            # -remove the ocra token
            parameters = {"serial": serial}
            response = self.make_admin_request("remove", params=parameters)
            assert '"value": 1' in response, response

    def test_OCRA_token_multipleChallenges(self):
        """
        test_OCRA_token_falseResponse: multiple open challenges

        1. create an ocra2 token
        2. fetch a challange1
        3. fetch another challange2
        3. submit right response for challenge 1
        3. submit right response for challenge 2
        5. check status

        """
        ocrasuite = "OCRA-1:HOTP-SHA256-8:QA64"
        for test in self.tests[0:1]:
            ocrasuite = test["ocrasuite"]
            log.info("################# OCRASUITE: %s", ocrasuite)
            key = test["keyh"]
            bkey = test["key"]
            ocrapin = "myocrapin"
            serial = "QR_One4"

            # -1- create an ocra token
            parameters = {
                "serial": serial,
                "user": "root",
                "pin": "pin",
                "description": "first QRToken",
                "type": "ocra2",
                "ocrapin": ocrapin,
                "otpkey": key,
                "ocrasuite": ocrasuite,
            }

            response = self.make_admin_request("init", params=parameters)
            assert '"value": true' in response, response

            for count in range(CHALLLENGE_RUNS):
                # -2a- fetch the challenge
                p = {
                    "serial": serial,
                    "data": "0105037311 Konto 50150850 BLZ 1752,03 Eur",
                }
                response = self.make_validate_request("check_s", params=p)
                assert '"value": false' in response, response

                # -2b- from the response get the challenge
                jresp = json.loads(response.body)
                assert "detail" in jresp, response.body
                challenge1 = str(jresp.get("detail", {}).get("challenge"))
                transid1 = str(jresp.get("detail", {}).get("transactionid"))

                ocra = OcraSuite(ocrasuite)

                param = {}
                param["C"] = count * 2
                param["Q"] = challenge1
                param["P"] = ocrapin
                param["S"] = ""

                if ocra.T is not None:
                    # Default value for G is 1M, i.e., time-step size is one
                    # minute and the T represents the number of minutes since
                    # epoch time [UT].
                    now = datetime.utcnow()
                    stime = now.strftime("%s")
                    itime = int(stime)
                    param["T"] = itime

                data = ocra.combineData(**param)
                otp1 = ocra.compute(data, bkey)

                # -3a- fetch the challenge
                p = {
                    "serial": serial,
                    "data": "0105037311 Konto 50150850 BLZ 234,56 Eur",
                }
                response = self.make_validate_request("check_s", params=p)
                assert '"value": false' in response, response

                # -3b- from the response get the challenge
                jresp = json.loads(response.body)
                assert "detail" in jresp, response.body
                challenge2 = str(jresp.get("detail", {}).get("challenge"))
                transid2 = str(jresp.get("detail", {}).get("transactionid"))

                ocra = OcraSuite(ocrasuite)

                param = {}
                param["C"] = (count * 2) + 1
                param["Q"] = challenge2
                param["P"] = ocrapin
                param["S"] = ""

                if ocra.T is not None:
                    # Default value for G is 1M, i.e., time-step size is one
                    # minute and the T represents the number of minutes since
                    # epoch time [UT].
                    now = datetime.utcnow()
                    stime = now.strftime("%s")
                    itime = int(stime)
                    param["T"] = itime

                data = ocra.combineData(**param)
                otp2 = ocra.compute(data, bkey)

                # -4- verify the first otp value
                parameters = {
                    "transactionid": transid1,
                    "pass": "pin" + otp1,
                }
                response = self.make_validate_request("check_t", params=parameters)
                assert '"value": true' in response, response

                # -5- verify the second otp value
                parameters = {
                    "transactionid": transid2,
                    "pass": "pin" + otp2,
                }
                response = self.make_validate_request("check_t", params=parameters)

                assert '"value": true' in response, response

                # -5- check if the failcounter has incremented
                parameters = {"serial": serial}

                response = self.make_admin_request("checkstatus", params=parameters)
                assert '"status": true' in response, response

            # -remove the ocra token
            parameters = {"serial": serial}
            response = self.make_admin_request("remove", params=parameters)
            assert '"value": 1' in response, response

    def test_OCRA_token_multipleChallenges2(self):
        """
        test_OCRA_token_multipleChallenges2: multiple open challenges  - now unordered

        1. create an ocra token
        2. fetch a challange1
        3. fetch aother challange2
        3. submit right respnse for challenge 1
        3. submit right respnse for challenge 2
        5. check status

        """
        ocrasuite = "OCRA-1:HOTP-SHA256-8:QA64"
        for test in self.tests[2:3]:
            ocrasuite = test["ocrasuite"]
            key = test["keyh"]
            bkey = test["key"]
            ocrapin = "myocrapin"
            serial = "QR_One4"

            # -1- create an ocra token
            parameters = {
                "serial": serial,
                "user": "root",
                "pin": "pin",
                "description": "first QRToken",
                "type": "ocra2",
                "ocrapin": ocrapin,
                "otpkey": key,
                "ocrasuite": ocrasuite,
            }

            response = self.make_admin_request("init", params=parameters)
            assert '"value": true' in response, response

            for count in range(CHALLLENGE_RUNS):
                # -2a- fetch the challenge
                p = {
                    "serial": serial,
                    "data": "0105037311 Konto 50150850 BLZ 1752,03 Eur",
                }
                response = self.make_validate_request("check_s", params=p)
                assert '"value": false' in response, response

                # -2b- from the response get the challenge
                jresp = json.loads(response.body)
                assert "detail" in jresp, response.body
                challenge1 = str(jresp.get("detail", {}).get("challenge"))
                transid1 = str(jresp.get("detail", {}).get("transactionid"))

                ocra = OcraSuite(ocrasuite)

                param = {}
                param["C"] = count * 2
                param["Q"] = challenge1
                param["P"] = ocrapin
                param["S"] = ""

                if ocra.T is not None:
                    # Default value for G is 1M, i.e., time-step size is one
                    # minute and the T represents the number of minutes since
                    # epoch time [UT].
                    now = datetime.utcnow()
                    stime = now.strftime("%s")
                    itime = int(stime)
                    param["T"] = itime

                data = ocra.combineData(**param)
                otp1 = ocra.compute(data, bkey)

                # -3a- fetch the challenge
                p = {
                    "serial": serial,
                    "data": "0105037311 Konto 50150850 BLZ 234,56 Eur",
                }
                response = self.make_validate_request("check_s", params=p)
                assert '"value": false' in response, response

                # -3b- from the response get the challenge
                jresp = json.loads(response.body)
                assert "detail" in jresp, response.body
                challenge2 = str(jresp.get("detail", {}).get("challenge"))
                transid2 = str(jresp.get("detail", {}).get("transactionid"))

                ocra = OcraSuite(ocrasuite)

                param = {}
                param["C"] = (count * 2) + 1
                param["Q"] = challenge2
                param["P"] = ocrapin
                param["S"] = ""

                if ocra.T is not None:
                    # Default value for G is 1M, i.e., time-step size is one
                    # minute and the T represents the number of minutes since
                    # epoch time [UT].
                    now = datetime.utcnow()
                    stime = now.strftime("%s")
                    itime = int(stime)
                    param["T"] = itime

                data = ocra.combineData(**param)
                otp2 = ocra.compute(data, bkey)

                # -4- verify the first otp value
                parameters = {
                    "transactionid": transid2,
                    "pass": "pin" + otp2,
                }
                response = self.make_validate_request("check_t", params=parameters)
                assert '"value": true' in response, response

                # with the former valid check all prevoius challenges are
                # deleted
                # -5- verify the second otp value
                parameters = {
                    "transactionid": transid1,
                    "pass": "pin" + otp1,
                }
                response = self.make_validate_request("check_t", params=parameters)
                assert '"value": false' in response, response

                # -5- check if the failcounter has incremented
                parameters = {"serial": serial}

                response = self.make_admin_request("checkstatus", params=parameters)
                assert '"status": true' in response, response

            # -remove the ocra token
            parameters = {"serial": serial}
            response = self.make_admin_request("remove", params=parameters)

            assert '"value": 1' in response, response

    def _getChallenge(
        self,
        ocrasuite,
        bkey,
        serial,
        ocrapin="",
        data=None,
        count=0,
        ttime=None,
    ):
        p = {
            "serial": serial,
            "challenge": f"0105037311 Konto 50150850 BLZ 1752,03 Eur {count}",
        }
        if data is not None:
            p["data"] = data

        # we need to create a challenge with input challenge parameter
        response = self.make_validate_request("check_s", params=p)

        assert '"value": false' in response, response

        # -2b- from the response get the challenge
        jresp = json.loads(response.body)
        assert "detail" in jresp, response.body
        challenge1 = jresp.get("detail", {}).get("challenge")
        transid1 = jresp.get("detail", {}).get("transactionid")

        now = datetime.utcnow()
        if ttime is not None:
            now = ttime
        stime = now.strftime("%s")
        itime = int(stime)

        param = {}
        param["C"] = count
        param["Q"] = challenge1
        param["P"] = ocrapin
        param["S"] = ""
        param["T"] = itime

        ocra = OcraSuite(ocrasuite)
        data = ocra.combineData(**param)
        otp1 = ocra.compute(data, bkey)

        return (otp1, transid1, challenge1)

    def get_challenge(self, serial, user=None, challenge_data="", params=None):
        p = {}
        if params:
            p.update(params)

        p["data"] = challenge_data
        if user is None:
            p["serial"] = serial
        else:
            p["user"] = user

        response = self.make_validate_request("check_s", params=p)

        return self.exctract_challenge(response)

    def exctract_challenge(self, response):
        try:
            jresp = json.loads(response.body)
            assert "detail" in jresp, response.body
            challenge = str(jresp.get("detail", {}).get("challenge"))
            transid = str(jresp.get("detail", {}).get("transactionid"))
        except Exception as e:
            challenge = None
            transid = None
            log.debug(" %r", e)

        return (response, challenge, transid)

    def test_OCRA_resync_Counter(self):
        """
        test_OCRA_resync_Counter: resync a counter based token

        (+)  create an ocra token
        (+)  fetch a challange1 for counter 20
        (+)  fetch aother challange2 for counter 21
        (+)  resync with otp1 + otp2
        (+)  check status
        """

        ttv = {
            "ocrasuite": "OCRA-1:HOTP-SHA512-8:C-QN08",
            "key": self.key64,
            "keyh": self.key64h,
        }
        ocrasuite = ttv.get("ocrasuite")
        key = ttv.get("keyh")
        bkey = ttv.get("key")
        ocrapin = "myocrapin"
        serial = "OCRA-resync"

        # -1- create an ocra token
        parameters = {
            "serial": serial,
            "user": "root",
            "pin": "pin",
            "description": serial,
            "type": "ocra2",
            "ocrapin": ocrapin,
            "otpkey": key,
            "ocrasuite": ocrasuite,
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        (otp1, _transid1, _challenge1) = self._getChallenge(
            ocrasuite, bkey, serial, ocrapin=ocrapin, count=19
        )

        # verify the token fail
        parameters = {"user": "root", "pass": "pin" + otp1}
        response = self.make_validate_request("check", params=parameters)

        assert '"value": false' in response, response

        (otp1, _transid1, _challenge1) = self._getChallenge(
            ocrasuite, bkey, serial, ocrapin=ocrapin, count=20
        )
        (otp2, _transid2, _challenge2) = self._getChallenge(
            ocrasuite, bkey, serial, ocrapin=ocrapin, count=21
        )

        # test resync of token 2
        parameters = {"user": "root", "otp1": otp1, "otp2": otp2}
        response = self.make_admin_request("resync", params=parameters)

        assert '"value": true' in response, response

        (otp1, transid1, _challenge1) = self._getChallenge(
            ocrasuite, bkey, serial, ocrapin=ocrapin, count=22
        )

        # verify the token works
        parameters = {"transactionid": transid1, "pass": "pin" + otp1}
        response = self.make_validate_request("check_t", params=parameters)

        assert '"value": true' in response, response

        for i in range(1, 3):
            (otp1, transid1, _challenge1) = self._getChallenge(
                ocrasuite, bkey, serial, ocrapin=ocrapin, count=22 + i
            )

        # check if the failcounter has incremented
        parameters = {"serial": serial}
        response = self.make_admin_request("checkstatus", params=parameters)

        assert '"status": true' in response, response

        # -remove the ocra token
        parameters = {"serial": serial}
        response = self.make_admin_request("remove", params=parameters)

        assert '"value": 1' in response, response

    @pytest.mark.xfail(reason="Currently not working in CI")
    def test_OCRA_autosync_Time(self):
        """
        test_OCRA_autosync_Time: resync a time based token

        (+)  create an ocra token
        (+)  fetch challange1 for time + timedelta (20 Min)
        (+)  fetch challange2 for time + timedelta (21 Min)
        (+)  check status

        """

        ttv = {
            "ocrasuite": "OCRA-1:HOTP-SHA512-8:QN08-T1M",
            "key": self.key64,
            "keyh": self.key64h,
        }

        ocrasuite = ttv.get("ocrasuite")
        key = ttv.get("keyh")
        bkey = ttv.get("key")
        ocrapin = "myocrapin"
        serial = "OCRA-resync"

        # -1- create an ocra token
        parameters = {
            "serial": serial,
            "user": "root",
            "pin": "pin",
            "description": serial,
            "type": "ocra2",
            "ocrapin": ocrapin,
            "otpkey": key,
            "ocrasuite": ocrasuite,
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        # switch on autoresync
        parameters = {"AutoResync": "true"}
        response = self.make_system_request("setConfig", params=parameters)

        now = datetime.utcnow()
        time1 = now + timedelta(minutes=20)
        (otp1, _transid1, _challenge1) = self._getChallenge(
            ocrasuite, bkey, serial, ocrapin=ocrapin, ttime=time1, data="Test2"
        )

        # verify the token fail
        parameters = {"user": "root", "pass": "pin" + otp1}
        response = self.make_validate_request("check", params=parameters)

        assert '"value": false' in response, response

        time2 = now + timedelta(minutes=21)
        (otp2, _transid1, _challenge1) = self._getChallenge(
            ocrasuite, bkey, serial, ocrapin=ocrapin, ttime=time2, data="Test2"
        )

        # verify the token successfuly has synced
        parameters = {"user": "root", "pass": "pin" + otp2}
        response = self.make_validate_request("check", params=parameters)

        assert '"value": true' in response, response

        # -remove the ocra token
        parameters = {"serial": serial}
        response = self.make_admin_request("remove", params=parameters)

        assert '"value": 1' in response, response

        # switch off autoresync
        parameters = {"key": "AutoResync"}
        response = self.make_system_request("delConfig", params=parameters)

    @pytest.mark.xfail(reason="Currently not working in CI")
    def test_OCRA_resync_Time(self):
        """
        test_OCRA_resync_Time: resync a time based token

        (+)  create an ocra token
        (+)  fetch challange1 for time + timedelta (20 Min)
        (+)  fetch challange2 for time + timedelta (21 Min)
        (+)  resync with otp1 + otp2
        (+)  check status

        """

        ttv = {
            "ocrasuite": "OCRA-1:HOTP-SHA512-8:QN08-T1M",
            "key": self.key64,
            "keyh": self.key64h,
        }

        ocrasuite = ttv.get("ocrasuite")
        key = ttv.get("keyh")
        bkey = ttv.get("key")
        ocrapin = "myocrapin"
        serial = "OCRA-resync"

        # -1- create an ocra token
        parameters = {
            "serial": serial,
            "user": "root",
            "pin": "pin",
            "description": serial,
            "type": "ocra2",
            "ocrapin": ocrapin,
            "otpkey": key,
            "ocrasuite": ocrasuite,
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        time1 = datetime.utcnow() + timedelta(minutes=20)
        (otp1, _transid1, _chall1) = self._getChallenge(
            ocrasuite, bkey, serial, ocrapin=ocrapin, ttime=time1
        )

        # verify the token fail
        parameters = {"user": "root", "pass": "pin" + otp1}
        response = self.make_validate_request("check", params=parameters)

        assert '"value": false' in response, response

        time1 = datetime.utcnow() + timedelta(minutes=21)
        (otp1, _transid1, _chall1) = self._getChallenge(
            ocrasuite, bkey, serial, ocrapin=ocrapin, ttime=time1
        )
        time1 = datetime.utcnow() + timedelta(minutes=22)
        (otp2, _transid2, _chall2) = self._getChallenge(
            ocrasuite, bkey, serial, ocrapin=ocrapin, ttime=time1
        )

        # test resync of token 2
        parameters = {"user": "root", "otp1": otp1, "otp2": otp2}
        response = self.make_admin_request("resync", params=parameters)

        assert '"value": true' in response, response

        time3 = datetime.utcnow() + timedelta(minutes=23)
        (otp3, transid1, _chall1) = self._getChallenge(
            ocrasuite, bkey, serial, ocrapin=ocrapin, ttime=time3
        )

        # verify the token works
        parameters = {"transactionid": transid1, "pass": "pin" + otp3}
        response = self.make_validate_request("check_t", params=parameters)

        assert '"value": true' in response, response

        # check if the failcounter has incremented
        parameters = {"serial": serial}
        response = self.make_admin_request("checkstatus", params=parameters)

        assert '"status": true' in response, response

        # -remove the ocra token
        parameters = {"serial": serial}
        response = self.make_admin_request("remove", params=parameters)

        assert '"value": 1' in response, response

    def test_kdpf2(self):
        """
        test_kdpf2: test the key generation

        kannst Du die funktion mal mit folgendem laufen lassen:

        Initialer Key: "WeakPW123"
        Iterationen: 10000
        Hash-Algo: SHA256

        Und vielleicht zur Sicherheit nochmal dasselbe mit initialem Key
        "SchwachesPW4711".
        """
        try:
            key = "weakpw"
            salt = binascii.unhexlify("01020304")
            Ergebniskeylaenge = 32
            Iterationen = 10000

            keyStream = PBKDF2(key, salt, iterations=Iterationen, digestmodule=SHA256)
            key = keyStream.read(Ergebniskeylaenge)

            res = binascii.hexlify(key)
            log.debug("%r", res)

            st = "abcdefg"
            ret = check(st)

            ret = createActivationCode(st)
            # st = os.urandom(12)
            summ = 0
            arry = bytearray(st)
            for x in arry:
                summ = summ ^ x
            ret = hex(summ % 255).upper()
            res = ret[-2:0]

        except Exception as e:
            log.debug("%r", e)

    def test_ERROR_771_(self):
        """
        test_ERROR_771_: #771 : OCRA Rollout: No attribute addToSession
        """

        # -1- create an ocra token
        parameters = {
            "user": "root",
            "type": "ocra2",
            "genkey": "1",
            "sharedsecret": "1",
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        act = createActivationCode("abcdefg")
        # -2- acivate ocra token
        parameters = {
            "user": "root",
            "type": "ocra2",
            "activationcode": act,
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        act = createActivationCode()
        # -2- acivate ocra token
        parameters = {
            "user": "root",
            "type": "ocra2",
            "activationcode": act,
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

    def test_ERROR_770_(self):
        """
        test_ERROR_770_: #770: OCRA Rollout without user

            ocra rollout w.o. user but with serial must not fail
        """
        # -1- create an ocra token
        parameters = {
            "type": "ocra2",
            "genkey": "1",
            "sharedsecret": "1",
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        # on the return we get the shared secret
        jresp = json.loads(response.body)
        assert "detail" in jresp, response.body
        app_import = str(jresp.get("detail", {}).get("app_import"))
        secret = str(jresp.get("detail", {}).get("sharedsecret"))
        serial = str(jresp.get("detail", {}).get("serial"))

        # now parse the appurl for the ocrasuite
        uri = urlparse(app_import.replace("lseqr://", "http://"))
        qs = uri.query
        qdict = parse_qs(qs)

        ocrasuite = qdict.get("os", None)
        if ocrasuite is not None and len(ocrasuite) > 0:
            ocrasuite = ocrasuite[0]

        act = "4XQRSVTKUNH7ETQYTVNXKWFUB4EZ4NC3C1"
        # -2- acivate ocra token
        parameters = {
            "type": "ocra2",
            "activationcode": act,
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"message": "no token found for user:' in response, response

        act = "4XQRSVTKUNH7ETQYTVNXKWFUB4EZ4NC3C1"
        # -2- acivate ocra token
        parameters = {
            "type": "ocra2",
            "serial": serial,
            "activationcode": act,
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response

        # -3.a- we got on the return side a transactionId and a challenge
        jresp = json.loads(response.body)
        assert "detail" in jresp, response.body
        _nonce = str(jresp.get("detail", {}).get("nonce"))
        transid = str(jresp.get("detail", {}).get("transactionid"))
        app_import = str(jresp.get("detail", {}).get("app_import"))

        # now parse the appurl for the ocrasuite
        uri = urlparse(app_import.replace("lseqr://", "http://"))
        qs = uri.query
        qdict = parse_qs(qs)
        nonce = qdict.get("no", None)
        if nonce is not None and len(nonce) > 0:
            nonce = nonce[0]

        challenge = qdict.get("ch", None)
        if challenge is not None and len(challenge) > 0:
            challenge = challenge[0]

        # now we have all in place for the key derivation to create the new key
        #   sharedsecret, activationcode and nonce
        key_len = 20
        if ocrasuite.find("-SHA256"):
            key_len = 32
        elif ocrasuite.find("-SHA512"):
            key_len = 64

        bkey = kdf2(secret, nonce, act, len=key_len)

        ocra = OcraSuite(ocrasuite)

        param = {}
        param["C"] = 0
        param["Q"] = challenge
        param["P"] = ""
        param["S"] = ""
        if ocra.T is not None:
            # Default value for G is 1M, i.e., time-step size is one minute and
            # theT represents the number of minutes since epoch time [UT].
            now = datetime.utcnow()
            stime = now.strftime("%s")
            itime = int(stime)
            param["T"] = itime

        data = ocra.combineData(**param)
        otp = ocra.compute(data, bkey)

        # -3.a- verify the otp value to finish the rollout
        parameters = {"transactionid": transid, "pass": otp}
        response = self.make_validate_request("check_t", params=parameters)

        assert '"value": true' in response, response

        # -remove the ocra token
        parameters = {
            "serial": serial,
        }
        response = self.make_admin_request("remove", params=parameters)

        assert '"value": 1' in response, response

    def test_wrong_transid(self):
        """
        test_sign_data: test with wrong transaction id
        """

        ocra = OcraOtp()
        response1 = self.init_0_QR_Token(
            user="root", ocrapin=None, pin=None, description=None
        )
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="TestTTT", serial=None, pin=None, ocrapin=None
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)
        counter = 0
        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1
        transidFail = int(transid) + 1

        _response = self.check_otp(transidFail, otp)

        _response = self.check_otp(transid, otp)

        (_response, challenge, transid) = self.get_challenge(ocra.serial)
        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        response = self.check_otp(transid, otp)
        log.debug(response)

        self.removeTokens(serial=ocra.serial)

    def test_genkey_w_users_fail(self):
        """
            test_genkey_w_users_fail: genkey with users

            admin/init?type=ocra&genkey=1&sharedsecret=1&user=7654321
                                  &session=41e1534d96df272de08b05d0ce83504fedf
                                  384c9c8a9d29a0db6c831f5d0eae4
            LinOTP-Response:
                > {
                >    "detail": {
                     "googleurl": {
                       "description": "URL for google Authenticator",
                       "value": "otpauth://ocra/LSOC00000001?secret=5F5BR2FO4F
                                   353EB7GWD2XIVQ3CJGYAZVRQQAWKTNTUHGBNGEXTWA
                                   &counter=0"
                 },
                 "oathurl": {
                "description": "URL for OATH token",
                 "value": "oathtoken:///addToken?name=LSOC00000001&lockdown=
                             true&key=e97a18e8aee177dd903f3587aba2b0d8926c03358
                             c200b2a6d9d0e60b4c4bcec"
                   },
                "app_import": "lseqr://init?sh=e97a18e8aee177dd903f3587aba2b0d
                                            8926c03358c200b2a6d9d0e60b4c4bcec
                                            &os=OCRA-1:HOTP-SHA256-6:C-QA64
                                            &se=LSOC00000001",
                "serial": "LSOC00000001",
                       "otpkey": {
                    "description": "OTP seed",
                      "value": "seed://e97a18e8aee177dd903f3587aba2b0d8926c0335
                                          8c200b2a6d9d0e60b4c4bcec"
                },
                "sharedsecret": "e97a18e8aee177dd903f3587aba2b0d8926c03358c20
                                    0b2a6d9d0e60b4c4bcec"

            admin/init?type=ocra&genkey=1&activationcode=6A3EG7JFIDWDSZX2UGXY
                            UUXTKQAHI2PK52&user=7654321&message=TestTTT
                            & session=51355c5ef23a47eaf0900dfe121d19cb7a1ebb
                            e4d14c1bb2746a84c23902d3f4



                LOCK TABLES `Token` WRITE;
                /*!40000 ALTER TABLE `Token` DISABLE KEYS */;
                INSERT INTO `Token` VALUES (14,'','LSOC00000001',
                'ocra2',
                '{\n\"rollout\": \"1\", \n\
                "ocrasuite\": \"OCRA-1:HOTP-SHA256-6:C-QA64\", \n\
                "sharedSecret\": \"d00bd597def1cc5d604b0b713d6ab72f:91b798d248
                                    bdd4f33a0b611526c351183020a046dafc08c02c0f
                                    947ac7fe0ad190641da50c668047bec9b6dc94ec75
                                    d80e30a56ed5feb8102aebb485d452c7e649de6e7f
                                    e79f233ce364a8ebe82fa4bb0cc5650ec058f13af4
                                    08cd81876750f95ee68b506de6637754ec7d3e801b
                                    d91a1265bfae69288e51570494f69a7873640bdc36
                                    1f313b3fecbbf99622e77f3a54\"\n
                }',
                '','','','','SQLIdResolver.IdResolver.mysql_test',
                'useridresolver.SQLIdResolver.IdResolver.mysql_test',
                '7654321','',6,'',
                '3e91ba46406db210dbce91395026ce56c187760fee68189f67f996ff3b57
                cd19a39dbc330fa738a41bfd3308358a81e3403a62b597358f2a9bb33db95
                9a814f5ec5726279210c75af8ba054eecfa92f61668df2098bdafede1a8ce
                f78238b586b7c9a1aec66a0bb65948046f2c23d92c72c1b1581393cf21aee
                c53c90ea3255ac21e63777b0e72902cf5d4f025da6569',
                '649364d85dfa899057ceea99ec1d9d13',10,0,0,0,10,1000);
                /*!40000 ALTER TABLE `Token` ENABLE KEYS */;
                UNLOCK TABLES;
        """
        ocra = OcraOtp()
        counter = 0
        response1 = self.init_0_QR_Token(
            user="7654321", ocrapin=None, pin=None, description=None
        )
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="7654321",
            message="TestTTT",
            serial=None,
            pin=None,
            ocrapin=None,
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)
        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        response = self.check_otp(transid, otp)
        log.debug(response)

        self.removeTokens(serial=ocra.serial)

    def test_short_message_rollout(self):
        """
        test_short_message_rollout: rollout w short message
        """

        ocra = OcraOtp()
        counter = 0
        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="TestTTT"
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)
        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1
        _response = self.check_otp(transid, otp)

        (_response, challenge, transid) = self.get_challenge(ocra.serial)
        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        response = self.check_otp(transid, otp)
        log.debug(response)

        self.removeTokens(serial=ocra.serial)

    def test_broken_enrollment_activation(self):
        """
        test_broken_enrollment_activation: test with failure in
                                                        activation code

        0. init 0
        1. complete initialization with failure in activation code
        1a. init 1 with defekt activation code  - will fail
        1b. init 1 with correct activation code - will work
                                                (how many retries)


        2 test error with first otp
        2a. 2x reply to challenge with wrong otp
        2b. reply to challenge with correct otp

        3. std otp check - only one attempt for one challenge
        3a. get challenge
        3b. wrong otp
        3c. correct otp - must fail


        """
        ocra = OcraOtp()
        counter = 0
        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="meine Ueberweisung 123"
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        _response = self.check_otp(transid, otp)

        (_response, challenge, transid) = self.get_challenge(ocra.serial)
        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        response = self.check_otp(transid, otp)
        log.debug(response)

        self.removeTokens(serial=ocra.serial)

    def test_QR_rollout_w_3_fails(self):
        """
        test_QR_rollout_w_3_fails: rollout a QRToken with 3 fails for OTP and re-rollout

        """
        ocra = OcraOtp()
        counter = 0
        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="TestTTT"
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        # get the correct otp
        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        wrongOtp = self.randOTP(otp)
        response = self.check_otp(transid, wrongOtp)
        assert '"value": false' in response, response

        wrongOtp = self.randOTP(otp)
        response = self.check_otp(transid, wrongOtp)
        assert '"value": false' in response, response

        wrongOtp = self.randOTP(otp)
        response = self.check_otp(transid, wrongOtp)
        assert '"value": false' in response, response

        # after "OcraMaxChallengeRequests", '3' failde auth requests
        # the token is reset to rollout=1 status, which means you have
        # to restart the rollout
        response = self.check_otp(transid, otp)

        # due to fixes on security leakeage prevention the response changes
        # and does not contain the following text anymore:
        # "validate/check_t failed: unable to complete the rollout"
        # instead  only a False value
        assert '"value": false' in response, response

        # re-enroll token
        ocra.init_1(response1)
        counter = 0
        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="TestTTT"
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        # get the correct otp
        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        response = self.check_otp(transid, otp)

        assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)

    def test_QR_rollout_w_long_message(self):
        """
        test_QR_rollout_w_long_message: rollout a QRToken with
                    long rollout messages

        remarks: mysql silently truncates the data and no reply
                is shown to the user!!! see ticket #12324
        """

        sqlconnect = self.app.config.get("DATABASE_URI")
        if sqlconnect.startswith("mysql"):
            self.skipTest("MySQL silently truncates data. See #12324.")

        ocra = OcraOtp()
        counter = 0
        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        ms = (
            "This is a very long message text, "
            "which should be used as the data "
            "for the challenge01234567890" * 5
        )

        (response2, _activationkey) = self.init_1_QR_Token(user="root", message=ms)
        assert response2.json["result"]["value"], response2

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message=ms[0:100]
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        # get the correct otp
        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        wrongOtp = self.randOTP(otp)
        response = self.check_otp(transid, wrongOtp)
        assert '"value": false' in response, response

        wrongOtp = self.randOTP(otp)
        response = self.check_otp(transid, wrongOtp)
        assert '"value": false' in response, response

        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # finally usage with other otp's check_t should support
        # max_check_challenge_retry == 3'''
        # normal check supports only one check !!!

        for _i in range(1, 3):
            (response, challenge, transid) = self.get_challenge(ocra.serial)
            otp = ocra.callcOtp(challenge, counter=counter)
            counter += 1

            response = self.check_otp(transid, otp)
            assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)

    def test_QR_rollout_w_2_retries(self):
        """
        test_QR_rollout_w_2_retries: rollout a QRToken with 2 fails for OTP before final rollout is done
        """
        ocra = OcraOtp()
        counter = 0

        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="TestTTT"
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        # get the correct otp
        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        wrongOtp = self.randOTP(otp)
        response = self.check_otp(transid, wrongOtp)
        assert '"value": false' in response, response

        wrongOtp = self.randOTP(otp)
        response = self.check_otp(transid, wrongOtp)
        assert '"value": false' in response, response

        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # finally usage with other otp's check_t should support
        # max_check_challenge_retry == 3'''
        # normal check supports only one check !!! '''

        for _i in range(1, 3):
            (response, challenge, transid) = self.get_challenge(ocra.serial)
            otp = ocra.callcOtp(challenge, counter=counter)
            counter += 1
            response = self.check_otp(transid, otp)
            assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)

    def test_QR_rollout_wrong_activation(self):
        """
        test_QR_rollout_wrong_activation: rollout a QRToken with 2 fails for OTP before final rollout is done
        """
        ocra = OcraOtp()
        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        activationkey = createActivationCode()

        wrongactivationkey = activationkey + "w"
        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="TestTTT", activationkey=wrongactivationkey
        )
        assert "Incorrect padding" in response2, response2

        wrongactivationkey = "w" + activationkey
        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="TestTTT", activationkey=wrongactivationkey
        )
        assert "Incorrect padding" in response2, response2

        activationkey = createActivationCode()
        while True:
            wrongactivationkey = self.randOTP(activationkey)
            checksum = check(wrongactivationkey.encode("utf-8"))
            if checksum != wrongactivationkey[-2:]:
                break

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="TestTTT", activationkey=wrongactivationkey
        )
        assert '"status": false' in response2, response2
        stat = (
            "Non-base32 digit found" in response2
            or "activation code checksum error" in response2
        )
        assert stat, response2

        activationkey = createActivationCode()
        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="TestTTT", activationkey=activationkey
        )
        assert "app_import" in response2, response2

        (challenge, transid) = ocra.init_2(response2, activationkey)

        # get the correct otp
        otp = ocra.callcOtp(challenge)

        wrongOtp = self.randOTP(otp)
        response = self.check_otp(transid, wrongOtp)
        assert '"value": false' in response, response

        wrongOtp = self.randOTP(otp)
        response = self.check_otp(transid, wrongOtp)
        assert '"value": false' in response, response

        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # finally usage with other otp's check_t should
        # support max_check_challenge_retry == 3
        # normal check supports only one check !!!

        # support challenge retry
        parameters = {"ocra2.max_check_challenge_retry": 3}
        response = self.make_system_request("setConfig", params=parameters)

        for i in range(1, 3):
            (response, challenge, transid) = self.get_challenge(ocra.serial)
            otp = ocra.callcOtp(challenge)
            response = self.check_otp(transid, otp)
            assert '"value": true' in response, f" count: {i} \n {response}"

        self.removeTokens(serial=ocra.serial)

    def test_QR_rollout_responses(self):
        """
        test_QR_rollout_responses: check the rollout responses
        """
        ocra = OcraOtp()
        counter = 0

        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="TestTTT"
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        # finish rollout
        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # get next challenge
        (response, challenge, transid) = self.get_challenge(ocra.serial)

        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        # wrong otp
        wrongOtp = self.randOTP(otp)
        response = self.check_otp(transid, wrongOtp)
        assert '"value": false' in response, response

        # wrong transaction id
        wrongtransid = str(int(transid) - 3)
        wrongOtp = self.randOTP(otp)
        response = self.check_otp(wrongtransid, otp)
        # due to information leakage prevention, this call does not return
        # anything valuable
        # assert wrongtransid in response, response
        # assert "No challenge for transaction" in response, response

        # correct response
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)

    def test_QR_rollout_w_new_challenge(self):
        """
        test_QR_rollout_w_new_challenge: check the rollout with new challenges instead of the one from the init
        """
        ocra = OcraOtp()
        counter = 0
        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="TestTTT"
        )
        (_challenge, _transid) = ocra.init_2(response2, activationkey)

        # finish rollout
        # otp = ocra.callcOtp(challenge)

        # response = self.check_otp(transid, otp)
        # assert '"result": true' in response, response

        # get next challenge
        (_response, challenge, transid) = self.get_challenge(ocra.serial)

        otp = ocra.callcOtp(challenge, counter=counter)
        counter += 1

        # correct response
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)

    def test_QRchallenge_w_umlaute(self):
        """
        test_QRchallenge_w_umlaute: check challenge with umlaute

        """
        ocra = OcraOtp()

        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="Täst äußerst wichtig!"
        )
        (_challenge, _transid) = ocra.init_2(response2, activationkey)

        # finish rollout
        # otp = ocra.callcOtp(challenge)

        # response = self.check_otp(transid, otp)
        # assert '"result": true' in response, response

        # get next challenge
        (_response, challenge, transid) = self.get_challenge(
            ocra.serial, challenge_data="Äns Zwö Drü"
        )
        otp = ocra.callcOtp(challenge)

        # correct response
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)

    def test_Activationcode_switch(self):
        """
        test_Activationcode_switch: switch char in activation code -results in same checksumm :-(
        """
        ocra2 = OcraOtp()
        response1 = self.init_0_QR_Token(user="root")
        ocra2.init_1(response1)

        activationkey1 = createActivationCode("1234567890")
        activationkey2 = createActivationCode("1234567809")

        (response2, _activationkey) = self.init_1_QR_Token(
            user="root",
            message="Täst äußerst wichtig!",
            activationkey=activationkey1,
        )
        (challenge, transid) = ocra2.init_2(response2, activationkey2)

        # finish rollout
        otp = ocra2.callcOtp(challenge)
        response = self.check_otp(transid, otp)
        assert '"value": false' in response, response

        ocra2.init_1(response1)
        (response2, _activationkey) = self.init_1_QR_Token(
            user="root",
            message="Täst äußerst wichtig!",
            activationkey=activationkey1,
        )
        (challenge, transid) = ocra2.init_2(response2, activationkey1)

        # finish rollout
        otp = ocra2.callcOtp(challenge)
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

    def test_QRchallenge_w_wrong_serial(self):
        """
            test_QRchallenge_w_wrong_serial: create two tokens and check the \
            responses of the requests with wrong serial or not defined user \
            or mutliple tokens
        """
        ocra2 = OcraOtp()
        response1 = self.init_0_QR_Token(user="root")
        ocra2.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="Täst äußerst wichtig!"
        )
        (challenge, transid) = ocra2.init_2(response2, activationkey)

        # finish rollout
        otp = ocra2.callcOtp(challenge, counter=0)
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # main working token
        ocra = OcraOtp()
        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="Täst äußerst wichtig!"
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        # finish rollout
        otp = ocra.callcOtp(challenge, counter=1)
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # support challenge retry
        parameters = {"ocra2.max_check_challenge_retry": 3}
        response = self.make_system_request("setConfig", params=parameters)

        # get next challenge
        (response, challenge, transid) = self.get_challenge(
            ocra.serial, challenge_data="Äns Zwö Drü"
        )
        otp = ocra.callcOtp(challenge, counter=2)

        # correct response
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # now test wrong serial number
        serial = "L" + ocra.serial
        (response, challenge, transid) = self.get_challenge(
            serial, challenge_data="Äns Zwö Drü"
        )
        # due to security fixes to prevent information leakage, there is no
        # more the text:
        #         'No token found: unable to create challenge for'
        assert '"value": false' in response, response

        # test for user with two tokens
        (response, challenge, transid) = self.get_challenge(
            serial, user="root", challenge_data="Äns Zwö Drü"
        )

        # due to security fixes to prevent information leakage, there is no
        # more the text:
        #         More than one token found'
        assert '"value": false' in response, response

        # now test wrong user
        (response, challenge, transid) = self.get_challenge(
            serial, user="rr", challenge_data="Äns Zwö Drü"
        )

        # due to security fixes to prevent information leakage, there is no
        # more the text:
        #         getUserId failed: no user >rr< found!
        assert '"value": false' in response, response

        # get next challenge
        (response, challenge, transid) = self.get_challenge(
            ocra.serial, challenge_data="Äns Zwö Drü"
        )
        otp = ocra.callcOtp(challenge, counter=3)

        # correct response
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # correct response
        response = self.check_otp(transid, otp)

        # due to security fixes to prevent information leakage, there is no
        # more the text:
        #         'No challenge for transaction'
        assert '"value": false' in response, response

        self.removeTokens(serial=ocra.serial)
        self.removeTokens(serial=ocra2.serial)

    def test_sign_data(self):
        """
        test_sign_data: test signing data with the ocra token
        """

        testsig = [
            {
                "ocrasuite": "OCRA-1:HOTP-SHA256-8:QA64",
                "key": "12345678901234567890",
                "vectors": [
                    {
                        "url": (
                            "lseqr://nonce?me=T%C3%B6st+%C3%A4u%C3%9Ferst+"
                            "wichtig%21&ch=Tstuerstwichtig0000KIFYjZzwSZfSA"
                            "MLdKxRIvLz8en6EiC9zqpfVrIwWyxDId&no=ca7c48c239"
                            "2f3c71f6a3ecfa22a482621c965db8223e928094b2c4a0"
                            "d3e9893f1d836bc9492fa2685ec2d1efc10b2be93682b9"
                            "fccb987e20bf06b34dd0fcae02&tr=690511961451&"
                            "u=http%253A%252F%252F127.0.0.1%252Focra%252Fcheck_t&"
                            "se=LSOC00000001"
                        ),
                        "signature": (
                            "c6403b5552a158324866d049d2cf7e5540029cca3"
                            "360556b200aa83fccc499e5"
                        ),
                    },
                    {
                        "url": (
                            "lseqr://nonce?me=TestTTT&ch=TestTTT0000UbYaOh9XiMYrn"
                            "fm5w6K9d2LNVXCLT5USvoCswXisGD4CsxFPAzsFB&no=5ef9b921"
                            "5412e439edcbe2f1bfbe782a2bad593e0610f7ca2227707e6527"
                            "7135bf31b1fea9abe62ba457975f6e038df0d71aa851cde838e2"
                            "1132bef731675dc1&tr=849623122426&u=http%253A%252F%25"
                            "2F127.0.0.1%252Focra%252Fcheck_t&se=LSOC00000001"
                        ),
                        "signature": (
                            "20a62643abd4298b8b4b23e153bc90a1a334e4a21869a"
                            "e177e730304457abd40"
                        ),
                    },
                    {
                        "url": (
                            "lseqr://req?me=None&u=http%253A%252F%252F127.0.0.1"
                            "%252Focra%252Fcheck_t&ch=None00004zpvxvBoytejPXuhP"
                            "4F6XnCKBhPyS5ZS40otN10YaMYX3zS0VRx2m351&"
                            "tr=299636729110"
                        ),
                        "signature": (
                            "88fe51ee80d103cd8e57b884ee293260f99fb5718713"
                            "ed0be0143a7a582cddc9"
                        ),
                    },
                    {
                        "url": (
                            "lseqr://nonce?me=TestTTT&ch=TestTTT0000tiprDFh7H8nsD"
                            "0gewFgJqRrQmtbHcwbzkqIXfN8YY9lEgYT328xdu&no=2b8d5dc5"
                            "0997ddd58f649eb1c8073613c40594294a31b2b4aad1ddf091e0"
                            "3c9884d6fe341a355ec50f1b80667b0eeae65dff99c90e8159d3"
                            "54c569bc77ae3a5b&tr=168896679193&"
                            "u=http%253A%252F%252F127.0.0.1%252Focra%252Fcheck_t&"
                            "se=LSOC00000001"
                        ),
                        "signature": (
                            "973ed993d8560cc3ebba143048fc0a1f6c53c2f8a32c"
                            "5717d700fdd750deacd2"
                        ),
                    },
                    {
                        "url": (
                            "lseqr://req?me=None&u=http%253A%252F%252F127.0.0.1%"
                            "252Focra%252Fcheck_t&ch=None0000ZtcoBT3HRaiMzLVm4cz"
                            "jvUE5mEmUdpPU0rPg6mWAmUYspF021G64GrIP&tr=396709068"
                            "48"
                        ),
                        "signature": (
                            "e4b5cc56170f366e475e1773e4f4830cd431011f34a57"
                            "99e90314936c31813fd"
                        ),
                    },
                ],
            },
        ]

        for test in testsig:
            ocra = OcraSuite(test["ocrasuite"])
            key = test.get("key").encode("utf-8")
            for v in test.get("vectors"):
                url = v.get("url").encode("utf-8")
                sig = v.get("signature").encode("utf-8")
                res = ocra.signData(url, key)
                assert res == sig, f"{res!r} != {sig!r}"

    def test_ocra_autosync_event(self):
        """
        Autosync and resync for OCRA token / event + timebased
        including syncwindow / timeshift parameters from TOTP
        """
        # main working token
        ocra = OcraOtp()
        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="Täst äußerst wichtig!"
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        # finish rollout
        otp = ocra.callcOtp(challenge)
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # no retry of a challenge
        parameters = {"ocra2.max_check_challenge_retry": 0}
        response = self.make_system_request("setConfig", params=parameters)

        # get next challenge
        (response, challenge, transid) = self.get_challenge(
            ocra.serial, challenge_data="Täst: auch äußerst wichtig"
        )
        otp = ocra.callcOtp(challenge, counter=ocra.counter + 1)

        # correct response
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)

    def test_ocra_challenge_check(self):
        """
        Test support for challenges in validate/check
        """
        ocra = OcraOtp()
        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="Täst äußerst wichtig"
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        # finish rollout
        otp = ocra.callcOtp(challenge)
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        challenge = "thisismychallenge123"
        cout = ocra.counter
        otp = ocra.callcOtp(challenge, counter=cout + 1)

        parameters = {
            "pass": "pin" + otp,
            "user": "root",
            "challenge": challenge,
        }

        response = self.make_validate_request("check", params=parameters)
        assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)

    def test_ocra_challenge_check_s(self):
        """
        Test support for challenges in validate/check_s on timebased ocra
        """
        ocrasuite = "OCRA-1:HOTP-SHA1-6:QN06-T1M"
        message = "783232123"
        serial = "QR2_123"

        ocra = OcraOtp()
        response1 = self.init_0_QR_Token(ocrasuite=ocrasuite, user=None, serial=serial)
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            ocrasuite=ocrasuite, serial=serial, message=message
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        # finish rollout
        otp = ocra.callcOtp(challenge)
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        challenge = "123456"
        cout = ocra.counter
        otp = ocra.callcOtp(challenge, counter=cout + 1)

        parameters = {
            "pass": "pin" + otp,
            "serial": serial,
            "challenge": challenge,
        }

        response = self.make_validate_request("check_s", params=parameters)
        assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)

    def test_serial_based_w_callbackid(self):
        """
        ocra2 token with check_s and check_t and callback_id as parameter
        with replacements for transactionis and serial number
        """
        ocrasuite = "OCRA-1:HOTP-SHA256-8:C-QA64"
        message = "Transaktion: Ausrollen eines OCRA2 Tokens"
        serial = "ExternalManagedOcraToken"

        pin = ""

        ocra = OcraOtp()

        self.setupPolicies()

        enroll_param = {
            "callback.id": "one",
            "callback.user": "hugo",
            "callback.password": "abracad:abra123",
        }
        response1 = self.init_0_QR_Token(
            serial=serial,
            pin=pin,
            realm="mydefrealm",
            params=enroll_param,
            ocrasuite=ocrasuite,
        )

        resp = json.loads(response1.body)
        curl = resp.get("detail", {}).get("url", "")

        # now check
        # was the callback.id used
        # and if the replacements went right
        assert "one" in curl, curl
        assert "ini" in curl, curl
        assert serial in curl, curl
        assert enroll_param["callback.user"] in curl, curl
        assert urllib.parse.quote(enroll_param["callback.password"]) in curl, curl

        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            serial=serial,
            pin=pin,
            message=message,
            realm="mydefrealm",
            params=enroll_param,
        )
        resp = json.loads(response2.body)
        transid = resp.get("detail", {}).get("transactionid", "")
        curl = resp.get("detail", {}).get("url", "")
        assert transid in curl, curl
        assert "one" in curl, curl
        assert "ini" not in curl, curl

        (challenge, transid) = ocra.init_2(response2, activationkey)

        """ finish rollout """
        otp = ocra.callcOtp(challenge)

        response = self.check_otp(transid, otp, pin=pin, params=enroll_param)

        assert '"value": true' in response, response

        for i in range(1, 5):
            message = f"Veränderung {i} am System durchgeführt! Bitte bestätigen!"

            if i == 3:
                enroll_param["no_callback"] = True

            if i == 4:
                del enroll_param["callback.id"]
                del enroll_param["no_callback"]

            (response, challenge, transid) = self.get_challenge(
                ocra.serial, challenge_data=message, params=enroll_param
            )

            resp = json.loads(response.body)
            curl = resp.get("detail", {}).get("url", "")

            if i < 3:
                assert transid in curl, curl
                assert serial in curl, curl
            if i == 3:
                assert curl == "", curl
            if i == 4:
                assert "validate/check_t" in curl, curl

            assert '"value": false' in response, response

            otp = ocra.callcOtp(challenge, counter=i)

            parameters = {
                "pass": otp,
                "transactionid": transid,
            }

            response = self.make_validate_request("check_t", params=parameters)

            assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)

    def createSpassToken(self, serial=None, user="root", pin="spass"):
        if serial is None:
            serial = "TSpass"
        parameters = {
            "serial": serial,
            "user": user,
            "pin": pin,
            "description": "SpassToken",
            "type": "spass",
        }

        response = self.make_admin_request("init", params=parameters)
        assert '"value": true' in response, response
        return serial

    def test_ocra_and_spass_token(self):
        """
        Test: a user must be able to have an OCRA token and a SPASS token
        """
        spassPin = "spass"
        spassSerial = self.createSpassToken(user="root", pin=spassPin)

        ocra = OcraOtp()
        response1 = self.init_0_QR_Token(user="root")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="Täst äußerst wichtig!"
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        # finish rollout
        otp = ocra.callcOtp(challenge)
        _response = self.check_otp(transid, otp)

        # now run first spass token validate
        parameters = {"user": "root", "pass": spassPin}
        response = self.make_validate_request("check", params=parameters)
        assert '"value": true' in response, response

        # ocra challenge/check
        challenge = "thisismychallenge123"
        cout = ocra.counter
        otp = ocra.callcOtp(challenge, counter=cout + 1)
        parameters = {
            "pass": "pin" + otp,
            "user": "root",
            "challenge": challenge,
        }
        response = self.make_validate_request("check", params=parameters)
        assert '"value": true' in response, response

        # spass fail test
        parameters = {"user": "root", "pass": spassPin + "!"}
        response = self.make_validate_request("check", params=parameters)
        assert '"value": false' in response, response

        # standard ocra test
        (response, challenge, transid) = self.get_challenge(
            ocra.serial, challenge_data="äns zwo dräi"
        )

        otp = ocra.callcOtp(challenge, counter=ocra.counter + 2)
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # spass test
        parameters = {"user": "root", "pass": spassPin}
        response = self.make_validate_request("check", params=parameters)
        assert '"value": true' in response, response

        # standard ocra fail test
        (response, challenge, transid) = self.get_challenge(
            ocra.serial, challenge_data="äns zwo dräi"
        )
        otp = ocra.callcOtp(challenge)
        ootp = self.randOTP(otp)
        response = self.check_otp(transid, ootp)
        assert '"value": false' in response, response

        # standard ocra test
        for i in range(1, 10):
            (response, challenge, transid) = self.get_challenge(
                ocra.serial, challenge_data=f"challenge {i}"
            )
            ocra.counter = ocra.counter + 1
            otp = ocra.callcOtp(challenge)

        parameters = {"user": "root", "pass": "pin" + otp}
        response = self.make_validate_request("check", params=parameters)
        assert '"value": true' in response, response

        # no retry of a challenge
        response = self.check_otp(transid, otp)
        assert '"value": false' in response, response

        # spass test
        parameters = {"user": "root", "pass": spassPin}
        response = self.make_validate_request("check", params=parameters)
        assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)
        self.removeTokens(serial=spassSerial)

    def test_ocra(self):
        """
        OCRA and SPASS token, test validate/check with open transactions
        """
        ocra = OcraOtp()
        response1 = self.init_0_QR_Token(user="root", pin="pin", tokentype="ocra2")
        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            user="root", message="äns zwo dräi", tokentype="ocra2"
        )
        (challenge, transid) = ocra.init_2(response2, activationkey)

        # finish rollout
        otp = ocra.callcOtp(challenge)
        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # standard ocra test
        for i in range(1, 3):
            (response, challenge, transid) = self.get_challenge(
                ocra.serial, challenge_data=f"challenge {i}"
            )
            ocra.counter = ocra.counter + 1
            otp = ocra.callcOtp(challenge)

            # use the new interface to start an challenge response request
            parameters = {
                "user": "root",
                "pass": "pin",
                "challenge": f"challenge {i}",
            }
            response2 = self.make_validate_request("check", params=parameters)
            # extract the stat(=transactionIs) + challenge(=message)
            # to calc the otp and refer to the next validation request

            (response2, challenge, transid) = self.exctract_challenge(response2)

            ocra.counter = ocra.counter + 1
            otp = ocra.callcOtp(
                challenge,
            )

        parameters = {"user": "root", "pass": "pin" + otp}
        response = self.make_validate_request("check", params=parameters)
        assert '"value": true' in response, response

        # no retry of a challenge
        parameters = {"ocra2.max_check_challenge_retry": 0}
        response = self.make_system_request("setConfig", params=parameters)

        response = self.check_otp(transid, otp)
        assert '"value": false' in response, response

        # trigger a new challenge, that will work again
        parameters = {
            "user": "root",
            "pass": "pin",
            "challenge": "challenge 99",
        }
        response2 = self.make_validate_request("check", params=parameters)
        # extract the stat(=transactionIds) + challenge(=message)
        # to calc the otp and refer to the next validation request

        (response2, challenge, transid) = self.exctract_challenge(response2)

        ocra.counter = ocra.counter + 1
        otp = ocra.callcOtp(challenge)

        response = self.check_otp(transid, otp)
        assert '"value": true' in response, response

        # to be tested: checkStatus, resync, challenge as parameter
        self.removeTokens(serial=ocra.serial)

    def setupPolicies2(self):
        self.delete_all_policies()

        params = {
            "name": "l_callback_one",
            "scope": "authentication",
            "realm": "mydefrealm",
            "user": "*",
        }
        params["action"] = (
            "qrtanurl_init.one=https://<user>:<password>/init/one/<serial>/, "
            "qrtanurl.one=https://<user>:<password>/one/<serial>/<transactionid>,"
        )
        response = self.make_system_request("setPolicy", params=params)

        assert '"setPolicy l_callback_one"' in response, response
        assert '"status": true' in response, response

        params = {
            "name": "l_callback",
            "scope": "authentication",
            "realm": "mydefrealm",
            "user": "*",
        }
        params["action"] = (
            "qrtanurl_init=https://<user>:<password>@host/init_<serial>/, "
            "qrtanurl=https://<user>:<password>/callback/<serial>/<transactionid>,"
        )

        response = self.make_system_request("setPolicy", params=params)

        assert '"setPolicy l_callback"' in response, response
        assert '"status": true' in response, response

        return response

    def test_check_signature(self):
        """
        standard challenge response with signature check
        """
        ocrasuite = "OCRA-1:HOTP-SHA256-8:C-QA64"
        message = "Transaktion: Ausrollen eines OCRA2 Tokens"
        serial = "95538327:ocra2:1"

        pin = ""

        ocra = OcraOtp()

        self.setupPolicies2()

        enroll_param = {
            "callback.id": "one",
            "callback.user": "U",
            "callback.password": "PW",
            "description": "PENDING",
            "serial": serial,
        }
        response1 = self.init_0_QR_Token(
            serial=serial,
            pin=pin,
            realm="mydefrealm",
            params=enroll_param,
            ocrasuite=ocrasuite,
        )

        resp = json.loads(response1.body)
        curl = resp.get("detail", {}).get("url", "")
        lse_url = resp.get("detail", {}).get("app_import", "")

        # now check
        # was the callback.id used
        # and if the replacements went right
        assert "one" in curl, curl
        assert "ini" in curl, curl
        assert serial in curl, curl
        assert enroll_param["callback.user"] in curl, curl
        assert urllib.parse.quote(enroll_param["callback.password"]) in curl, curl

        ocra.init_1(response1)
        res = ocra.check_signature(lse_url)
        assert res is None, res

        (response2, activationkey) = self.init_1_QR_Token(
            serial=serial,
            pin=pin,
            message=message,
            realm="mydefrealm",
            params=enroll_param,
        )
        resp = json.loads(response2.body)
        transid = resp.get("detail", {}).get("transactionid", "")
        curl = resp.get("detail", {}).get("url", "")
        lse_url = resp.get("detail", {}).get("app_import", "")

        assert transid in curl, curl
        assert "one" in curl, curl
        assert "ini" not in curl, curl

        (challenge, transid) = ocra.init_2(response2, activationkey)
        res = ocra.check_signature(lse_url)
        assert res, lse_url

        """ finish rollout """
        otp = ocra.callcOtp(challenge)

        response = self.check_otp(transid, otp, pin=pin, params=enroll_param)

        assert '"value": true' in response, response

        for i in range(1, 5):
            message = f"Veränderung {i} am System durchgeführt! Bitte bestätigen!"

            if i == 3:
                enroll_param["no_callback"] = True

            if i == 4:
                del enroll_param["callback.id"]
                del enroll_param["no_callback"]

            (response, challenge, transid) = self.get_challenge(
                ocra.serial, challenge_data=message, params=enroll_param
            )

            resp = json.loads(response.body)
            curl = resp.get("detail", {}).get("url", "")
            lse_url = resp.get("detail", {}).get("message", "")
            res = ocra.check_signature(lse_url)
            assert res, lse_url

            if i < 3:
                assert transid in curl, curl
                assert serial in curl, curl
            if i == 3:
                assert curl == "", curl
            if i == 4:
                assert "/callback/" in curl, curl

            assert '"value": false' in response, response

            otp = ocra.callcOtp(challenge, counter=i)

            parameters = {
                "pass": otp,
                "transactionid": transid,
            }

            response = self.make_validate_request("check_t", params=parameters)

            assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)

    def test_qr_code(self):
        """
        check the response qrcode to contain the same value as the lsqr url
        - derived from test_serial_based_w_callbackid
        """
        ocrasuite = "OCRA-1:HOTP-SHA256-8:C-QA64"
        message = "Transaktion: Ausrollen eines OCRA2 Tokens"
        serial = "ExternalManagedOcraToken"

        pin = ""

        ocra = OcraOtp()

        self.setupPolicies()

        enroll_param = {
            "callback.id": "one",
            "callback.user": "hugo",
            "callback.password": "abracad:abra123",
        }
        response1 = self.init_0_QR_Token(
            serial=serial,
            pin=pin,
            realm="mydefrealm",
            params=enroll_param,
            ocrasuite=ocrasuite,
        )

        # now verify that the qrcode image is the same
        # as the qr code generated from the lseqr value
        resp = json.loads(response1.body)

        qr_img = resp.get("detail", {}).get("ocraurl", {}).get("img", "")
        qr_img = qr_img.split('rc="data:image/png;base64,')[1]

        qr_data = resp.get("detail", {}).get("ocraurl", {}).get("value", "")
        qr_code = create_img(qr_data)
        qr_code = qr_code.split('rc="data:image/png;base64,')[1]

        assert qr_img == qr_code, resp

        assert "lseqr://init" in qr_data, resp
        assert serial in qr_data, resp

        ocra.init_1(response1)

        (response2, activationkey) = self.init_1_QR_Token(
            serial=serial,
            pin=pin,
            message=message,
            realm="mydefrealm",
            params=enroll_param,
        )

        # now verify that the qrcode image is the same
        # as the qr code generated from the lseqr value
        resp = json.loads(response2.body)

        qr_img = resp.get("detail", {}).get("ocraurl", {}).get("img", "")
        qr_img = qr_img.split('rc="data:image/png;base64,')[1]

        qr_data = resp.get("detail", {}).get("ocraurl", {}).get("value", "")
        qr_code = create_img(qr_data)
        qr_code = qr_code.split('rc="data:image/png;base64,')[1]

        assert qr_img == qr_code, resp

        assert "lseqr://nonce" in qr_data, resp
        assert serial in qr_data, resp

        (challenge, transid) = ocra.init_2(response2, activationkey)

        # finish rollout
        otp = ocra.callcOtp(challenge)

        response = self.check_otp(transid, otp, pin=pin, params=enroll_param)

        assert '"value": true' in response, response

        for i in range(1, 5):
            message = f"Veränderung {i} am System durchgeführt! Bitte bestätigen!"

            if i == 3:
                enroll_param["no_callback"] = True

            if i == 4:
                del enroll_param["callback.id"]
                del enroll_param["no_callback"]

            (response, challenge, transid) = self.get_challenge(
                ocra.serial, challenge_data=message, params=enroll_param
            )

            assert '"value": false' in response, response

            # now verify that the qrcode image is the same
            # as the qr code generated from the lseqr value
            resp = json.loads(response.body)

            qr_img = resp.get("detail", {}).get("ocraurl", {}).get("img", "")
            qr_img = qr_img.split('rc="data:image/png;base64,')[1]

            qr_data = resp.get("detail", {}).get("ocraurl", {}).get("value", "")
            qr_code = create_img(qr_data)
            qr_code = qr_code.split('rc="data:image/png;base64,')[1]

            assert qr_img == qr_code, resp

            assert "lseqr://req" in qr_data, resp
            assert transid in qr_data, resp

            # now check if this is the same as the returned message
            assert qr_data == resp.get("detail", {}).get("message", ""), resp

            otp = ocra.callcOtp(challenge, counter=i)

            parameters = {
                "pass": otp,
                "transactionid": transid,
            }

            response = self.make_validate_request("check_t", params=parameters)

            assert '"value": true' in response, response

        self.removeTokens(serial=ocra.serial)


##eof##########################################################################
