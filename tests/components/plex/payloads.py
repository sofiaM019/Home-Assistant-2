"""Plex XML payloads for testing.

Calls to xml.etree.ElementTree.fromstring are allowed as all payloads are static and known.
"""
import xml.etree.ElementTree as ET


def media_container(attribs={}, *payloads):
    """Create a MediaContainer XML wrapper with the provided attributes."""
    mc = ET.Element("MediaContainer", attrib=attribs)
    mc.set("size", str(len(payloads)))
    for payload in payloads:
        mc.append(payload)
    return ET.tostring(mc, encoding="unicode")


EMPTY_PAYLOAD = media_container()
SECURITY_TOKEN = media_container({"token": "transient-1234567890"})
BASE_LIBRARY_ATTRIBS = {
    "identifier": "com.plexapp.plugins.library",
    "mediaTagPrefix": "/system/bundle/media/flags/",
    "mediaTagVersion": "1603922053",
}
EMPTY_LIBRARY = media_container(BASE_LIBRARY_ATTRIBS)
USER_OWNER_ATTRIBS = {
    "id": "1",
    "thumb": "https://plex.tv/users/1234567890abcdef/avatar?c=11111",
    "title": "User 1",
}

# Plex clients
PLAYER_PLEXWEB_BASE = {
    "machineIdentifier": "plexweb_id",
    "deviceClass": "pc",
    "platform": "Chrome",
    "platformVersion": "14.0",
    "product": "Plex Web",
    "protocol": "plex",
    "protocolCapabilities": "timeline,playback,navigation,mirror,playqueues",
    "protocolVersion": "3",
    "title": "Chrome",
    "version": "4.47.1",
}
PLAYER_SHIELD_BASE = {
    "product": "Plex for Android (TV)",
    "machineIdentifier": "1234567890123456-com-plexapp-android",
    "platformVersion": "9",
    "deviceClass": "stb",
    "protocolVersion": "1",
    "title": "SHIELD Android TV",
    "platform": "Android",
    "protocolCapabilities": "timeline,playback,mirror,playqueues,provider-playback",
}
SESSION_PLAYER_PLEXWEB_ATTRIBS = {
    **PLAYER_PLEXWEB_BASE,
    "address": "1.2.3.5",
    "remotePublicAddress": "10.20.30.40",
    "device": "OSX",
    "model": "hosted",
    "state": "playing",
    "vendor": "",
    "version": "4",
    "userID": "1",
}
SESSION_PLAYER_PLEXWEB_ATTRIBS.pop(
    "protocolCapabilities", None
)  # Not included in sessions
SESSION_PLAYER_SHIELD_ATTRIBS = {
    **PLAYER_SHIELD_BASE,
    "address": "1.2.3.11",
    "remotePublicAddress": "10.20.30.40",
    "device": "SHIELD Android TV",
    "model": "darcy",
    "platform": "Android",
    "profile": "Android",
    "vendor": "NVIDIA",
    "version": "8.9.2.21619",
    "state": "playing",
    "local": "1",
    "relayed": "0",
    "secure": "1",
    "userID": "1",
}
SESSION_PLAYER_SHIELD_ATTRIBS.pop(
    "protocolCapabilities", None
)  # Not included in sessions
PLAYER_PLEXWEB_RESOURCES = media_container(
    {}, ET.Element("Player", attrib=PLAYER_PLEXWEB_BASE)
)
PLAYER_SHIELD_RESOURCES = media_container(
    {}, ET.Element("Player", attrib=PLAYER_SHIELD_BASE)
)

# Movies
MOVIE_COMMON = """
<Video ratingKey="{key}" key="/library/metadata/{key}" guid="com.plexapp.agents.imdb://tt0123456?lang=en" studio="Studio Entertainment" type="movie" title="Movie {key}" librarySectionTitle="Movies" librarySectionID="1" librarySectionKey="/library/sections/1" contentRating="R" summary="Some elaborate summary." rating="9.0" audienceRating="9.5" viewCount="1" lastViewedAt="1505969509" year="2000" tagline="Witty saying." thumb="/library/metadata/{key}/thumb/1590245989" art="/library/metadata/{key}/art/1590245989" duration="9000000" originallyAvailableAt="2000-01-01" addedAt="1377829261" updatedAt="1590245989" audienceRatingImage="rottentomatoes://image.rating.upright" chapterSource="agent" primaryExtraKey="/library/metadata/195540" ratingImage="rottentomatoes://image.rating.certified">
<Genre count="119" filter="genre=25578" id="25578" tag="Sci-Fi" />
<Genre count="197" filter="genre=87" id="87" tag="Action" />
<Director count="4" filter="director=100" id="100" tag="Famous Director" />
<Writer count="2" filter="writer=50000" id="50000" tag="A Writer" />
<Producer count="3" filter="producer=2000" id="2000" tag="Dr. Producer" />
<Country count="452" filter="country=1105" id="1105" tag="USA" />
<Role count="25" filter="actor=1" id="1" role="Character 1" tag="Actor 1" thumb="http://4.3.2.1/t/p/original/1.jpg" />
<Role count="2" filter="actor=2" id="2" role="Character 2" tag = "Actor 2" thumb="http://4.3.2.1/t/p/original/2.jpg" />
<Role filter="actor=3" id="3" role="Character 3" tag="Actor 3" thumb="http://4.3.2.1/t/p/original/3.jpg" />
</Video>"""

# TV Shows (Show -> Season -> Episode)
SHOW_COMMON = """
<Directory ratingKey="{key}" key="/library/metadata/{key}/children" guid="com.plexapp.agents.thetvdb://12345?lang=en" studio="TV Studio" type="show" title="TV Show" contentRating="TV-Y" summary="Elaborate summary." index="1" rating="9.0" year="2000" thumb="/library/metadata/{key}/thumb/1488495292" art="/library/metadata/{key}/art/1488495292" banner="/library/metadata/{key}/banner/1488495292" theme="/library/metadata/{key}/theme/1488495292" duration="3000000" originallyAvailableAt="2000-01-01" leafCount="100" viewedLeafCount="0" childCount="5" addedAt="1377827407" updatedAt="1488495292" primaryExtraKey="/library/metadata/194407">
<Genre tag="Action" />
<Genre tag="Animated" />
<Role tag="Some Actor" />
<Role tag="Another One" />
</Directory>"""

