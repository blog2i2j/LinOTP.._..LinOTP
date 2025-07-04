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
"""Contains TokenImport class"""

import os
import tempfile

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.file_detector import LocalFileDetector

from linotp_selenium_helper.manage_ui import ManageUi

from .manage_ui import ManageDialog


class TokenImportError(RuntimeError):
    pass


class TokenImport(ManageDialog):
    """
    TokenImport imports files as Tokens in the LinOTP WebUI
    """

    def __init__(self, manage_ui: ManageUi):
        """
        Base class for all token imports. Derive from this class
        and implement its special behavior. You have to overwrite
        at least the following attributes in your derived class.
            menu_item_id
            body_id
            load_button_id
            file_name_lineedit
        :param manage_ui: The base manage class for the ui elements
        """
        ManageDialog.__init__(self, manage_ui)
        self.menu_css = manage_ui.MENU_LINOTP_IMPORT_TOKEN_CSS

        # Open the appropriate Token import dialog.
        # TopMenu->Import Token File-><safenet/aladdin,oath,yubikey,...>
        self.manage.activate_menu_item(self.menu_css, self.menu_item_id)
        self.wait_for_dialog()

    def do_import(self, file_content=None, file_path=None):
        """
        Imports the file. Currently the only type supported is 'safenet'.
        Either xml_content (string) or file_path (string) has to be present.
        If file_content is not None and there is no path then file_content
        is written to a temporary file that is used for the import.

        :param file_content: xml string with Token import details
        :param file_path: the file path of provided xml token file
        :raises TokenImportError if the import failed
        """

        if not file_content and not file_path:
            msg = """Wrong test implementation. TokenImport.do_import
                            needs file_content or file_path!
                            """
            raise Exception(msg)

        if not self.manage.realm_manager.get_realms_via_api():
            msg = (
                "Test problem: TokenImport requires a realm, but norealms are available"
            )
            raise Exception(msg)

        if file_content:
            # Create the temp xml file with the given file_content.
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".xml"
            ) as tf:
                tf.write(file_content)
                self.file_path = tf.name
        else:
            # Use the provided xml token file.
            self.file_path = file_path

        filepath_input = self.driver.find_element(By.XPATH, self.file_name_lineedit)

        # On firefox the lineedit is not cleared after dialog re-open
        # So we have to do this explicitly
        # Otherwise the token file to load will be added and
        # LinOTP ends up in an undefined state.
        filepath_input.clear()

        # Make the file available, even if using a remote
        # Selenium instance
        with self.driver.file_detector_context(LocalFileDetector):
            # Send the filename to the token file lineedit in the dialog.
            filepath_input.send_keys(self.file_path)

        self.driver.find_element(By.ID, self.load_button_id).click()
        self.manage.wait_for_waiting_finished()

        # delete the temp file if necessary
        if file_content:
            os.unlink(self.file_path)

        self.driver.execute_script("document.activeElement.blur()", None)

        # Check the alert boxes on the top of the LinOTP UI
        info = self.manage.alert_box_handler.last_line
        if info.type != "info" or not info.text.startswith("Token import result:"):
            msg = f"Import failure:{info}"
            raise TokenImportError(msg)


class TokenImportAladdin(TokenImport):
    """
    Import an Aladdin Token file (xml).
    Create an instance and invoke the 'do_import' method.
    """

    menu_item_id = "menu_load_aladdin_xml_tokenfile"
    body_id = "dialog_import_safenet"
    load_button_id = "button_aladdin_load"
    file_name_lineedit = '//*[@id="load_tokenfile_form_aladdin"]/p[2]/input'

    def __init__(self, manage_ui):
        TokenImport.__init__(self, manage_ui)


class TokenImportOATH(TokenImport):
    """
    Import an OATH token file (csv).
        Create an instance and invoke the 'do_import' method.
    """

    menu_item_id = "menu_load_oath_csv_tokenfile"
    body_id = "dialog_import_oath"
    load_button_id = "button_oathcsv_load"
    file_name_lineedit = '//*[@id="load_tokenfile_form_oathcsv"]/p[4]/input[1]'

    def __init__(self, manage_ui):
        TokenImport.__init__(self, manage_ui)
