#
#    LinOTP - the open source solution for two factor authentication
#    Copyright (C) 2015-2019 KeyIdentity GmbH
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

import typing

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

if typing.TYPE_CHECKING:
    from linotp_selenium_helper.manage_ui import ManageUi

"""
This file contains classes for interacting with elements on the manage page
in the Selenium tests.
"""


class ManageElement:
    """
    Base class for elements (tabs, dialogs) within the manage UI page.

    """

    def __init__(self, manage_ui: "ManageUi"):
        """
        The manage element can be initialised with an existing manage object, or a testcase.
        If the testcase is supplied, it will be used to determine the manage ui instance.
        """
        self.manage = manage_ui
        "The manage page that we are attached to"

    @property
    def driver(self):
        return self.manage.driver

    @property
    def testcase(self):
        return self.manage.testcase

    def open_manage(self):
        "Open Manager page"
        self.manage.open_manage()

    def find_by_css(self, css_value):
        """Return the element indicated by CSS selector"""
        return self.manage.find_by_css(css_value)

    def find_by_id(self, id_value):
        """Return the element by ID"""
        return self.manage.find_by_id(id_value)

    def wait_for_element(self, id_value):
        """
        Wait for the element to appear
        """
        self.manage.find_by_id(id_value)

    def wait_for_waiting_finished(self):
        """
        Wait for server communication to finish
        """
        return self.manage.wait_for_waiting_finished()

    def implicit_wait_disabled(self):
        return self.testcase.implicit_wait_disabled()


class ManageTab(ManageElement):
    """
    Base class for tabs within the Manage UI page
    """

    TAB_INDEX = None
    "Position of the tab in the manage interface"

    CSS_FLEXIGRID_RELOAD = "div.flexigrid div.pReload"
    "Selector for reload element of grid"

    tabpane_css = None
    "Selector for the tab pane"

    flexigrid_css = None
    "Selector for the flexigrid widget"

    def __init__(self, manage_ui: "ManageUi"):
        super().__init__(manage_ui)
        self.tabbutton_css = f"div#tabs > ul[role=tablist] > li[role=tab]:nth-of-type({self.TAB_INDEX}) > a > span"

        self.tabpane_css = f"div#tabs > div.ui-tabs-panel:nth-of-type({self.TAB_INDEX})"
        self.flexigrid_css = self.tabpane_css + " div.flexigrid"

    def _is_tab_open(self):
        """
        Check without waiting whether the tab is currently visible

        @return is tab visible (boolean)
        """
        return self.manage.is_element_visible(self.tabpane_css)

    def wait_for_grid_loading(self):
        """
        The Flexigrid loads in the background when the filter button is clicked. This
        funtion waits for the grid to finish loading and the refresh spinner to disappear,
        which indicates that the data has been updated.
        """
        # While the flexigrid is reloading the tokens, the reload button is set with class 'loading'.
        # Wait for this to disappear
        flexigrid_reloading_css = self.CSS_FLEXIGRID_RELOAD + ".loading"
        self.testcase.disableImplicitWait()

        WebDriverWait(
            self.driver,
            self.testcase.backend_wait_time,
            ignored_exceptions=NoSuchElementException,
        ).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, flexigrid_reloading_css))
        )
        self.testcase.enableImplicitWait()

    def open_tab(self):
        """
        Open tab if necessary and return tab pane element
        """
        self.open_manage()

        if self._is_tab_open():
            return self.find_by_css(self.tabpane_css)

        tab_button = self.find_by_css(self.tabbutton_css)

        WebDriverWait(self.driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, self.tabbutton_css))
        )
        if tab_button.is_enabled():
            self.manage.close_dialogs_and_click(tab_button)

        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, self.tabpane_css))
        )

        assert self._is_tab_open(), f"Tab should be open (css={self.tabpane_css})"

        # Wait for tab pane to show up and return element
        tab_element = self.find_by_css(self.tabpane_css)

        self.wait_for_grid_loading()

        return tab_element

    def _activate_tab(self, tab_id, reload_page=False):
        if reload_page or not self.manage.is_manage_open():
            self.open_manage()

    def get_grid_contents(self) -> list[dict[str, str]]:
        """
        Parse the flexigrid contents and return a list of dicts

        Each dict corresponds to one row in the table. The keys
        are the table headings
        """
        result = []

        grid = self.find_by_css(self.flexigrid_css)

        heading_rows = grid.find_elements(By.CSS_SELECTOR, ".hDiv table th")
        headings = [h.text for h in heading_rows]

        rows = grid.find_elements(By.CSS_SELECTOR, ".bDiv table tr")

        for row in rows:
            values = [cell.text for cell in row.find_elements(By.CSS_SELECTOR, "td")]
            result.append(dict(zip(headings, values, strict=True)))

        return result