SHOW_SEASONS_PAYLOAD = """<MediaContainer size="1" allowSync="1" art="/library/metadata/30/art/1488495294" banner="/library/metadata/30/banner/1488495294" identifier="com.plexapp.plugins.library" key="30" librarySectionID="2" librarySectionTitle="TV Shows" librarySectionUUID="1d8c8690-2dc5-48e6-9b54-accfacd0067c" mediaTagPrefix="/system/bundle/media/flags/" mediaTagVersion="1603922053" nocache="1" parentIndex="1" parentTitle="TV Show" parentYear="2000" sortAsc="1" summary="Show summary." theme="/library/metadata/30/theme/1488495294" thumb="/library/metadata/30/thumb/1488495294" title1="TV Shows" title2="TV Show" viewGroup="season" viewMode="458810">
<Directory ratingKey="20" key="/library/metadata/20/children" parentRatingKey="30" guid="com.plexapp.agents.thetvdb://12345/1?lang=en" parentGuid="com.plexapp.agents.thetvdb://12345?lang=en" type="season" title="Season 1" parentKey="/library/metadata/30" parentTitle="TV Show" summary="" index="1" parentIndex="1" viewCount="20" lastViewedAt="1524197296" thumb="/library/metadata/20/thumb/1488495294" art="/library/metadata/30/art/1488495294" parentThumb="/library/metadata/30/thumb/1488495294" parentTheme="/library/metadata/30/theme/1488495294" leafCount="14" viewedLeafCount="14" addedAt="1377827368" updatedAt="1488495294">
</Directory>
</MediaContainer>"""

EPISODE_COMMON = """
<Video addedAt="1408989944" art="/library/metadata/30/art/1441479050" contentRating="TV-Y" duration="1419520" grandparentArt="/library/metadata/30/art/1441479050" grandparentGuid="com.plexapp.agents.thetvdb://54321?lang=en" grandparentKey="/library/metadata/30" grandparentRatingKey="30" grandparentTheme="/library/metadata/30/theme/1441479050" grandparentThumb="/library/metadata/30/thumb/1441479050" grandparentTitle="TV Show" guid="com.plexapp.agents.thetvdb://12345/1/{key}?lang=en" index="{episode}" key="/library/metadata/{key}" lastViewedAt="1438105107" librarySectionID="2" librarySectionKey="/library/sections/2" librarySectionTitle="TV Shows" originallyAvailableAt="2000-01-01" parentGuid="com.plexapp.agents.thetvdb://12345/1?lang=en" parentIndex="1" parentKey="/library/metadata/20" parentRatingKey="20" parentThumb="/library/metadata/20/thumb/1441479050" parentTitle="Season 1" ratingKey="{key}" summary="Elaborate Summary." thumb="/library/metadata/{key}/thumb/1590245886" title="Episode {episode}" type="episode" updatedAt="1590245886" viewCount="14" year="2000">
</Video>"""

# Music (Artist -> Album -> Track)
ARTIST_CHILDREN_BASE_ATTRIBS = {
    **BASE_LIBRARY_ATTRIBS,
    "allowSync": "1",
    "art": "/library/metadata/300/art/1604348461",
    "key": "300",
    "librarySectionID": "3",
    "librarySectionTitle": "Music",
    "librarySectionUUID": "ba0c2140-c6ef-448a-9d1b-31020741d014",
    "nocache": "1",
    "parentIndex": "1",
    "parentTitle": "Artist",
    "title1": "Music",
    "title2": "Artist",
}
ARTIST_ALBUMS_ATTRIBS = {
    **ARTIST_CHILDREN_BASE_ATTRIBS,
    "summary": "Artist summary.",
    "thumb": "/library/metadata/300/thumb/1604348461",
    "viewGroup": "album",
    "viewMode": "65592",
}
ALBUM_TRACKS_ATTRIBS = {
    **ARTIST_CHILDREN_BASE_ATTRIBS,
    "grandparentRatingKey": "300",
    "grandparentThumb": "/library/metadata/300/thumb/1604348461",
    "grandparentTitle": "Artist",
    "key": "200",
    "parentTitle": "Album",
    "parentYear": "2019",
    "thumb": "/library/metadata/200/thumb/1604348461",
    "title1": "Artist",
    "title2": "Album",
    "viewGroup": "track",
    "viewMode": "65593",
}
ARTIST_TRACKS_ATTRIBS = {
    **ARTIST_CHILDREN_BASE_ATTRIBS,
    "mixedParents": "1",
    "viewGroup": "track",
    "viewMode": "65593",
}

ARTIST_ALBUMS_PAYLOAD = """<MediaContainer size="1" allowSync="1" art="/library/metadata/300/art/1595543202" identifier="com.plexapp.plugins.library" key="300" librarySectionID="3" librarySectionTitle="Music" librarySectionUUID="ba0c2140-c6ef-448a-9d1b-31020741d014" mediaTagPrefix="/system/bundle/media/flags/" mediaTagVersion="1603922053" nocache="1" parentIndex="1" parentTitle="Artist" summary="Artist summary." thumb="/library/metadata/300/thumb/1595543202" title1="Music" title2="Artist" viewGroup="album" viewMode="65592">
<Directory ratingKey="200" key="/library/metadata/200/children" parentRatingKey="300" guid="plex://album/12345" parentGuid="plex://artist/12345" studio="Studio" type="album" title="Album" parentKey="/library/metadata/300" parentTitle="Artist" summary="" index="1" viewCount="5" lastViewedAt="1605456703" year="2019" thumb="/library/metadata/200/thumb/1602534481" art="/library/metadata/300/art/1595543202" parentThumb="/library/metadata/300/thumb/1595543202" originallyAvailableAt="2019-01-01" addedAt="1602534474" updatedAt="1602534481" loudnessAnalysisVersion="2">
</Directory>
</MediaContainer>"""

ALBUM_PAYLOAD = """<MediaContainer size="1" allowSync="1" identifier="com.plexapp.plugins.library" librarySectionID="3" librarySectionTitle="Music" librarySectionUUID="ba0c2140-c6ef-448a-9d1b-31020741d014" mediaTagPrefix="/system/bundle/media/flags/" mediaTagVersion="1603922053">
<Directory ratingKey="200" key="/library/metadata/200/children" parentRatingKey="300" guid="plex://album/12345" parentGuid="plex://artist/12345" studio="Warp" type="album" title="Album" parentKey="/library/metadata/300" librarySectionTitle="Music" librarySectionID="3" librarySectionKey="/library/sections/5" parentTitle="Artist" summary="" index="1" viewCount="5" lastViewedAt="1605456703" year="2019" thumb="/library/metadata/200/thumb/1602534481" art="/library/metadata/300/art/1595543202" parentThumb="/library/metadata/300/thumb/1595543202" originallyAvailableAt="2019-01-01" leafCount="9" viewedLeafCount="2" addedAt="1602534474" updatedAt="1602534481" loudnessAnalysisVersion="2">
</Directory>
</MediaContainer>"""

