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

This file contains utilities to generates the URL for smartphone apps like
                google authenticator
                oath token

"""

import base64
import binascii
import logging
import urllib
from urllib.parse import quote

from linotp.lib.policy import get_tokenissuer, get_tokenlabel

Valid_Token_Types = {
    "hmac": "hotp",
    "hotp": "hotp",
    "totp": "totp",
    "motp": "motp",
}

log = logging.getLogger(__name__)


class NoOtpAuthTokenException(Exception):
    pass


def create_google_authenticator(param: dict, user=None) -> str:
    """Create the google url from the parameters

    :param param: dict containing the parameters
    :param user: the user to which the token should be assigned
    :return: the google authenticator url
    """

    serial = param["serial"]
    login = (user and user.login) or param.get("user.login", "")
    realm = (user and user.realm) or param.get("user.realm", "")
    description = param.get("description", "")

    token_label = get_tokenlabel(
        serial=serial, user=login, realm=realm, description=description
    )

    issuer = get_tokenissuer(
        serial=serial, user=login, realm=realm, description=description
    )

    # --------------------------------------------------------------------- --

    # as the issuer is also used as an url parameter,
    # we add it to the parameters

    param["issuer"] = issuer

    # build the label, which is defined as:
    #   label = accountname / issuer (“:” / “%3A”) *”%20” accountname

    label = quote(issuer) + ":" + quote(token_label)

    return google_authenticator_url(label, param)


def google_authenticator_url(label, param):
    """create url for google authenticator

      otpauth://TYPE/LABEL?PARAMETERS

    remark: be aware of that the google authenticator does not support
            other hash algorithms than 'SHA1' and no other digits like '6'!
    remark: the counter value is respected by both, the google authenticator
            and the free otp app
    remark: currently the free otp app handles the issuer not correctly as the
            issuer in the parameter list overrules the account in the LABEL

    :param label: the label for the url prefix
    :param param: request dictionary
    :return: string with google url
    """

    try:
        token_type = Valid_Token_Types[param.get("type", "hotp").lower()]
    except KeyError as exx:
        msg = "not supported otpauth token type: {!r}".format(param.get("type"))
        raise NoOtpAuthTokenException(msg) from exx

    digits = int(param.get("otplen", 6))
    if digits not in [6, 8]:
        msg = "unsupported digits {!r}".format(param.get("otplen"))
        raise Exception(msg)

    algorithm = param.get("hashlib", "SHA1").upper()
    if algorithm not in ["SHA1", "SHA256", "SHA512"]:
        log.info("unsupported hmac hash algorithm %r - adjusting to 'SHA1'")
        algorithm = "SHA1"

    otpkey = param.get("otpkey", "")
    # For mOTP tokens, the `otpkey` already consists of hexadecimal
    # digits. If we “unhexlify” these, we get raw bytes, which is wrong.
    seed = (
        otpkey.encode("ascii") if token_type == "motp" else binascii.unhexlify(otpkey)
    )
    if not seed:
        msg = "Failed to create token url due to missing seed!"
        raise Exception(msg)
    secret = base64.b32encode(seed).decode().strip("=")

    period = int(param.get("timeStep", 30))
    if period not in [30, 60]:
        msg = "unsupported period for totp token {!r}".format(param.get("timeStep"))
        raise Exception(msg)

    # --------------------------------------------------------------------- --

    # gather the url parameters

    url_param = {}
    url_param["secret"] = secret

    # set number of digits but dont add the default
    if digits != 6:
        url_param["digits"] = digits

    # set hmac algorithm but dont add the default
    if algorithm != "SHA1":
        url_param["algorithm"] = algorithm

    if token_type == "totp":
        if period != 30:
            url_param["period"] = period

    elif token_type == "hotp":
        url_param["counter"] = 0

    url_param["issuer"] = param.get("issuer")

    # --------------------------------------------------------------------- --

    # the overall url has a length restriction ~ 400 chars.
    # as the prefix is fixed and the url parameters are required,
    # we will limit the label length

    max_len = 400

    authenticator_params = urllib.parse.urlencode(url_param, quote_via=quote)
    base_len = len(f"otpauth://{token_type}/?{authenticator_params}")
    allowed_label_length = max_len - base_len

    if len(label) > allowed_label_length:
        log.debug(
            "[create_google_authenticator_url] we got %d characters"
            " left for the token label",
            allowed_label_length,
        )

    label = label[0:allowed_label_length]

    # --------------------------------------------------------------------- --

    # create the url

    auth_url = f"otpauth://{token_type}/{label}?{authenticator_params}"

    auth_url_prefix_len = len("otpauth:///") + len(token_type) + len(label)
    log.debug("google authenticator: %r", auth_url[:auth_url_prefix_len])

    return auth_url


def create_oathtoken_url(user, realm, otpkey, type="hmac", serial=""):
    # 'url' : 'oathtoken:///addToken?name='+serial +
    #                '&key='+otpkey+
    #                '&timeBased=false&counter=0&numDigites=6&lockdown=true',

    timebased = ""
    if type.lower() == "totp":
        timebased = "&timeBased=true"

    label = get_tokenlabel(user, realm, serial)
    url_label = quote(label)

    url = (
        f"oathtoken:///addToken?name={url_label}&lockdown=true&key={otpkey}{timebased}"
    )
    return url
