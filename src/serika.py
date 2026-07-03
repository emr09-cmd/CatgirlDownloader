# serika.py
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

import requests
import json
from typing import Optional, Any

from gi.repository import Gtk
from .types import NSFWOption
from .api_base import BaseDownloaderAPI


class SerikaBooruDownloaderAPI(BaseDownloaderAPI):
    """
    Downloader for Serika Booru (serika.art), per the official API docs.

    Base URL: https://serika.art/api/v1
    Auth: Authorization: Bearer sk_serika_YOUR_API_KEY  (requires the
    images:read permission scope on the key)

    GET /images
      page, limit (<=100), tags, ratings (comma-separated: safe,
      questionable, explicit), sort (newest/oldest/popular/favorites/
      views/random), ai, q, user_id, min_width, min_height

    Response:
        {
          "success": true,
          "data": [
            {
              "id": "...", "post_id": 123, "url": "...",
              "thumbnail_url": "...", "width": .., "height": ..,
              "rating": "safe", "is_ai_generated": false,
              "tags": [{"name": "...", "type": "..."}],
              "stats": {...},
              "user": {"id": "...", "username": "..."},
              "created_at": "..."
            }
          ],
          "meta": {"pagination": {...}}
        }

    This is the only source that shows/uses the gear-icon settings
    popover, since it's the only one that needs an API key.
    """

    has_settings = True

    def __init__(self, settings=None) -> None:
        super().__init__(settings=settings, source_id="serika")
        self.endpoint = "https://serika.art/api/v1/images"

    def _headers(self) -> dict:
        headers = {}
        api_key = self.get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _ratings_for(self, nsfw_mode: NSFWOption) -> str:
        if nsfw_mode == NSFWOption.ONLY_NSFW or nsfw_mode == NSFWOption.ONLY_NSFW.value:
            return "questionable,explicit"
        if nsfw_mode == NSFWOption.SHOW_EVERYTHING or nsfw_mode == NSFWOption.SHOW_EVERYTHING.value:
            return "safe,questionable,explicit"
        # BLOCK_NSFW / default
        return "safe"

    def get_image_url(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> Optional[str]:
        api_key = self.get_api_key()
        if not api_key:
            print("Serika Booru: no API key set. Click the gear icon next to the source to add one.")
            return None

        params = {
            "limit": 1,
            "sort": "random",
            "ratings": self._ratings_for(nsfw_mode),
        }

        try:
            r = requests.get(self.endpoint, params=params, headers=self._headers(), timeout=10)
        except Exception as e:
            print(f"Serika Booru request error: {e}")
            return None

        if r.status_code == 401:
            print("Serika Booru: unauthorized — the API key is missing or invalid.")
            return None
        if r.status_code == 403:
            print("Serika Booru: forbidden — the API key lacks the images:read permission.")
            return None
        if r.status_code == 429:
            print("Serika Booru: rate limited — slow down requests.")
            return None
        if r.status_code != 200:
            print(f"Serika Booru request failed: {r.status_code} {r.text[:200]}")
            return None

        try:
            data = json.loads(r.text)
            if not data.get("success"):
                print(f"Serika Booru error: {data.get('error')} ({data.get('code')})")
                return None
            self.info = data
            return data["data"][0]["url"]
        except Exception as e:
            print(f"Error parsing Serika Booru response: {e}")
            return None

    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            return data["data"][0]["user"]["username"]
        except Exception:
            return None

    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            post_id = data["data"][0]["post_id"]
            return f"https://serika.art/post/{post_id}"
        except Exception:
            return None

    def get_filename_suggestion(self, extension: Optional[str], info: Optional[dict] = None) -> str:
        data = info if info else self.info
        try:
            if data:
                image_id = data["data"][0].get("id", "unknown")
            else:
                raise Exception("No info")
        except Exception:
            import time
            image_id = str(int(time.time()))
        if extension:
            return f"serikabooru_{image_id}.{extension}"
        return f"serikabooru_{image_id}"

    # --- Settings popover: API key only, and only for this source -------------

    def open_settings_window(self, parent: Any) -> None:
        popover = Gtk.Popover()
        popover.set_parent(parent)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_size_request(240, -1)

        label = Gtk.Label(label="Serika Booru API Key", halign=Gtk.Align.START)
        label.add_css_class("heading")
        box.append(label)

        entry = Gtk.Entry()
        entry.set_visibility(False)
        entry.set_placeholder_text("sk_serika_…")
        current = self.get_api_key()
        if current:
            entry.set_text(current)
        entry.set_activates_default(True)
        box.append(entry)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")

        def on_save(btn):
            self.set_api_key(entry.get_text().strip())
            popover.popdown()

        save_btn.connect("clicked", on_save)
        entry.connect("activate", lambda e: on_save(save_btn))
        box.append(save_btn)

        popover.set_child(box)
        popover.popup()