TRACK_COMMON = """<Track addedAt="1600999261" art="/library/metadata/300/art/1605462131" duration="250000" grandparentArt="/library/metadata/300/art/1605462131" grandparentGuid="plex://artist/12345" grandparentKey="/library/metadata/300" grandparentRatingKey="300" grandparentThumb="/library/metadata/300/thumb/1605462131" grandparentTitle="Arist Name" guid="plex://track/12345" index="{track}" key="/library/metadata/{key}" lastViewedAt="1603309346" librarySectionID="3" librarySectionKey="/library/sections/3" librarySectionTitle="Music" parentGuid="plex://album/12345" parentIndex="1" parentKey="/library/metadata/200" parentRatingKey="200" parentThumb="/library/metadata/200/thumb/1605462119" parentTitle="Album Title" ratingKey="{key}" summary="" thumb="/library/metadata/200/thumb/1605462119" title="Track {track}" type="track" updatedAt="1605462119" viewCount="1"></Track>"""

# Photos
PHOTO_999_COMMON = """
<Photo addedAt="1605739344" createdAtAccuracy="local" createdAtTZOffset="-18000" guid="local://999" index="1" key="/library/metadata/999" librarySectionID="4" librarySectionKey="/library/sections/4" librarySectionTitle="Photos" originallyAvailableAt="2020-10-31" ratingKey="999" summary="" thumb="/library/metadata/999/thumb/1605739344" title="Photo 1" type="photo" updatedAt="1605739344" viewOffset="0" year="2020">
<Media aspectRatio="1.33" container="jpeg" height="2880" id="381658" width="1620">
<Part container="jpeg" file="/storage/photos/Photo 1.jpeg" id="382082" key="/library/parts/382082/1604162245/file.jpeg" size="500000" />
</Media>
</Photo>"""

# Media file metadata
TRACK_MEDIA_AUDIO_ATTRIBS = {
    "id": "381515",
    "duration": "250000",
    "bitrate": "256",
    "audioChannels": "2",
    "audioCodec": "mp3",
    "container": "mp3",
}
TRACK_PART_AUDIO_ATTRIBS = {
    "id": "381939",
    "key": "/library/parts/381939/1602996958/file.mp3",
    "duration": "250000",
    "file": "/storage/music/Artist Name/Album Name/Track Name.mp3",
    "size": "5000000",
    "container": "mp3",
}
TRACK_STREAM_AUDIO_ATTRIBS = {
    "id": "766687",
    "streamType": "2",
    "selected": "1",
    "codec": "mp3",
    "index": "0",
    "channels": "2",
    "bitrate": "256",
    "albumGain": "-10.34",
    "albumPeak": "1.000000",
    "albumRange": "8.429853",
    "audioChannelLayout": "stereo",
    "gain": "-10.34",
    "loudness": "-11.38",
    "lra": "7.80",
    "peak": "0.870300",
    "samplingRate": "44100",
    "displayTitle": "Unknown (MP3 Stereo)",
    "extendedDisplayTitle": "Unknown (MP3 Stereo)",
}

# Metadata (with session)
SESSION_MEDIA_AUDIO_ATTRIBS = {**TRACK_MEDIA_AUDIO_ATTRIBS, "selected": "1"}
SESSION_PART_AUDIO_ATTRIBS = {
    **TRACK_PART_AUDIO_ATTRIBS,
    "decision": "directplay",
    "selected": "1",
}
SESSION_STREAM_AUDIO_ATTRIBS = {
    **TRACK_STREAM_AUDIO_ATTRIBS,
    "location": "direct",
    "selected": "1",
}


# Attributes for MEDIA, PART, and STREAM elements
MEDIA_VIDEO_ATTRIBS = {
    "id": "2637",
    "duration": "9000000",
    "bitrate": "7500",
    "width": "1280",
    "height": "544",
    "aspectRatio": "2.35",
    "audioChannels": "6",
    "audioCodec": "dca",
    "videoCodec": "h264",
    "videoResolution": "720",
    "container": "mkv",
    "videoFrameRate": "24p",
    "audioProfile": "dts",
    "videoProfile": "high",
}
PART_VIDEO_ATTRIBS = {
    "id": "4631",
    "key": "/library/parts/4631/1215643935/file.mkv",
    "duration": "9000000",
    "file": "/storage/videos/video.mkv",
    "size": "8500000000",
    "audioProfile": "dts",
    "container": "mkv",
    "videoProfile": "high",
}
STREAM_VIDEO_ATTRIBS = {
    "id": "21428",
    "streamType": "1",
    "default": "1",
    "codec": "h264",
    "index": "0",
    "bitrate": "6000",
    "language": "English",
    "languageCode": "eng",
    "bitDepth": "8",
    "chromaLocation": "left",
    "chromaSubsampling": "4:2:0",
    "codedHeight": "544",
    "codedWidth": "1280",
    "frameRate": "23.976",
    "hasScalingMatrix": "0",
    "height": "544",
    "level": "51",
    "profile": "high",
    "refFrames": "8",
    "scanType": "progressive",
    "title": "x264 @ 6000 kbps",
    "width": "1280",
    "displayTitle": "720p (H.264)",
    "extendedDisplayTitle": "x264 @ 6000 kbps (720p H.264)",
}
STREAM_AUDIO_ATTRIBS = {
    "id": "21429",
    "streamType": "2",
    "selected": "1",
    "default": "1",
    "codec": "dca",
    "index": "1",
    "channels": "6",
    "bitrate": "1500",
    "language": "English",
    "languageCode": "eng",
    "audioChannelLayout": "5.1(side)",
    "bitDepth": "16",
    "profile": "dts",
    "samplingRate": "48000",
    "title": "DTS 5.1 @ 1500 kbps",
    "displayTitle": "English (DTS 5.1)",
    "extendedDisplayTitle": "DTS 5.1 @ 1500 kbps (English)",
}
STREAM_SUB_ATTRIBS = {
    "id": "21430",
    "streamType": "3",
    "default": "1",
    "codec": "srt",
    "index": "2",
    "language": "English",
    "languageCode": "eng",
    "displayTitle": "English (SRT)",
    "extendedDisplayTitle": "English (SRT)",
}


