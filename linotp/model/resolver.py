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
from enum import Enum
from logging import getLogger

import linotp
from linotp.lib.realm import getRealms
from linotp.useridresolver import UserIdResolver

log = getLogger(__name__)


class ResolverType(Enum):
    HTTP = "httpresolver"
    LDAP = "ldapresolver"
    SQL = "sqlresolver"
    PW = "passwdresolver"


class User:
    """
    Represents a user for the new API of the manage UI.

    TODO: Ideally this should be fused with the User in lib.user, but that is a
    larger undertaking for which we do not have time now. Perhaps we can tidy up
    the User there and bring its functionality here.
    """

    def __init__(
        self,
        user_id: str,
        resolver_name: str,
        resolver_class: ResolverType,
        username: str,
        surname: str | None,
        given_name: str | None,
        phone: str | None,
        mobile: str | None,
        email: str | None,
    ):
        self.user_id = user_id
        self.resolver_name = resolver_name
        self.resolver_class = resolver_class
        self.username = username
        self.surname = surname or None
        self.given_name = given_name or None
        self.phone = phone or None
        self.mobile = mobile or None
        self.email = email or None

    @staticmethod
    def from_dict(
        resolver_name: str,
        resolver_type: ResolverType,
        user_dictionary: dict,
    ):
        return User(
            user_id=user_dictionary["userid"],
            resolver_name=resolver_name,
            resolver_class=resolver_type,
            username=user_dictionary["username"],
            surname=user_dictionary.get("surname"),
            given_name=user_dictionary.get("givenname"),
            phone=user_dictionary.get("phone"),
            mobile=user_dictionary.get("mobile"),
            email=user_dictionary.get("email"),
        )

    def as_dict(self) -> dict[str, str | str | None]:
        return {
            "userId": self.user_id,
            "resolverClass": self.resolver_class.value,
            "resolverName": self.resolver_name,
            "username": self.username,
            "surname": self.surname,
            "givenName": self.given_name,
            "email": self.email,
            "mobile": self.mobile,
            "phone": self.phone,
        }


class Resolver:
    """
    Class to represent a resolver instance.

    Developer notes: Currently there is no database table for storing resolver
    entries. All resolver information is loaded from the LinOTP Config. In the
    long run we would like to change this, and for now we can already define
    this interface to help us structure the remaining code.
    """

    def __init__(
        self,
        name: str,
        type: ResolverType,
        spec: str,
        read_only: bool | None,
        admin: bool,
        config: UserIdResolver,
    ):
        self._name = name
        self._type = type
        self._spec = spec
        self._is_read_only = read_only
        self._is_admin = admin
        self._configuration_instance = config
        self._realms = None

    @staticmethod
    def from_dict(resolver_dict: dict):
        spec = resolver_dict["spec"]
        resolver_object = linotp.lib.resolver.getResolverObject(spec)
        if not resolver_object:
            resolver_object = linotp.lib.resolver.getResolverObject(
                spec,
                load_config=False,
            )
        if not resolver_object:
            message = f"Could not find a resolver with this spec: {spec}"
            raise linotp.lib.user.NoResolverFound(message)
        return Resolver(
            name=resolver_dict["resolvername"],
            spec=spec,
            type=ResolverType(resolver_object.getResolverClassType()),
            read_only=resolver_dict.get("readonly"),
            admin=resolver_dict["admin"],
            config=resolver_object,
        )

    @property
    def name(self) -> str:
        """
        User-assigned name, unique
        """
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def type(self) -> ResolverType:
        """
        The type of the resolver. Allowed values are defined in the enum
        ResolverType.
        """
        return self._type

    @property
    def spec(self) -> str:
        """
        LinOTP-internal resolver type.
        It should be deprecated as soon as the type attribute is recognized
        everywhere, as it is a dot-separated string which gets split uselessly
        all over the place.
        """
        return self._spec

    @property
    def is_admin(self) -> bool:
        """
        Returns whether the resolver is storing administrator users.
        """
        return self._is_admin

    @is_admin.setter
    def is_admin(self, value: bool):
        self._is_admin = value

    @property
    def is_read_only(self) -> bool:
        """
        Returns whether the resolver is read-only.
        """
        return self._is_read_only

    @property
    def configuration_instance(self) -> UserIdResolver:
        return self._configuration_instance

    @configuration_instance.setter
    def configuration_instance(self, value: UserIdResolver):
        self._configuration_instance = value

    @property
    def realms(self) -> set[str]:
        """
        Set of names of the realms the resolver is in
        """
        result = set()
        all_realms = getRealms()  # later on this should come from the db

        for realm_name, realm_dict in all_realms.items():
            resolver_names = [
                spec.split(".")[-1] for spec in realm_dict["useridresolver"]
            ]
            if self.name in resolver_names:
                result.add(realm_name)
        return result

    def get_users(self, search_dictionary: dict | None = None) -> list[User]:
        """
        List users of a resolver. Some resolvers might limit this result, so it
        is not always guaranteed that the list is complete.

        The list of users can be restricted by supplying a search dictionary,
        where the key maps to a user's attribute.
        """
        if search_dictionary is None:
            search_dictionary = {}
        log.debug(
            "[get_users_of_resolver] with this search dictionary: %r",
            search_dictionary,
        )

        try:
            user_iterator = self.configuration_instance.getUserListIterator(
                search_dictionary
            )
        except AttributeError as no_iterator_found:
            log.info(
                "Getting user list using iterator not possible. "
                "Falling back to fetching userlist without iterator. "
                "Reason: %r",
                no_iterator_found,
            )
            users = []
            for user_dict in self.configuration_instance.getUserList(search_dictionary):
                user = User.from_dict(self.name, self.type, user_dict)
                users.append(user)

                user_dict["useridresolver"] = self.spec
                linotp.lib.user._refresh_user_lookup_cache(user_dict)

            log.debug(
                "[get_users_of_resolver] Found this user list: %r",
                users,
            )
            return users

        users: list[User] = []
        for iteration_results in user_iterator:
            for user_dict in iteration_results:
                user = User.from_dict(self.name, self.type, user_dict)
                users.append(user)

                user_dict["useridresolver"] = self.spec
                linotp.lib.user._refresh_user_lookup_cache(user_dict)

            log.debug(
                "[get_users_of_resolver] Found this user list: %r",
                iteration_results,
            )
        return users

    def as_dict(self):
        """
        Return a JSON-serializable dictionary with the attributes of the
        resolver.
        This requires returning the set of realms as a list,  and the type's
        value.
        """
        return {
            "name": self.name,
            "type": self.type.value,
            "spec": self.spec,
            "readonly": self.is_read_only,
            "admin": self.is_admin,
            "realms": list(self.realms),
        }
