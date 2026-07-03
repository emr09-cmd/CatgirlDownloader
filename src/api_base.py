# api_base.py
#
# Copyright 2026 SilverOS
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from typing import Any, Optional
import requests
from .types import NSFWOption


class BaseDownloaderAPI(ABC):
    #: Set to True in a subclass to have the gear icon next to this
    #: source in the picker be visible and clickable. Sources that
    #: don't override this stay False, so the icon is hidden for them.
    has_settings: bool = False

    def __init__(self, settings: Any = None, source_id: Optional[str] = None) -> None:
        self.endpoint: str = ""
        self.info: Optional[dict[str, Any]] = None
        self.settings = settings
        self.source_id = source_id

    @abstractmethod
    def get_image_url(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> Optional[str]:
        pass

    @abstractmethod
    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        pass

    @abstractmethod
    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        pass

    def get_image(self, url: str) -> Optional[bytes]:
        try:
            r = requests.get(url, timeout=20)
            # The original implementations didn't check status code explicitly in get_image
            # but usually relied on the caller or just returned content.
            # We'll return content if successful, or None on error for safety.
            if r.status_code == 200:
                return r.content
            return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None

    @abstractmethod
    def get_filename_suggestion(self, extension: Optional[str], info: Optional[dict] = None) -> str:
        pass

    # --- API key handling -----------------------------------------------------

    @property
    def api_key_pref_name(self) -> str:
        """Preference key used to store this source's API key."""
        return f"{self.source_id or self.__class__.__name__}_api_key"

    def get_api_key(self) -> Optional[str]:
        """Return the saved API key for this source, or None if unset/no settings."""
        if not self.settings:
            return None
        key = self.settings.get_preference(self.api_key_pref_name)
        return key or None

    def set_api_key(self, value: Optional[str]) -> None:
        """Persist the API key for this source."""
        if not self.settings:
            return
        self.settings.set_preference(self.api_key_pref_name, value or "")

    # --- Settings popover -------------------------------------------------------

    def open_settings_window(self, parent: Any) -> None:
        """
        Called when the gear icon next to this source is clicked.

        No-op by default — most sources have nothing to configure, and
        the gear icon is hidden for them anyway (see `has_settings`).
        Subclasses that need a settings UI (e.g. an API key field)
        should set `has_settings = True` and override this method.
        """
        pass