def fetch_video_element(key, payload):
    """Update a Video element with SubElements."""
    element = ET.fromstring(payload.format(key=key))  # nosec
    for video_node in element.iter("Video"):
        ET.SubElement(video_node, "Media", attrib=MEDIA_VIDEO_ATTRIBS)
        ET.SubElement(video_node, "Part", attrib=PART_VIDEO_ATTRIBS)
        ET.SubElement(video_node, "Stream", attrib=STREAM_VIDEO_ATTRIBS)
        ET.SubElement(video_node, "Stream", attrib=STREAM_AUDIO_ATTRIBS)
        ET.SubElement(video_node, "Stream", attrib=STREAM_SUB_ATTRIBS)
    return element


def fetch_movie(key):
    """Create a movie Media Container."""
    node = fetch_video_element(key, MOVIE_COMMON)
    mc_attribs = {
        **BASE_LIBRARY_ATTRIBS,
        "allowSync": "1",
        "librarySectionID": "1",
        "librarySectionTitle": "Movies",
        "librarySectionUUID": "805308ec-5019-43d4-a449-75d2b9e42f93",
    }
    return media_container(mc_attribs, node)


def fetch_episode_node(key):
    """Return an episode Video element."""
    episode = key - 9
    return fetch_video_element(key, EPISODE_COMMON.format(key=key, episode=episode))


def fetch_episode(key):
    """Return an episode Media Container."""
    node = fetch_episode_node(key)
    mc_attribs = {
        **BASE_LIBRARY_ATTRIBS,
        "allowSync": "1",
        "librarySectionID": "2",
        "librarySectionTitle": "TV Shows",
        "librarySectionUUID": "905308ec-5019-43d4-a449-75d2b9e42f93",
    }
    return media_container(mc_attribs, node)


def fetch_season():
    """Return a season Media Container."""
    nodes = []
    for key in range(10, 20):
        nodes.append(fetch_episode_node(key))
    mc_attribs = {
        **BASE_LIBRARY_ATTRIBS,
        "allowSync": "1",
        "librarySectionID": "2",
        "librarySectionTitle": "TV Shows",
        "librarySectionUUID": "905308ec-5019-43d4-a449-75d2b9e42f93",
    }
    return media_container(mc_attribs, *nodes)


def fetch_show(key):
    """Return a show Media Container."""
    show_fetch = ET.fromstring(SHOW_COMMON.format(key=key))  # nosec
    for directory_node in show_fetch.iter("Directory"):
        ET.SubElement(directory_node, "Location", path="/storage/tvshows/TV Show")
    mc_attribs = {
        **BASE_LIBRARY_ATTRIBS,
        "allowSync": "1",
        "librarySectionID": "2",
        "librarySectionTitle": "TV Shows",
        "librarySectionUUID": "905308ec-5019-43d4-a449-75d2b9e42f93",
    }
    return media_container(mc_attribs, show_fetch)


def fetch_track_element(key, single):
    """Return a track Track element."""
    track = key - 99
    element = ET.fromstring(TRACK_COMMON.format(key=100, track=track))  # nosec
    for track_node in element.iter("Track"):
        ET.SubElement(track_node, "Media", attrib=TRACK_MEDIA_AUDIO_ATTRIBS)
        ET.SubElement(track_node, "Part", attrib=TRACK_PART_AUDIO_ATTRIBS)
        if single:
            ET.SubElement(track_node, "Stream", attrib=TRACK_STREAM_AUDIO_ATTRIBS)
    return element


def fetch_track(key, single=True):
    """Return a track Media Container."""
    node = fetch_track_element(key, single)
    mc_attribs = {
        **BASE_LIBRARY_ATTRIBS,
        "allowSync": "1",
        "librarySectionID": "3",
        "librarySectionTitle": "Music",
        "librarySectionUUID": "005308ec-5019-43d4-a449-75d2b9e42f93",
    }
    return media_container(mc_attribs, node)


def fetch_artist_tracks(key):
    """Return an artist Media Container of tracks."""
    nodes = []
    for key in range(100, 110):
        nodes.append(fetch_track_element(key, single=False))
    return media_container(ARTIST_TRACKS_ATTRIBS, *nodes)


def fetch_album_tracks(key):
    """Return an album Media Container of tracks."""
    nodes = []
    for key in range(100, 110):
        nodes.append(fetch_track_element(key, single=False))
    return media_container(ALBUM_TRACKS_ATTRIBS, *nodes)


def fetch_grandchildren(key):
    """Return payload for a media item's grandchildren."""
    if key == 300:
        return fetch_artist_tracks(key)


def fetch_children(key):
    """Return payload for a media item's children."""
    if key == 20:
        return fetch_season()
    elif key == 30:
        return SHOW_SEASONS_PAYLOAD
    elif key == 200:
        return fetch_album_tracks(key)
    elif key == 300:
        return ARTIST_ALBUMS_PAYLOAD


def fetch_media(key):
    """Return payload for a media item."""
    if key < 10:
        return fetch_movie(key)
    elif key < 20:
        return fetch_episode(key)
    elif key == 30:
        return fetch_show(key)
    elif key < 200:
        return fetch_track(key)
    elif key == 200:
        return ALBUM_PAYLOAD


def fetch_playlist(key):
    """Return payload for a playlist."""
    node = fetch_video_element(1, MOVIE_COMMON)
    attribs = {
        "composite": "/playlists/{key}/composite/1606158679",
        "duration": "5000",
        "leafCount": "1",
        "playlistType": "video",
        "ratingKey": str(key),
        "smart": "0",
        "title": f"Playlist {key}",
    }
    return media_container(attribs, node)


def generate_photo_session(session_key, player, user):
    """Generate photo XML payload for 'status/sessions'."""
    session_root = ET.fromstring(PHOTO_999_COMMON)  # nosec
    for photo_node in session_root.iter("Photo"):
        photo_node.set("viewOffset", "0")
        photo_node.set("sessionKey", session_key)
        photo_node.append(player)
        photo_node.append(user)
    return media_container({}, session_root)


