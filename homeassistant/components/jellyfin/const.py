"""Constants for the Jellyfin integration."""

from typing import Final

DOMAIN: Final = "jellyfin"

CLIENT_VERSION: Final = "1.0"

COLLECTION_TYPE_MOVIES: Final = "movies"
COLLECTION_TYPE_TVSHOWS: Final = "tvshows"
COLLECTION_TYPE_MUSIC: Final = "music"

DATA_CLIENT: Final = "client"

ITEM_KEY_COLLECTION_TYPE: Final = "CollectionType"
ITEM_KEY_ID: Final = "Id"
ITEM_KEY_IMAGE_TAGS: Final = "ImageTags"
ITEM_KEY_INDEX_NUMBER: Final = "IndexNumber"
ITEM_KEY_MEDIA_SOURCES: Final = "MediaSources"
ITEM_KEY_MEDIA_TYPE: Final = "MediaType"
ITEM_KEY_NAME: Final = "Name"

ITEM_TYPE_ALBUM: Final = "MusicAlbum"
ITEM_TYPE_ARTIST: Final = "MusicArtist"
ITEM_TYPE_AUDIO: Final = "Audio"
ITEM_TYPE_LIBRARY: Final = "CollectionFolder"

MAX_STREAMING_BITRATE: Final = "140000000"

MEDIA_SOURCE_KEY_PATH: Final = "Path"

MEDIA_TYPE_AUDIO: Final = "Audio"
MEDIA_TYPE_NONE: Final = ""

SUPPORTED_COLLECTION_TYPES: Final = [COLLECTION_TYPE_MUSIC]

USER_APP_NAME: Final = "Home Assistant"
USER_AGENT: Final = f"Home-Assistant/{CLIENT_VERSION}"
