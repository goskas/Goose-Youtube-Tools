import urllib.request
import datetime
from ura import *

def get_playlist_duration_from_URL(url, converse=False):
    """
    Gets playlist duration from playlist URL.
    Playlist must be public or unlisted.
    It only works correctly for playlists with less than 100 videos.*
    It does zero error checking.
    It does 1 http request to YouTube servers.

    * If there are more than 100 videos, not all show up on the first
      page (they are under 'Show more' button). In that case, this function
      returns the duration of first 100 videos.
    """
    html = urllib.request.urlopen(url).read()
    splited = str(html).split('timestamp')[1:]
    extracted = []
    for i in range(len(splited)):
        extracted += [splited[i].split('</span>')[0].split('>')[-1]]
        
    print('Found', len(splited), 'videos.')
    if len(splited) > 98:
        string = 'This program usually only finds first 100 videos on a playlist. '
        string += 'This playlist my be affected by this.'
        print(string)
    sekundeVseh = list(map(str_to_seconds, extracted))
    skupaj = sum(sekundeVseh)
    dhms = seconds_to_tuple(skupaj)
    print('Combined duration is', dhms[0], 'day(s)', dhms[1], 'hours(s)',
          dhms[2], 'minute(s)', dhms[3], 'second(s)')
    if converse:
        dhms = seconds_to_tuple(max(sekundeVseh))
        print('    Longest video is', dhms[0], 'day(s)', dhms[1], 'hours(s)',
              dhms[2], 'minute(s)', dhms[3], 'second(s)')
        dhms = seconds_to_tuple(min(sekundeVseh))
        print('   Shortest video is', dhms[0], 'day(s)', dhms[1], 'hours(s)',
              dhms[2], 'minute(s)', dhms[3], 'second(s)')
    return len(splited), skupaj