def generate_video_session(media_payload, offset, session_key, player, user):
    """Generate video XML payload for 'status/sessions'."""
    session_root = ET.fromstring(media_payload)  # nosec
    for video_node in session_root.iter("Video"):
        video_node.set("viewOffset", offset)
        video_node.set("sessionKey", session_key)
        video_node.append(player)
        video_node.append(user)
        ET.SubElement(
            video_node, "Session", id="session_id_1", bandwidth="7000", location="lan"
        )
        media_node = ET.SubElement(
            video_node,
            "Media",
            audioProfile="dts",
            id="2637",
            videoProfile="high",
            audioChannels="2",
            audioCodec="aac",
            bitrate="6000",
            container="mp4",
            duration="9000000",
            height="544",
            optimizedForStreaming="1",
            protocol="dash",
            videoCodec="h264",
            videoFrameRate="24p",
            videoResolution="720p",
            width="1280",
            selected="1",
        )
        part_node = ET.SubElement(
            media_node,
            "Part",
            audioProfile="dts",
            id="4631",
            videoProfile="high",
            bitrate="6000",
            container="mp4",
            duration="9000000",
            height="544",
            optimizedForStreaming="1",
            protocol="dash",
            width="1280",
            decision="transcode",
            selected="1",
        )
        ET.SubElement(
            part_node,
            "Stream",
            bitrate="6000",
            codec="h264",
            default="1",
            displayTitle="720p (H.264)",
            extendedDisplayTitle="x264 @ 6000 kbps (720p H.264)",
            frameRate="23.975999999999999",
            height="544",
            id="21428",
            language="English",
            languageCode="eng",
            streamType="1",
            width="1280",
            decision="copy",
            location="segments-video",
        )
        ET.SubElement(
            part_node,
            "Stream",
            bitrate="256",
            bitrateMode="cbr",
            channels="2",
            codec="aac",
            default="1",
            displayTitle="English (DTS 5.1)",
            extendedDisplayTitle="DTS 5.1 @ 1536 kbps (English)",
            id="21429",
            language="English",
            languageCode="eng",
            selected="1",
            streamType="2",
            decision="transcode",
            location="segments-audio",
        )

    return media_container({}, session_root)


def generate_session(
    kind="movie", client_type="native", offset="0", session_key="1", user_id="1"
):
    """Generate XML payload for 'status/sessions'."""
    if client_type == "plexweb":
        player_attribs = SESSION_PLAYER_PLEXWEB_ATTRIBS
    else:
        player_attribs = SESSION_PLAYER_SHIELD_ATTRIBS

    player = ET.Element("Player", attrib=player_attribs, userID=str(user_id))
    user = ET.Element(
        "User",
        id=user_id,
        thumb="https://plex.tv/users/1234567890abcdef/avatar?c=11111",
        title=f"User {user_id}",
    )

    if kind == "movie":
        return generate_video_session(
            MOVIE_COMMON.format(key=1), offset, session_key, player, user
        )
    elif kind == "episode":
        return generate_video_session(
            EPISODE_COMMON.format(key=10, episode=1), offset, session_key, player, user
        )
    elif kind == "photo":
        return generate_photo_session(session_key, player, user)


MUSIC_LIBRARY_ALL = """
<MediaContainer size="1" allowSync="1" art="/:/resources/artist-fanart.jpg" identifier="com.plexapp.plugins.library" librarySectionID="3" librarySectionTitle="Music" librarySectionUUID="ba0c2140-c6ef-448a-9d1b-31020741d014" mediaTagPrefix="/system/bundle/media/flags/" mediaTagVersion="1603922053" nocache="1" sortAsc="1" thumb="/:/resources/artist.png" title1="Music" title2="All Artists" viewGroup="artist" viewMode="131124">
<Directory ratingKey="300" key="/library/metadata/300/children" guid="plex://artist/12345" type="artist" title="Artist" summary="Artist summary." index="1" viewCount="64" lastViewedAt="1605456703" thumb="/library/metadata/300/thumb/1595543202" art="/library/metadata/300/art/1595543202" addedAt="1595543193" updatedAt="1595543202">
<Genre tag="Electronic" />
<Country tag="United Kingdom" />
</Directory>
</MediaContainer>"""


def generate_library_all(kind):
    """Return a payload for all items in a library."""
    payloads = []
    short_name = kind
    attribs = {
        **BASE_LIBRARY_ATTRIBS,
        "allowSync": "1",
        "art": f"/:/resources/{short_name}-fanart.jpg",
        "nocache": "1",
        "sortAsc": "1",
        "thumb": f"/:/resources/{short_name}.png",
        "viewGroup": short_name,
        "viewMode": "131122",
    }
    if kind == "movie":
        attribs = {
            **attribs,
            "librarySectionID": "1",
            "librarySectionTitle": "Movies",
            "title": "Movies",
            "title1": "All Movies",
            "librarySectionUUID": "805308ec-5019-43d4-a449-75d2b9e42f93",
        }
        for key in range(1, 6):
            movie_payload = ET.fromstring(MOVIE_COMMON.format(key=key))  # nosec
            payloads.append(movie_payload)
    elif kind == "show":
        attribs = {
            **attribs,
            "librarySectionID": "2",
            "librarySectionTitle": "TV Shows",
            "title": "TV Shows",
            "title1": "All Shows",
            "librarySectionUUID": "905308ec-5019-43d4-a449-75d2b9e42f93",
        }
        payloads.append(ET.fromstring(SHOW_COMMON.format(key=30)))  # nosec
    elif kind == "artist":
        return MUSIC_LIBRARY_ALL

    return media_container(attribs, *payloads)


