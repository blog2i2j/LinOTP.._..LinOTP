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
Description of OCRA algorithm::

    OcraSuite = CryptoFunction(K, DataInput)

    CryptoFunction = HOTP-H-n
        H in { SHA-1, SHA256, SHA512 }
        n - truncation 4-10 or 0 (= no truncation)

    DataInput = OCRASuite | 00 | C | Q | P | S | T
        OCRASuite - mode of operation
        C - Counter (optional)
        Q - Challenge
        P - hashed password/pin (optional)
        S - session information (optional)
        T - timestamp (optional)


    [C] | QFxx | [PH | Snnn | TG] : Challenge-Response computation

    [C] | QFxx | [PH | TG] : Plain Signature computation

    Each input that is used for the computation is represented by a
    single letter (except Q) as and they are separated by a hyphen.

    + Q: Challenge +
    The input for challenge is further qualified by the formats supported
    by the client for challenge question(s).  Supported values can be:

                    +------------------+-------------------+
                    |    Format (F)    | Up to Length (xx) |
                    +------------------+-------------------+
                    | A (alphanumeric) |       04-64       |
                    |    N (numeric)   |       04-64       |
                    |  H (hexadecimal) |       04-64       |
                    +------------------+-------------------+

                        Table 2: Challenge Format Table

    The default challenge format is N08, numeric and up to 8 digits.

    + P: Pin +
    The input for P is further qualified by the hash function used for
    the PIN/password.  Supported values for hash function can be:

    Hash function (H) - SHA1, SHA256, SHA512.

    The default hash function for P is SHA1.

    + S: Session +
    The input for S is further qualified by the length of the session
    data in bytes.  The client and server could agree to any length but
    the typical values are:

    Length (nnn) - 064, 128, 256, and 512.

    The default length is 064 bytes.

    The input for timestamps is further qualified by G, size of the time-
    step.  G can be specified in number of seconds, minutes, or hours:

            +--------------------+------------------------------+
            | Time-Step Size (G) |           Examples           |
            +--------------------+------------------------------+
            |       [1-59]S      | number of seconds, e.g., 20S |
            |       [1-59]M      |  number of minutes, e.g., 5M |
            |       [0-48]H      |  number of hours, e.g., 24H  |
            +--------------------+------------------------------+

                        Table 3: Time-step Size Table

    Default value for G is 1M, i.e., time-step size is one minute and the
    T represents the number of minutes since epoch time [UT].


    OCRASuite = 'Algorithm:CryptoFunction:DataInput'


    OcraSuite-1:HOTP-SHA512-8:C-QN08-PSHA1

    - OcraSuite-1: OcraSuite Version 1
    - HOTP-SHA512-8: HTOP mit SHA512 verkuerzt auf 8 Ziffern
    - C-QN08-PSHA1:

    - C: mit counter
    - QN08: numerische Challenge bis zu 8 Ziffern
    - PSHA1: SHA1 des Passworts


    OcraSuite-1:HOTP-SHA256-6:QA10-T1M

    - OcraSuite-1: OcraSuite Version 1
    - HOTP-SHA256-6: HTOP mit SHA256 verkuerzt auf 6 Ziffern
    - QA10-T1M:

    - QA10: alphanumerische Challenge bis zu 10 Zeichen.
    - T1M: Timestamp Counter (time step = 1 minute)


    'ocrasuite' in unit tests:

    OcraSuite-1:HOTP-SHA1-6:QN08
    OcraSuite-1:HOTP-SHA256-8:QA08
    OcraSuite-1:HOTP-SHA256-8:QN08-PSHA1

    OcraSuite-1:HOTP-SHA512-8:C-QN08
    OcraSuite-1:HOTP-SHA256-8:C-QN08-PSHA1

    OcraSuite-1:HOTP-SHA512-8:QN08-T1M
    OcraSuite-1:HOTP-SHA512-8:QA10-T1M




    When computing a response, the concatenation order is always the
    following:

        C | OTHER-PARTY-GENERATED-CHALLENGE-QUESTION |
                                YOUR-GENERATED-CHALLENGE-QUESTION | P| S | T


    If a value is empty (i.e., a certain input is not used in the
    computation) then the value is simply not represented in the string.

    The counter on the token or client MUST be incremented every time a
    new computation is requested by the user.  The server's counter value
    MUST only be incremented after a successful OcraSuite authentication.




                CLIENT                                   SERVER
                (PROVER)                                 VERIFIER)
                    |                                        |
                    |   Verifier sends challenge to prover   |
                    |   Challenge = Q                        |
                    |<---------------------------------------|
                    |                                        |
                    |   Prover Computes Response             |
                    |   R = OcraSuite(K, {[C] | Q | [P | S | T]}) |
                    |   Prover sends Response = R            |
                    |--------------------------------------->|
                    |                                        |
                    |  Verifier Validates Response           |
                    |  If Response is valid, Server sends OK |
                    |  If Response is not,  Server sends NOK |
                    |<---------------------------------------|
                    |                                        |


            CLIENT                                             SERVER
            (PROVER)                                          (VERIFIER)
            |                                                  |
            |   1. Client sends client-challenge               |
            |   QC = Client-challenge                          |
            |------------------------------------------------->|
            |                                                  |
            |   2. Server computes server-response             |
            |      and sends server-challenge                  |
            |   RS = OcraSuite(K, [C] | QC | QS | [S | T])          |
            |   QS = Server-challenge                          |
            |   Response = RS, QS                              |
            |<-------------------------------------------------|
            |                                                  |
            |   3. Client verifies server-response             |
            |      and computes client-response                |
            |   OcraSuite(K, [C] | QC | QS | [S | T]) != RS -> STOP |
            |   RC = OcraSuite(K, [C] | QS | QC | [P | S | T])      |
            |   Response = RC                                  |
            |------------------------------------------------->|
            |                                                  |
            |   4. Server verifies client-response             |
            |   OcraSuite(K, [C] | QS | QC | [P|S|T]) != RC -> STOP |
            |   Response = OK                                  |
            |<-------------------------------------------------|
            |                                                  |

