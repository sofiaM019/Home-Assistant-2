"""Support for media browsing."""
import asyncio
import logging

from homeassistant.components.media_player import BrowseError, BrowseMedia
from homeassistant.components.media_player.const import (
    MEDIA_CLASS_CHANNEL,
    MEDIA_CLASS_DIRECTORY,
    MEDIA_TYPE_CHANNEL,
)

CHILD_TYPE_MEDIA_CLASS = {
    MEDIA_TYPE_CHANNEL: MEDIA_CLASS_CHANNEL,
    "preset": MEDIA_CLASS_CHANNEL,
}

_LOGGER = logging.getLogger(__name__)


class UnknownMediaType(BrowseError):
    """Unknown media type."""


async def build_item_response(media_library, payload, get_thumbnail_url=None):
    """Create response payload for the provided media query."""
    search_id = payload["search_id"]
    search_type = payload["search_type"]

    _, title, media = await get_media_info(media_library, search_id, search_type)
    if get_thumbnail_url is not None:
        thumbnail = await get_thumbnail_url(search_type, search_id)
    else:
        thumbnail = None

    if media is None:
        return None

    children = await asyncio.gather(
        *(item_payload(item, get_thumbnail_url) for item in media)
    )

    response = BrowseMedia(
        media_class=MEDIA_CLASS_DIRECTORY,
        media_content_id=search_id,
        media_content_type=search_type,
        title=title,
        can_play=bool(search_id),
        can_expand=True,
        children=children,
        thumbnail=thumbnail,
    )
    response.calculate_children_class()

    return response


async def item_payload(item, get_thumbnail_url=None):
    """
    Create response payload for a single media item.

    Used by async_browse_media.
    """
    title = item["label"]

    media_class = None

    if "band" in item:
        media_content_type = f"{item['type']}"
        media_content_id = f"{item['band']}"
        can_play = True
        can_expand = False
    else:
        # this case is for the top folder of each type
        # possible content types: album, artist, movie, library_music, tvshow, channel
        media_class = MEDIA_CLASS_DIRECTORY
        media_content_type = item["type"]
        media_content_id = ""
        can_play = False
        can_expand = True

    if media_class is None:
        try:
            media_class = CHILD_TYPE_MEDIA_CLASS[media_content_type]
        except KeyError as err:
            _LOGGER.debug("Unknown media type received: %s", media_content_type)
            raise UnknownMediaType from err

    thumbnail = item.get("thumbnail")
    if thumbnail is not None and get_thumbnail_url is not None:
        thumbnail = await get_thumbnail_url(
            media_content_type, media_content_id, thumbnail_url=thumbnail
        )

    return BrowseMedia(
        title=title,
        media_class=media_class,
        media_content_type=media_content_type,
        media_content_id=media_content_id,
        can_play=can_play,
        can_expand=can_expand,
        thumbnail=thumbnail,
    )


async def library_payload():
    """
    Create response payload to describe contents of a specific library.

    Used by async_browse_media.
    """
    library_info = BrowseMedia(
        media_class=MEDIA_CLASS_DIRECTORY,
        media_content_id="library",
        media_content_type="library",
        title="Media Library",
        can_play=False,
        can_expand=True,
        children=[],
    )

    library = {
        MEDIA_TYPE_CHANNEL: "Channels",
        "preset": "Favorites",
    }

    library_info.children = await asyncio.gather(
        *(
            item_payload(
                {
                    "label": item["label"],
                    "type": item["type"],
                    "uri": item["type"],
                },
            )
            for item in [
                {"label": name, "type": type_} for type_, name in library.items()
            ]
        )
    )

    return library_info


async def get_media_info(media_library, search_id, search_type):
    """Fetch media/channels."""
    thumbnail = None
    title = None
    media = None

    if search_type == "preset":
        nav = await media_library.handle_set("netRemote.nav.state", 1)
        if not nav:
            _LOGGER.error("Failed to enter nav state")
            return thumbnail, title, media
        presets = await media_library.handle_list("netRemote.nav.presets")
        await media_library.handle_set("netRemote.nav.state", 0)
        media = []
        for preset in presets:
            if "band" in preset and "name" in preset and preset["name"].text:
                entry = {
                    **preset,
                    **{
                        "label": preset["name"].text.strip(),
                        "type": "preset",
                    },
                }
                if (
                    not search_id
                    or (search_id.isnumeric() and entry["band"] == int(search_id))
                    or (search_id.lower() in entry["label"].lower())
                ):
                    media.append(entry)
        title = "Favorites"
    if search_type == MEDIA_TYPE_CHANNEL:
        nav = await media_library.handle_set("netRemote.nav.state", 1)
        if not nav:
            _LOGGER.error("Failed to enter nav state")
            return thumbnail, title, media

        channels = await media_library.call(
            "LIST_GET_NEXT/netRemote.nav.list/-1", {"maxItems": 100}
        )
        nav = media_library.handle_set("netRemote.nav.state", 0)

        media = []
        for item in channels.findall("item"):
            if "key" not in item.attrib or not item.attrib["key"]:
                continue

            channel = {"band": int(item.attrib["key"])}
            for field in item.findall("field"):
                if "name" not in field.attrib:
                    continue
                value = []
                for text in field.itertext():
                    value.append(text.strip())
                if not value:
                    continue
                channel[field.attrib["name"]] = "\n".join(value)

            if "name" in channel and channel["name"]:
                entry = {
                    **channel,
                    **{
                        "label": channel["name"],
                        "type": MEDIA_TYPE_CHANNEL,
                    },
                }
                if (
                    not search_id
                    or (search_id.isnumeric() and entry["band"] == int(search_id))
                    or (search_id.lower() in entry["label"].lower())
                ):
                    media.append(entry)
        title = "Channels"
        await nav

    return thumbnail, title, media