# Plex Server
PLEX_SERVER_BASE = """<MediaContainer size="25" allowCameraUpload="1" allowChannelAccess="1" allowMediaDeletion="1" allowSharing="1" allowSync="1" allowTuners="1" backgroundProcessing="1" certificate="1" companionProxy="1" countryCode="usa" diagnostics="logs,databases,streaminglogs" eventStream="1" friendlyName="{name}" hubSearch="1" itemClusters="1" livetv="7" machineIdentifier="{machine_identifier}" mediaProviders="1" multiuser="1" myPlex="1" myPlexMappingState="mapped" myPlexSigninState="ok" myPlexSubscription="1" myPlexUsername="myplexusername@email.com" offlineTranscode="1" ownerFeatures="adaptive_bitrate,camera_upload,cloudsync,collections,content_filter,download_certificates,dvr,federated-auth,hardware_transcoding,home,hwtranscode,item_clusters,kevin-bacon,livetv,loudness,lyrics,music_videos,news,pass,photo_autotags,photos-v5,photosV6-edit,photosV6-tv-albums,premium_music_metadata,radio,server-manager,session_bandwidth_restrictions,session_kick,shared-radio,sync,trailers,tuner-sharing,type-first,unsupportedtuners,webhooks" photoAutoTag="1" platform="Linux" platformVersion="20.04.1 LTS (Focal Fossa)" pluginHost="1" pushNotifications="0" readOnlyLibraries="0" requestParametersInCookie="1" streamingBrainABRVersion="3" streamingBrainVersion="2" sync="1" transcoderActiveVideoSessions="0" transcoderAudio="1" transcoderLyrics="1" transcoderPhoto="1" transcoderSubtitles="1" transcoderVideo="1" transcoderVideoBitrates="64,96,208,320,720,1500,2000,3000,4000,8000,10000,12000,20000" transcoderVideoQualities="0,1,2,3,4,5,6,7,8,9,10,11,12" transcoderVideoResolutions="128,128,160,240,320,480,768,720,720,1080,1080,1080,1080" updatedAt="1605463238" updater="1" version="1.20.4.3517-ab5e1197c" voiceSearch="1">
<Directory count="1" key="activities" title="activities" />
<Directory count="1" key="butler" title="butler" />
<Directory count="1" key="channels" title="channels" />
<Directory count="1" key="clients" title="clients" />
<Directory count="1" key="devices" title="devices" />
<Directory count="1" key="diagnostics" title="diagnostics" />
<Directory count="1" key="hubs" title="hubs" />
<Directory count="3" key="library" title="library" />
<Directory count="3" key="livetv" title="livetv" />
<Directory count="3" key="media" title="media" />
<Directory count="2" key="metadata" title="metadata" />
<Directory count="1" key="neighborhood" title="neighborhood" />
<Directory count="1" key="playQueues" title="playQueues" />
<Directory count="1" key="player" title="player" />
<Directory count="1" key="playlists" title="playlists" />
<Directory count="1" key="resources" title="resources" />
<Directory count="1" key="search" title="search" />
<Directory count="1" key="server" title="server" />
<Directory count="1" key="servers" title="servers" />
<Directory count="1" key="statistics" title="statistics" />
<Directory count="1" key="system" title="system" />
<Directory count="1" key="transcode" title="transcode" />
<Directory count="2" key="tv%2Eplex%2Eproviders%2Eepg%2Ecloud%3A2" title="tv.plex.providers.epg.cloud:2" />
<Directory count="1" key="updater" title="updater" />
<Directory count="1" key="user" title="user" />
</MediaContainer>"""
PLEX_SERVER_PAYLOAD = PLEX_SERVER_BASE.format(
    name="Plex Server 1", machine_identifier="unique_id_123"
)

PMS_ACCOUNT_PAYLOAD = """
<MediaContainer size="4" identifier="com.plexapp.system.accounts">
<Account id="0" key="/accounts/0" name="" defaultAudioLanguage="en" autoSelectAudio="1" defaultSubtitleLanguage="en" subtitleMode="1" thumb="" />
<Account id="1" key="/accounts/1" name="User 1" defaultAudioLanguage="en" autoSelectAudio="1" defaultSubtitleLanguage="en" subtitleMode="1" thumb="" />
<Account id="1000" key="/accounts/1000" name="User 1000" defaultAudioLanguage="en" autoSelectAudio="1" defaultSubtitleLanguage="en" subtitleMode="1" thumb="" />
<Account id="1001" key="/accounts/1001" name="User 1001" defaultAudioLanguage="en" autoSelectAudio="1" defaultSubtitleLanguage="en" subtitleMode="1" thumb="" />
</MediaContainer>"""

PMS_CLIENTS = """<MediaContainer size="1">
<Server name="SHIELD Android TV" host="1.2.3.11" address="1.2.3.11" port="32500" machineIdentifier="1234567890123456-com-plexapp-android" version="8.8.2.21525" protocol="plex" product="Plex for Android (TV)" deviceClass="mobile" protocolVersion="1" protocolCapabilities="timeline,playback,mirror,playqueues,provider-playback" />
</MediaContainer>"""

# plex.tv
PLEXTV_ACCOUNT_PAYLOAD = """
<user email="myplexusername@email.com" id="12345" uuid="1234567890" mailing_list_status="active" thumb="https://plex.tv/users/1234567890abcdef/avatar?c=11111" username="User 1" title="User 1" cloudSyncDevice="" locale="" authenticationToken="faketoken" authToken="faketoken" scrobbleTypes="" restricted="0" home="1" guest="0" queueEmail="queue+1234567890@save.plex.tv" queueUid="" hasPassword="true" homeSize="2" maxHomeSize="15" secure="1" certificateVersion="2">
  <subscription active="1" status="Active" plan="lifetime">
    <feature id="companions_sonos"/>
  </subscription>
  <roles>
    <role id="plexpass"/>
  </roles>
  <entitlements all="1"/>
  <profile_settings default_audio_language="en" default_subtitle_language="en" auto_select_subtitle="1" auto_select_audio="1" default_subtitle_accessibility="0" default_subtitle_forced="0"/>
  <services/>
  <username>testuser</username>
  <email>testuser@email.com</email>
  <joined-at type="datetime">2000-01-01 12:34:56 UTC</joined-at>
  <authentication-token>faketoken</authentication-token>
</user>
"""