"""

import binascii
import hmac
import logging
import re
import secrets
import struct
from datetime import datetime

from linotp.lib.crypto.utils import get_hashalgo_from_description

log = logging.getLogger(__name__)


def is_int(v):
    try:
        int(v)
        return True
    except ValueError:
        return False


def truncated_value(bytes_s):
    # bytes_s = list(map(ord, h))
    offset = bytes_s[-1] & 0xF
    v = (
        (bytes_s[offset] & 0x7F) << 24
        | (bytes_s[offset + 1] & 0xFF) << 16
        | (bytes_s[offset + 2] & 0xFF) << 8
        | (bytes_s[offset + 3] & 0xFF)
    )
    return v


def dec(h, p):
    v = f"{truncated_value(h)}"
    if len(v) < p:
        v = (p - len(v)) * "0" + v
    return v[len(v) - p :]


def int2beint64(i):
    hex_counter = hex(int(i))[2:]
    hex_counter = "0" * (16 - len(hex_counter)) + hex_counter
    bin_counter = binascii.unhexlify(hex_counter)
    return bin_counter


def bytearray_to_bytes(a_bytearray):
    return bytes(list(a_bytearray))


PERIODS = {"H": 3600, "M": 60, "S": 1}


class OcraSuite:
    """
    OCRA-1:HOTP-SHA1-6:QN08
    OCRA-1:HOTP-SHA256-8:QA08
    OCRA-1:HOTP-SHA256-8:QN08-PSHA1

    OCRA-1:HOTP-SHA512-8:C-QN08
    OCRA-1:HOTP-SHA256-8:C-QN08-PSHA1

    OCRA-1:HOTP-SHA512-8:QN08-T1M
    OCRA-1:HOTP-SHA512-8:QA10-T1M
    """

    def __init__(self, ocrasuite, secretObject=None):
        self.secretObj = secretObject
        self.C = None
        self.Q = None
        self.P = None
        self.S = None
        self.T = None

        self.ocrasuite_description = ocrasuite
        (version, crypto, caller) = ocrasuite.split(":")

        # version check
        if version.upper() != "OCRA-1":
            msg = "unsupported ocra version"
            raise Exception(msg)

        # crypto algo
        (hotpStr, hash_type, trunc) = crypto.split("-")

        if hotpStr.upper() != "HOTP":
            msg = f"unsupported hash version: {hotpStr!s}"
            raise Exception(msg)

        self.hash_algo = self._getCrypto(hash_type.lower())
        self.truncation = self._getTruncation(trunc)

        # communication QA10-T1M or C-QN08-PSHA1 . . . QA99??
        params = caller.split("-")
        for param in params:
            # set and verify the counter
            if param[0] == "C":
                self.C = param

            elif param[0] == "Q":
                # verify the challenge description
                self.Q = ("N", 8)
                if len(param[1:]) > 0:
                    if param[1] not in "ANH":
                        msg = "challenge description not in 'ANH'"
                        raise ValueError(msg)
                    length = int(param[2:])
                    # the spec says only max 64
                    if length < 4 or length > 64:
                        msg = "challenge legthn not in len[4,64]"
                        raise ValueError(msg)
                self.Q = (param[1], length)

            elif param[0] == "S":
                # verify and set session description
                self.S = 64
                S = param[1:]
                if S not in ["064", "128", "256", "512"]:
                    msg = f"Unknown session length {S!r}"
                    raise ValueError(msg)
                self.S = int(S)

            elif param[0] == "P":
                # verify and set Pin hash algo
                self.P = self._getCrypto(param[1:] or "SHA1")

            elif param[0] == "T":
                # verify and set timestep parameter
                complement = param[1:] or "1M"
                try:
                    length = 0
                    if not re.match(r"^(\d+[HMS])+$", complement):
                        msg = f"timestep not in [HMS] {complement!r}"
                        raise ValueError(msg)
                    parts = re.findall(r"\d+[HMS]", complement)
                    for part in parts:
                        period = part[-1]
                        quantity = int(part[:-1])
                        length += quantity * PERIODS[period]
                    self.T = length
                except ValueError as exx:
                    msg = f"Invalid timestamp descriptor {complement!r}"
                    raise ValueError(msg) from exx

    def compute(self, data, key=None):
        """
        Compute an HOTP digest using the given key and data input and
        following the current crypto function description.
        """
        h_data = binascii.hexlify(data)
        try:
            data_input = bytearray(self.ocrasuite_description.encode("utf-8") + b"\0")
            for d in data:
                data_input.append(d)

        except Exception as exx:
            log.error("Failed to encode data %r: \n%r", exx, h_data)
            raise exx

        # call the secret object to get the object
        #    convert it to binary
        #                        from linotp.lib.crypto import SecretObj
        h = None

        if self.secretObj is not None:
            h = self.secretObj.hmac_digest(data_input, self.hash_algo)
        else:
            bkey = key
            """' akey = binascii.hexlify(bkey) """
            h = hmac.new(bkey, data_input, self.hash_algo).digest()

        ret = dec(h, self.truncation) if self.truncation else str(truncated_value(h))

        return ret

    def signData(self, data, key=None):
        h = None
        if key is None:
            h = self.secretObj.hmac_digest(data, self.hash_algo)
        else:
            h = hmac.new(key, data, self.hash_algo).digest()
        h_out = binascii.hexlify(h)

        return h_out

    def _getCrypto(self, description):
        """
        Convert the name of a hash algorithm as described in the OATH
        specifications, to a python object handling the digest algorithm
        interface
        """
        hash_type = description.lower()

        if hash_type in ["sha1", "sha256", "sha512"]:
            return get_hashalgo_from_description(hash_type)

        # any other case is an error
        msg = f"Unknown hash algorithm {hash_type!r}"
        raise ValueError(msg)

    def _getTruncation(self, trunc):
        truncation_length = 8
        try:
            truncation_length = int(trunc)
            if truncation_length < 0 or truncation_length > 10:
                msg = f"Invalid truncation length [0,10] {truncation_length!r}"
                raise ValueError(msg)
        except ValueError as exx:
            msg = f"Invalid truncation length {trunc!r}"
            raise ValueError(msg) from exx
        return truncation_length

    ########################################
    # runtime method
    ########################################
    def combineData(
        self,
        C=None,
        Q=None,
        P=None,
        P_digest=None,
        S=None,
        T=None,
        T_precomputed=None,
        Qsc=None,
    ):
        datainput = b""

        if self.C is not None:
            datainput += self._addCounter(C)
        if self.Q is not None:
            datainput += self._addChallenge(Q)
        if self.P is not None:
            datainput += self._addPin(P, P_digest)
        if self.S is not None:
            datainput += self._addSession(S)
        if self.T is not None:
            datainput += self._addTimeStr(T, T_precomputed)

        return datainput

    def _addCounter(self, C):
        datainput = b""
        if self.C:
            try:
                C = int(C)
                if C < 0 or C > 2**64:
                    raise Exception
            except BaseException as exx:
                msg = f"Invalid counter value {C!r}"
                raise ValueError(msg) from exx
            datainput = int2beint64(int(C))
        return datainput

    def _addChallenge(self, Q):
        datainput = b""

        if self.Q:
            max_length = self.Q[1]
            # do some sanity checks
            if Q is None or len(Q) == 0:
                msg = f"challenge is empty : {Q!r}"
                raise ValueError(msg)
            if isinstance(Q, str):
                # this might raise an ascii conversion exception
                Q = Q.encode("utf-8")
            elif not isinstance(Q, str):
                msg = f"challenge is no string: {Q!r}"
                raise ValueError(msg)
            if len(Q) > max_length:
                msg = f"challenge is to long: {Q!r}"
                raise ValueError(msg)

            if self.Q[0] == "N" and not Q.isdigit():
                msg = f"challenge is not digits only: {Q!r}"
                raise ValueError(msg)
            if self.Q[0] == "A" and not Q.isalnum():
                msg = f"challenge is not alpha-numeric: {Q!r}"
                raise ValueError(msg)
            if self.Q[0] == "H":
                try:
                    int(Q, 16)
                except ValueError as exx:
                    msg = f"challenge is hex only: {Q}"
                    raise ValueError(msg) from exx

            # now encode the challenge acordingly
            if self.Q[0] == "N":
                Q = hex(int(Q))[2:]
                Q += "0" * (len(Q) % 2)
                Q = bytes.fromhex(Q)
            elif self.Q[0] == "H":
                Q = bytes.fromhex(Q)
            elif self.Q[0] == "A":
                # nothing to do - take and append
                pass

            datainput = Q
            datainput += b"\0" * (128 - len(Q))

        return datainput

    def _addPin(self, P=None, P_digest=None):
        datainput = ""
        if self.P:
            if P_digest:
                if len(P) == self.P.digest_size:
                    datainput += P_digest
                elif len(P) == 2 * self.P.digest_size:
                    datainput += P_digest.decode("hex")
                else:
                    msg = f"Pin/Password digest invalid {P_digest!r}"
                    raise ValueError(msg)
            elif P is None:
                msg = "Pin/Password missing"
                raise ValueError(msg)
            else:
                if isinstance(P, str):
                    P = P.encode("utf-8")

                datainput = self.P(P).digest()
        return datainput

    def _addSession(self, S):
        datainput = ""
        if self.S:
            if S is None or len(S) > self.S:
                msg = f"session {S!r}"
                raise ValueError(msg)

            datainput = S
            datainput += "\0" * (self.S - len(S))
        return datainput

    def _addTimeStr(self, T=None, T_precomputed=None):
        datainput = b""
        if self.T:
            if T_precomputed is not None and is_int(T_precomputed):
                # t = time.gmtime(T_precomputed*60)
                # timestr = time.strftime('%Y-%m-%d:%H:%M:%S',t)
                data = int2beint64(int(T_precomputed))
            elif is_int(T):
                # t = time.gmtime(T)
                # timestr = time.strftime('%Y-%m-%d:%H:%M:%S',t)
                data = int2beint64(int(T // self.T))

            else:
                msg = f"time format error {self.T!r}"
                raise ValueError(msg)
            datainput += data
        return datainput

    def data2hashChallenge(self, data):
        c_type = self.Q[0]
        c_len = self.Q[1]

        challenge_bin = self.hash_algo(data)
        challenge_hex = challenge_bin.hexdigest()

        if c_type == "A":
            challenge = challenge_hex[:c_len]
        elif c_type == "H":
            challenge = challenge_hex[: c_len * 2]
        elif c_type == "N":
            challenge_num = int(challenge_hex[:c_len], 16)
            challenge = str(challenge_num)

        if len(challenge) < c_len:
            challenge += "\0" * (c_len - len(challenge))
        challenge = challenge[:c_len]

        return str(challenge)

    def data2rawChallenge(self, data):
        c_type = self.Q[0]
        c_len = self.Q[1]

        challenge = ""
        chall = self.data2randomChallenge(data)

        if c_type == "A":
            for c in data:
                if c.isalnum() and ord(c) < 128:
                    challenge += c

        elif c_type == "N":
            for c in data:
                if c.isdigit():
                    challenge += c

        elif c_type == "H":
            for c in data:
                if c.isdigit() or c.lower() in ["a", "b", "c", "d", "e", "f"]:
                    challenge += c

        for _i in range(4):
            if len(challenge) < c_len:
                challenge += "0"

        c_ = len(challenge)
        challenge += chall[c_:]
        challenge = challenge[:c_len]

        return str(challenge)

    def data2randomChallenge(self, data):
        """
        build a random challenge according to the challenge definition
        """
        digits = "0123456789"
        lower_alpha = "abcdefghijklmnopqrstuvwxyz"
        upper_alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        alphnum = f"{lower_alpha}{upper_alpha}{digits}"
        hexs = digits + "abcdef"

        challenge = ""

        c_type = self.Q[0]
        c_len = self.Q[1]

        if c_type == "A":
            for _c in range(c_len):
                challenge += secrets.choice(alphnum)

        elif c_type == "N":
            for _c in range(c_len):
                challenge += secrets.choice(digits)

        elif c_type == "H":
            for _c in range(c_len):
                challenge += secrets.choice(hexs)

        challenge = challenge[:c_len]
        return str(challenge)

    def checkOtp(
        self,
        passw,
        counter,
        window,
        ocraChallenge,
        pin="",
        options=None,
        timeshift=0,
    ):
        """
        check the given passw

        :param passw:     the otp to verified
        :param counter:   the start counter from the token
        :param window:    the range, within the counter should be checked
        :param challenge: the ocra challenge, which goes into the otp calculation
        :param pin:       the ocra token pin
        :param options:   support to identifies nonsequential otp verification
        :param timeshif:  for timebased tokens we support time offsets

        :return:          counter of match - otherwise -1
        """
        ret = -1

        window = int(window)

        # std counter for tokens w.o. timer or counter
        start = counter
        end = counter + 1
        step = 1

        # callculate the start for the timer based tokens
        if self.T is not None:
            ttime = datetime.utcnow()
            ftime = ttime.strftime("%s")
            otime = int(ftime) + timeshift

            step = 1  # self.T

            start = otime - (window * self.T)
            end = otime + (window * self.T)

            # counter preserves the last access time, so we dont allow
            # lookup in the past
            if start < counter:
                # support the assynchronous handling of transactions
                if options is not None and "transactionid" in options:
                    pass
                else:
                    start = counter

        # callculate the start for the counter based tokens
        if self.C is not None:
            start = counter
            end = counter + window
            if options is not None and "transactionid" in options:
                # in case of a provided transactionid, we scroll back in
                # counter to support asynchronous transaction verification

                start = counter - window // 2 if counter > window // 2 else 0
            sdate = datetime.fromtimestamp(start)
            edate = datetime.fromtimestamp(end)

        # finally do the check of the otps
        session = ""
        if "session" in ocraChallenge:
            session = ocraChallenge.get("session")

        # required - will raise exception, if not present
        challenge = ocraChallenge.get("challenge")
        idx = challenge.find(":")
        if idx != -1:
            challenge = challenge[idx + 1 :]

        param = {}
        param["Q"] = challenge
        param["P"] = pin
        param["S"] = session

        for count in range(start, end, step):
            if self.C is not None:
                param["C"] = count

            if self.T is not None:
                param["T"] = count

            c_data = self.combineData(**param)
            otp = self.compute(c_data)

            if passw == otp:
                ret = count
                break

        # support some logging at the end
        if ret == -1:
            if self.T is not None:
                sdate = datetime.fromtimestamp(start)
                edate = datetime.fromtimestamp(end)
                log.info(
                    "[OcraSuite:checkOtp] failed for otp val %r :(exp %r)"
                    " for timerange:  %r - %r ",
                    otp,
                    passw,
                    sdate,
                    edate,
                )
            else:
                log.info(
                    "[OcraSuite:checkOtp] failed for otp val %r :(exp %r)"
                    " for range: %r - %r",
                    otp,
                    passw,
                    start,
                    end,
                )
        return ret


def test():
    # ocrasuite   = 'OcraSuite-1:HOTP-SHA256-8:C-QN08-S128-PSHA1'
    ocrasuite = "OCRA-1:HOTP-SHA256-8:QA08"
    key = "3132333435363738393031323334353637383930313233343536373839303132".decode(
        "hex"
    )
    pin = "1234"
    session = "Kontonummer:1234568|BLZ:5675522|Betrag:1234343434,99"
    challenge = "12345678"
    counter = 11

    param = {}
    param["C"] = counter
    param["Q"] = challenge
    param["P"] = pin
    param["S"] = session

    ocra = OcraSuite(ocrasuite)
    data = ocra.combineData(**param)
    otp = ocra.compute(key, data)

    data = struct.pack(">Q", counter)
    print(f"data {binascii.hexlify(data)!r}")
    print(f"otp {otp!r}")


if __name__ == "__main__":
    """
    devel hook
    """

    test()


# eof######################################
