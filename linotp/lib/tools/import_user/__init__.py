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
import user tool -
  import a csv file of users

if called from within LinOTP

import linotp.model.meta
Session = linotp.model.meta.Session
Engine = meta.engine

"""

import csv
import logging

from linotp.model.imported_user import ImportedUser

log = logging.getLogger(__name__)


class FormatReader:
    """
    support for special csv formats
    """


class DefaultFormatReader(FormatReader):
    delimiter = ","
    quotechar = '"'

    @classmethod
    def prepare_row(cls, row):
        return row


class PasswdFormatReader(FormatReader):
    delimiter = ":"
    quotechar = '"'

    @classmethod
    def prepare_row(cls, row):
        if len(row) < 5:
            return row

        ext_row = row[0:4]

        # support for extend password format, which contains email++

        if "," in row[4]:
            attr = row[4].split(",")
            if len(attr) < 5:
                attr.append("")
        else:
            attr = ["", "", "", "", ""]
            attr[0] = row[4]

        # now split the name into surname and lastname

        if " " in attr[0]:
            ext_name = attr[0].split(" ", 1)
        else:
            ext_name = (attr[0] + " ").split(" ", 1)

        # finally we concat all

        ext_row.extend(ext_name)
        ext_row.extend(attr[1:])
        ext_row.extend(row[5:])

        return ext_row


class UserImport:
    def __init__(self, ImportHandler):
        self.user_column_mapping = {}
        self.import_handler = ImportHandler
        self.encoding = "UTF-8"

    def set_mapping(self, mapping):
        self.user_column_mapping = mapping

    def get_users_from_data(
        self,
        csv_data,
        format_reader,
        passwords_in_plaintext=False,
        hash_passwords=False,
    ):
        """
        for each row
        - iterate over all available database columns and
        - check if there is a column for this in the csv data

        and add the group identifier

        :params hash_passwords: if true the plaintext passwords will be hashed upon reading

        """

        reader = csv.reader(
            csv_data.split("\n"),
            delimiter=format_reader.delimiter,
            quotechar=format_reader.quotechar,
        )

        for row in reader:
            if not row:
                continue

            row = format_reader.prepare_row(row)

            user = ImportedUser()

            for entry in user.user_entries:
                value = ""
                column_id = self.user_column_mapping.get(entry, -1)

                if column_id == -1 or column_id >= len(row):
                    continue

                value = row[column_id]
                user.set(entry, value)

            if passwords_in_plaintext:
                user.plain_password = user.password
                if hash_passwords:
                    user.password = user.create_password_hash(user.plain_password)

            yield user

    def import_csv_users(
        self,
        csv_data,
        dryrun=False,
        format_reader=DefaultFormatReader,
        passwords_in_plaintext=False,
    ):
        """
        insert and update users

        update of users is done in 2 steps

        0. get a list of all former stored userid
        1. insert all csv data, either update or create
        2. all former entries, which have not been update, will be removed

        """
        users_created = {}
        users_not_modified = {}
        users_modified = {}
        processed_users = {}

        former_userids_to_be_removed = self.import_handler.prepare()

        try:
            # -------------------------------------------------------------- --

            # finally remove all former, not updated users
            # update or insert all user from the csv data

            for user in self.get_users_from_data(
                csv_data,
                format_reader,
                passwords_in_plaintext=passwords_in_plaintext,
                hash_passwords=not dryrun,
            ):
                # only store valid users that have a userid and a username
                if not user.userid or not user.username:
                    continue

                # prevent processing user multiple times
                if (user.userid in processed_users) or (
                    user.username in processed_users.values()
                ):
                    msg = (
                        "Violation of unique constraint - "
                        f"duplicate user in data: {user!r}"
                    )
                    raise Exception(msg)
                else:
                    processed_users[user.userid] = user.username

                # search for the user
                former_user = self.import_handler.lookup(user)
                # if it does not exist we create a new one
                if not former_user:
                    users_created[user.userid] = user
                else:
                    # if it already exists remove it from the list of annihilation
                    # those who remain in former_userids_to_be_removed will be deleted
                    if former_user.userid in former_userids_to_be_removed:
                        del former_userids_to_be_removed[former_user.userid]

                    if user == former_user:
                        users_not_modified[user.userid] = user
                    else:
                        users_modified[user.userid] = {
                            "former_user": former_user,
                            "new_user": user,
                        }

            # prepare the results to send back
            result = {
                "created": {
                    userid: user.username for userid, user in users_created.items()
                },
                "updated": {
                    userid: user.username for userid, user in users_not_modified.items()
                },
                "modified": {
                    userid: u["new_user"].username
                    for userid, u in users_modified.items()
                },
                "deleted": former_userids_to_be_removed,
            }

            # wet run:
            if not dryrun:
                for user in users_created.values():
                    self.import_handler.add(user)
                for u in users_modified.values():
                    self.import_handler.update(u["former_user"], u["new_user"])
                for del_userid in former_userids_to_be_removed:
                    self.import_handler.delete_by_id(del_userid)

                self.import_handler.commit()

            return result

        except Exception as exx:
            self.import_handler.rollback()
            log.error(exx)
            raise exx

        finally:
            self.import_handler.close()


# ------------------------------------------------------------------------- --


def main():
    from linotp.lib.tools.import_user.SQLImportHandler import (  # noqa: PLC0415
        Shell_DatabaseContext,
        SQLImportHandler,
    )

    # in the test main() we use a password file, which is prepared
    # for splitting the description fields into csv data

    with open("/linotp/def-passwd") as f:
        csv_data = f.read()

    user_column_map = {
        "userid": 2,
        "username": 0,
        "phone": 8,
        "mobile": 7,
        "email": 9,
        "surname": 5,
        "givenname": 4,
        "password": 1,
    }

    sql_url = "postgresql://otpd:linotp2d@localhost/otpdb"  # gitleaks:allow
    shell_db_context = Shell_DatabaseContext(sql_url=sql_url)

    import_handler = SQLImportHandler(
        groupid="Hello",
        resolver_name="TestResolver",
        database_context=shell_db_context,
    )

    user_import = UserImport(import_handler)

    user_import.set_mapping(user_column_map)

    result = user_import.import_csv_users(csv_data, format_reader=PasswdFormatReader())

    print(result)


if __name__ == "__main__":
    main()