PLEXTV_RESOURCES_BASE = """<MediaContainer size="5">
  <Device name="Plex Server 1" product="Plex Media Server" productVersion="1.20.4.3517-ab5e1197c" platform="Linux" platformVersion="20.04.1 LTS (Focal Fossa)" device="PC" clientIdentifier="unique_id_123" createdAt="1429510140" lastSeenAt="1605500006" provides="server" owned="1" accessToken="faketoken" publicAddress="10.20.30.40" httpsRequired="0" synced="0" relay="0" dnsRebindingProtection="0" natLoopbackSupported="1" publicAddressMatches="1" presence="1">
    <Connection protocol="https" address="1.2.3.4" port="32400" uri="https://1-2-3-4.123456789001234567890.plex.direct:32400" local="1"/>
  </Device>
  <Device name="Plex Server 2" product="Plex Media Server" productVersion="1.20.4.3517-ab5e1197c" platform="Linux" platformVersion="20.04.1 LTS (Focal Fossa)" device="PC" clientIdentifier="unique_id_456" createdAt="1429510140" lastSeenAt="1605500006" provides="server" owned="1" accessToken="faketoken" publicAddress="10.20.30.40" httpsRequired="0" synced="0" relay="0" dnsRebindingProtection="0" natLoopbackSupported="1" publicAddressMatches="1" presence="{second_server_enabled}">
    <Connection protocol="https" address="4.3.2.1" port="32400" uri="https://4-3-2-1.123456789001234567890.plex.direct:32400" local="1"/>
  </Device>
  <Device name="Chrome" product="Plex Web" productVersion="4.46.2" platform="Chrome" platformVersion="14.0" device="OSX" clientIdentifier="plexweb_id" createdAt="1578086003" lastSeenAt="1605461664" provides="client,player,pubsub-player" owned="1" publicAddress="10.20.30.40" publicAddressMatches="1" presence="1" accessToken="faketoken">
    <Connection protocol="https" address="1.2.3.5" port="32400" uri="https://1-2-3-5.123456789001234567890.plex.direct:32400" local="1"/>
    <Connection protocol="https" address="10.20.30.40" port="35872" uri="https://10-20-30-40.123456789001234567890.plex.direct:35872" local="0"/>
  </Device>
  <Device name="AppleTV" product="Plex for Apple TV" productVersion="7.9" platform="tvOS" platformVersion="14.2" device="Apple TV" clientIdentifier="A10E4083-BF1A-4586-B884-C638A32D5285" createdAt="1447217545" lastSeenAt="1605495521" provides="client,player,pubsub-player,provider-playback" owned="1" publicAddress="10.20.30.40" publicAddressMatches="1" presence="0">
    <Connection protocol="http" address="1.2.3.6" port="32500" uri="http://1.2.3.6:32500" local="1"/>
  </Device>
  <Device name="jPhone" product="Plex for iOS" productVersion="7.9" platform="iOS" platformVersion="14.2" device="iPhone" clientIdentifier="CDB83941-F8C2-4B56-989E-F3EFD0165BC1" createdAt="1537584529" lastSeenAt="1605501046" provides="client,controller,sync-target,player,pubsub-player,provider-playback" owned="1" publicAddress="10.20.30.40" publicAddressMatches="1" presence="0">
    <Connection protocol="http" address="1.2.3.7" port="32500" uri="http://1.2.3.7:32500" local="1"/>
  </Device>
  XXXXXXXXX
  <Device name="SHIELD Android TV" product="Plex for Android (TV)" productVersion="8.8.2.21525" platform="Android" platformVersion="9" device="SHIELD Android TV" clientIdentifier="2f2a5ae50a45837c-com-plexapp-android" createdAt="1584850408" lastSeenAt="1605384938" provides="player,pubsub-player,controller" owned="1" publicAddress="10.20.30.40" publicAddressMatches="1" presence="1">
    <Connection protocol="http" address="1.2.3.11" port="32500" uri="http://1.2.3.11:32500" local="1"/>
  </Device>
</MediaContainer>"""
PLEXTV_RESOURCES = PLEXTV_RESOURCES_BASE.format(second_server_enabled=0)

# Plex libraries
PMS_LIBRARY_PAYLOAD = """<MediaContainer size="3" allowSync="0" art="/:/resources/library-art.png" content="" identifier="com.plexapp.plugins.library" mediaTagPrefix="/system/bundle/media/flags/" mediaTagVersion="1603922053" title1="Plex Library" title2="">
<Directory key="sections" title="Library Sections" />
<Directory key="recentlyAdded" title="Recently Added Content" />
<Directory key="onDeck" title="On Deck Content" />
</MediaContainer>"""

PMS_LIBRARY_SECTIONS_PAYLOAD = """<MediaContainer size="3" allowSync="0" identifier="com.plexapp.plugins.library" mediaTagPrefix="/system/bundle/media/flags/" mediaTagVersion="1603922053" title1="Plex Library">
<Directory allowSync="1" art="/:/resources/movie-fanart.jpg" composite="/library/sections/1/composite/1605409122" filters="1" refreshing="0" thumb="/:/resources/movie.png" key="1" type="movie" title="Movies" agent="com.plexapp.agents.imdb" scanner="Plex Movie Scanner" language="en" uuid="41a28495-035e-46b0-ac84-878f096614da" updatedAt="1602461679" createdAt="1429510140" scannedAt="1605409122" content="1" directory="1" contentChangedAt="116893155" hidden="0">
<Location id="1" path="/storage/movies" />
</Directory>
<Directory allowSync="1" art="/:/resources/show-fanart.jpg" composite="/library/sections/2/composite/1605461424" filters="1" refreshing="0" thumb="/:/resources/show.png" key="2" type="show" title="TV Shows" agent="com.plexapp.agents.thetvdb" scanner="Plex Series Scanner" language="en" uuid="80208576-f7d1-406d-b6d8-aa96a5362131" updatedAt="1602523323" createdAt="1429510140" scannedAt="1605461424" content="1" directory="1" contentChangedAt="117133678" hidden="0">
<Location id="2" path="/storage/tvshows" />
</Directory>
<Directory allowSync="1" art="/:/resources/artist-fanart.jpg" composite="/library/sections/3/composite/1605413685" filters="1" refreshing="0" thumb="/:/resources/artist.png" key="3" type="artist" title="Music" agent="tv.plex.agents.music" scanner="Plex Music" language="en" uuid="1eeace5d-4839-45e8-90b0-8d03b3375744" updatedAt="1602211102" createdAt="1430432959" scannedAt="1605413685" content="1" directory="1" contentChangedAt="116260421" hidden="1">
<Location id="3" path="/storage/music" />
</Directory>
</MediaContainer>"""

