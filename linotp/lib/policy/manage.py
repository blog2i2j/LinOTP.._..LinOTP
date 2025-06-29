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
"""static policy definitions"""

import logging
import re

from configobj import ConfigObj
from flask_babel import gettext as _

from linotp.lib.config import (
    getFromConfig,
    getLinotpConfig,
    removeFromConfig,
    storeConfig,
)
from linotp.lib.context import request_context as context
from linotp.lib.error import ServerError
from linotp.lib.policy.definitions import validate_policy_definition
from linotp.lib.policy.forward import ForwardServerPolicy
from linotp.lib.type_utils import boolean

from .util import get_copy_of_policies, get_policies

PolicyNameRegex = re.compile("^[a-zA-Z0-9_]*$")


class PolicyWarning(Exception):
    pass


log = logging.getLogger(__name__)


def import_policies(policies):
    """
    import policies

    :param policies: the policies as dict or a result of the parsed ConfigObj
    :return: the number of the imported policies
    """

    for policy_name in policies:
        policy_definition = policies.get(policy_name)

        policy = {
            "name": policy_name,
            "action": policy_definition["action"],
            "active": policy_definition.get("active", "True"),
            "scope": policy_definition["scope"],
            "realm": policy_definition.get("realm", "*") or "*",
            "user": policy_definition.get("user", "*") or "*",
            "time": policy_definition.get("time", "*") or "*",
            "client": policy_definition.get("client", "*") or "*",
        }

        if policy["scope"] == "system":
            policy["enforce"] = True

        ret = setPolicy(policy)

        log.debug("[importPolicy] import policy %s: %r", policy_name, ret)

    return len(policies)


def setPolicy(policy):
    """
    define and store a policy definition

    :param policy: dict with the following keys:

          * name
          * action
          * scope
          * realm
          * user
          * time
          * client

    :return: dict with the results of the stored entries
    """

    ret = {}
    name = policy.get("name")

    if "active" not in policy:
        policy["active"] = "True"

    # check that the name does not contain any bad characters
    if not PolicyNameRegex.match(name):
        raise Exception(
            _("The name of the policy may only contain the characters a-zA-Z0-9_.")
        )

    # verify the required policy attributes
    required_attributes = ["action", "scope", "realm"]
    for required_attribute in required_attributes:
        if required_attribute not in policy or not policy[required_attribute]:
            msg = f"Missing attribute {required_attribute} in policy {name}"
            raise PolicyWarning(msg)

    # before storing the policy, we have to check the impact:
    # if there is a problem, we will raise an exception with a warning

    _check_policy_impact(**policy)

    policy_action_validation = boolean(
        getFromConfig("policy_action_validation", "False")
    )
    if policy_action_validation:
        # raise an exception if the action value is not compliant
        validate_policy_definition(policy)

    # transpose the forwardServer policy action as it might
    # contain sensitive data
    policy["action"] = ForwardServerPolicy.prepare_forward(policy["action"])

    attributes = [
        "action",
        "scope",
        "realm",
        "user",
        "time",
        "client",
        "active",
    ]

    for attr in attributes:
        key = f"Policy.{name}.{attr}"
        value = policy[attr]
        typ = ""
        descr = "a policy definition"
        ret[attr] = storeConfig(key, value, typ, descr)

    return ret


def deletePolicy(name, enforce=False):
    """
    Function to delete one named policy

    attributes:
        name:   (required) will only return the policy with the name
    """
    res = {}
    if not re.match("^[a-zA-Z0-9_]*$", name):
        msg = "policy name may only contain the characters a-zA-Z0-9_"
        raise ServerError(
            msg,
            id=8888,
        )

    if context and context.get("Config"):
        Config = context["Config"]
    else:
        Config = getLinotpConfig()

    #
    # we need the policies for a name lookup only

    policies = get_policies()

    # check if due to delete of the policy a lockout could happen
    param = policies.get(name)
    # delete is same as inactive ;-)
    if param:
        param["active"] = "False"
        param["name"] = name
        param["enforce"] = enforce
        _check_policy_impact(**param)

    delEntries = [
        entry for entry in Config if entry.startswith(f"linotp.Policy.{name}.")
    ]

    for entry in delEntries:
        # delete this entry.
        log.debug("[deletePolicy] removing key: %r", entry)
        ret = removeFromConfig(entry)
        res[entry] = ret

    return res


def _check_policy_impact(
    scope="",
    action="",
    active="True",
    client="",
    realm="",
    time=None,
    user=None,
    name="",
    enforce=False,
):
    """
    check if applying the policy will lock the user out
    """

    # Currently only system policies are checked
    if scope.lower() not in ["system"]:
        return

    reason = ""
    no_system_write_policy = True
    active_system_policy = False

    pol = {
        "scope": scope,
        "action": action,
        "active": active,
        "client": client,
        "realm": realm,
        "user": user,
        "time": time,
    }

    #
    # we need a copy of the policies as we want to modify them
    policies = get_copy_of_policies()

    # add the new policy and check the constrains
    policies[name] = pol

    for policy in policies.values():
        # do we have a system policy that is active?
        p_scope = policy["scope"].lower()
        p_active = policy["active"].lower()

        if p_scope == "system" and p_active == "true":
            active_system_policy = True

            # get the policy actions
            p_actions = [act.strip() for act in policy.get("action", "").split(",")]

            # check if there is a write in the actions
            if "*" in p_actions or "write" in p_actions:
                no_system_write_policy = False
                break

    # for any system policy:
    # if no user is defined defined this can as well result in a lockout
    if not user.strip():
        reason = f"no user defined for system policy {name}!"
    # same for empty realm
    if not realm.strip():
        reason = f"no realm defined for system policy {name}!"

    # if there has been no system policy with write option
    # and there are active system policy left
    if no_system_write_policy and active_system_policy:
        reason = "no active system policy with 'write' permission defined!"

    if reason and enforce is False:
        msg = f"Warning: potential lockout due to policy defintion: {reason}"
        raise PolicyWarning(msg)

    # admin policy could as well result in lockout
    return


def create_policy_export_file(policy, filename):
    """
    This function takes a policy dictionary and creates an export file from it
    """
    TMP_DIRECTORY = "/tmp"
    file_name = f"{TMP_DIRECTORY}/{filename}"
    if len(policy) == 0:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write("")
    else:
        for value in list(policy.values()):
            for k in list(value.keys()):
                value[k] = value[k] or ""

        policy_file = ConfigObj(encoding="UTF-8")
        policy_file.filename = file_name

        for name in list(policy.keys()):
            policy_file[name] = policy[name]
            policy_file.write()

    return file_name