class ManageDialog(ManageElement):
    """
    This class provides common access to the dialogs contained in the manage UI.
    """

    CLOSEBUTTON_CSS = "button.ui-dialog-titlebar-close"
    "CSS to select the close button in a dialog"

    TITLE_CSS = "span.ui-dialog-title"
    "CSS to select the dialog title"

    body_id = None
    """The Id of the dialog's body element. The header and
       buttons can be found using this
    """

    menu_css = None
    "CSS of the menu where the entry can be found"

    menu_item_id = None
    "ID of the menu entry, if applicable (e.g. useridresolver, realms dialog)"

    def __init__(
        self,
        manage_ui: "ManageUi",
        dialog_body_id=None,
        close_button_id=None,
        menu_item_id=None,
        menu_css=None,
    ):
        """
        Initialise the dialog box

        :param manage_ui: ref for basic LinOTP UI handling
        :param dialog_body_id: The ID of the dialog body element
        :param close_button_id: html element id of the dialog close button
        :param menu_item_id: The ID of the menu item to open the dialog
        :param menu_css: Default is CSS selector for the LinOTP config menu
        """
        self.manage: ManageUi = manage_ui

        # Configure class. These are only set if not None, so alternatively,
        # derived classes can set these in their class definition

        if dialog_body_id:
            self.body_id = dialog_body_id
        if menu_item_id:
            self.menu_item_id = menu_item_id
        if menu_css:
            self.menu_css = menu_css
        else:
            self.menu_css = manage_ui.MENU_LINOTP_CONFIG_CSS

        self.dialog_css = f'div[aria-describedby="{self.body_id}"]'
        self.buttonset_css = self.dialog_css + " div.ui-dialog-buttonset"
        self.closebutton_css = self.dialog_css + " " + self.CLOSEBUTTON_CSS
        self.title_css = self.dialog_css + " " + self.TITLE_CSS

    def __enter__(self):
        """Declares the infrastructure for using the dialogue as a context manager

        E.g. one can use the dialogue as in
        'with dialogue:
            dialogue.set_an_option()'
        so the closing of the dialogue and other clean up will be taken
        care of in the __exit__() method."""
        self.open()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Clean up code when the dialogue is being called as context manager"""
        self.close_if_open()

    def is_open(self):
        "Return boolean value - whether dialog is open"
        return self.manage.is_element_visible(self.dialog_css)

    def open(self):
        """
        Open the dialog if it is not already open.

        Throws an assertion if this dialog does not have an associated menu entry
        """
        if not self.is_open():
            self.manage.activate_menu_item(self.menu_css, self.menu_item_id)

        self.reparse()

    def wait_for_dialog(self, timeout=10):
        """
        Wait for the dialog to open

        @param timeout: Maximum time to wait in seconds
        """
        WebDriverWait(
            self.driver, timeout, ignored_exceptions=NoSuchElementException
        ).until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.dialog_css)))

    def reparse(self):
        """
        Wait for loading to finish, then parse contents of dialog
        using derived class hook
        """
        # Wait for dialog to open
        self.wait_for_element(self.body_id)
        self.manage.wait_for_waiting_finished()

        self.parse_contents()

    def raise_if_closed(self):
        "Raise an exception if the dialog is not open"
        if not self.is_open():
            msg = f"Dialog #{self.body_id} is not open"
            raise RuntimeError(msg)

    def click_button(self, button_id=None):
        """
        Click a button in the dialog

        :param button_id: ID of the element to click. Defaults to any button
        """
        button_css = self.buttonset_css + " button"
        if button_id:
            button_css += "#" + button_id
        self.find_by_css(button_css).click()

    def close(self):
        """
        Close the dialog
        """
        self.find_by_css(self.dialog_css + " button.ui-dialog-titlebar-close").click()

    def close_if_open(self):
        """
        Check if the dialog is open; dismiss it if it is.
        """
        if self.is_open():
            self.close()

    def get_body_element(self):
        """
        Get dialog body WebElement
        """
        self.raise_if_closed()
        return self.find_by_id(self.body_id)

    def get_text(self):
        """
        Get text contents of the dialog
        """
        self.raise_if_closed()
        element = self.find_by_id(self.body_id)
        text = element.text
        return text

    def get_title(self):
        """
        Get text contents of the dialog title
        """
        self.raise_if_closed()
        text = self.find_by_css(self.title_css).text
        return text

    def check_text(self, expected_text):
        """
        Verify contents of the dialog

        @param: expected_text Check contents and raise an exception if it does not match
        """
        text = self.get_text()
        self._verify_text("Alert text", expected_text, text)

    def check_title(self, expected_text):
        """
        Verify dialog title

        @param: expected_text Check title and raise an exception if it does not match
        """
        text = self.get_title()
        self._verify_text("Dialog title", expected_text, text)

    def _verify_text(self, description, expected_text, text_contents):
        "Check the text contents, raise an exception if not found"
        if text_contents != expected_text:
            msg = f'{description} [{self.body_id}] text does not match. Expected text:"{expected_text}" Found text:"{text_contents}"'
            raise RuntimeError(msg)

    def close_alert_and_get_its_text(self):
        "Close dialog and return the text contents"
        text = self.get_text()
        self.click_button()
        return text

    # ==============================
    # Hooks for derived classes
    # ==============================
    def parse_contents(self):
        """
        Hook to allow derived classes to parse the contents of the dialog when it is opened
        """
        return