LIBRARY_MOVIES_SORT = """<MediaContainer size="8" allowSync="0" art="/:/resources/movie-fanart.jpg" content="secondary" identifier="com.plexapp.plugins.library" mediaTagPrefix="/system/bundle/media/flags/" mediaTagVersion="1603922053" thumb="/:/resources/video.png" title1="Movies" viewGroup="secondary" viewMode="65592">
<Directory default="asc" defaultDirection="asc" descKey="titleSort:desc" firstCharacterKey="/library/sections/1/firstCharacter" key="titleSort" title="Title" />
<Directory defaultDirection="desc" descKey="originallyAvailableAt:desc" key="originallyAvailableAt" title="Release Date" />
<Directory defaultDirection="desc" descKey="rating:desc" key="rating" title="Critic Rating" />
<Directory defaultDirection="desc" descKey="audienceRating:desc" key="audienceRating" title="Audience Rating" />
<Directory defaultDirection="desc" descKey="duration:desc" key="duration" title="Duration" />
<Directory defaultDirection="desc" descKey="addedAt:desc" key="addedAt" title="Date Added" />
<Directory defaultDirection="desc" descKey="lastViewedAt:desc" key="lastViewedAt" title="Date Viewed" />
<Directory defaultDirection="asc" descKey="mediaHeight:desc" key="mediaHeight" title="Resolution" />
</MediaContainer>"""

LIBRARY_TVSHOWS_SORT = """<MediaContainer size="6" allowSync="0" art="/:/resources/show-fanart.jpg" content="secondary" identifier="com.plexapp.plugins.library" mediaTagPrefix="/system/bundle/media/flags/" mediaTagVersion="1603922053" nocache="1" thumb="/:/resources/show.png" title1="TV Shows" viewGroup="secondary" viewMode="65592">
<Directory default="asc" defaultDirection="asc" descKey="titleSort:desc" firstCharacterKey="/library/sections/2/firstCharacter" key="titleSort" title="Title" />
<Directory defaultDirection="desc" descKey="originallyAvailableAt:desc" key="originallyAvailableAt" title="Release Date" />
<Directory defaultDirection="desc" descKey="rating:desc" key="rating" title="Critic Rating" />
<Directory defaultDirection="desc" descKey="unviewedLeafCount:desc" key="unviewedLeafCount" title="Unplayed" />
<Directory defaultDirection="desc" descKey="episode.addedAt:desc" key="episode.addedAt" title="Last Episode Date Added" />
<Directory defaultDirection="desc" descKey="lastViewedAt:desc" key="lastViewedAt" title="Date Viewed" />
</MediaContainer>"""

LIBRARY_MUSIC_SORT = """<MediaContainer size="5" allowSync="0" art="/:/resources/artist-fanart.jpg" content="secondary" identifier="com.plexapp.plugins.library" mediaTagPrefix="/system/bundle/media/flags/" mediaTagVersion="1603922053" nocache="1" thumb="/:/resources/artist.png" title1="Music" viewGroup="secondary" viewMode="65592">
<Directory default="asc" defaultDirection="asc" descKey="titleSort:desc" firstCharacterKey="/library/sections/3/firstCharacter" key="titleSort" title="Title" />
<Directory defaultDirection="desc" descKey="userRating:desc" key="userRating" title="Rating" />
<Directory defaultDirection="desc" descKey="addedAt:desc" key="addedAt" title="Date Added" />
<Directory defaultDirection="desc" descKey="lastViewedAt:desc" key="lastViewedAt" title="Date Played" />
<Directory defaultDirection="desc" descKey="viewCount:desc" key="viewCount" title="Plays" />
</MediaContainer>"""

# Playlists
PLAYLISTS_PAYLOAD = """<MediaContainer size="2">
<Playlist ratingKey="500" key="/playlists/500/items" guid="com.plexapp.agents.none://9a8f4a48-dd89-40e0-955b-286285350fdf" type="playlist" title="Playlist 1" summary="" smart="0" playlistType="video" composite="/playlists/500/composite/1597983847" viewCount="2" lastViewedAt="1568512403" duration="5054000" leafCount="1" addedAt="1505969338" updatedAt="1597983847">
</Playlist>
<Playlist ratingKey="501" key="/playlists/501/items" guid="com.plexapp.agents.none://9a8f4a48-dd89-40e0-955b-286285350fdf" type="playlist" title="Playlist 2" summary="" smart="0" playlistType="video" composite="/playlists/501/composite/1597983847" viewCount="5" lastViewedAt="1568512403" duration="5054000" leafCount="1" addedAt="1505969339" updatedAt="1597983847">
</Playlist>
</MediaContainer>"""

# Sonos speakers
SONOS_RESOURCES = """<MediaContainer size="3">
  <Player title="Speaker 1" machineIdentifier="RINCON_12345678901234561:1234567891" deviceClass="speaker" product="Sonos" platform="Sonos" platformVersion="56.0-76060" protocol="plex" protocolVersion="1" protocolCapabilities="timeline,playback,playqueues,provider-playback" lanIP="192.168.1.11"/>
  <Player title="Speaker 2 + 1" machineIdentifier="RINCON_12345678901234562:1234567892" deviceClass="speaker" product="Sonos" platform="Sonos" platformVersion="56.0-76060" protocol="plex" protocolVersion="1" protocolCapabilities="timeline,playback,playqueues,provider-playback" lanIP="192.168.1.12"/>
  <Player title="Speaker 3" machineIdentifier="RINCON_12345678901234563:1234567893" deviceClass="speaker" product="Sonos" platform="Sonos" platformVersion="56.0-76060" protocol="plex" protocolVersion="1" protocolCapabilities="timeline,playback,playqueues,provider-playback" lanIP="192.168.1.13"/>
</MediaContainer>
"""

# Playqueue creation
playqueue = ET.fromstring(TRACK_COMMON.format(key=100, track=1))  # nosec
for track_node in playqueue.iter("Track"):
    ET.SubElement(
        track_node, "Media", attrib=TRACK_MEDIA_AUDIO_ATTRIBS, playQueueItemID="98610"
    )
    ET.SubElement(track_node, "Part", attrib=TRACK_PART_AUDIO_ATTRIBS)
    ET.SubElement(track_node, "Stream", attrib=TRACK_STREAM_AUDIO_ATTRIBS)
mc_attribs = {
    **BASE_LIBRARY_ATTRIBS,
    "allowSync": "1",
    "librarySectionID": "3",
    "librarySectionTitle": "Music",
    "librarySectionUUID": "905308ec-5019-43d4-a449-75d2b9e42f93",
    "playQueueID": "11111",
    "playQueueSelectedItemID": "98610",
    "playQueueSelectedItemOffset": "0",
    "playQueueSelectedMetadataItemID": "100",
    "playQueueShuffled": "0",
    "playQueueSourceURI": "library://ba0c2140-c6ef-448a-9d1b-31020741d014/item//library/metadata/100",
    "playQueueTotalCount": "1",
    "playQueueVersion": "1",
}
PLAYQUEUE_CREATED = media_container(mc_attribs, playqueue)
