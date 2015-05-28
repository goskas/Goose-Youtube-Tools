#!/usr/bin/python

import httplib2
import os
import sys

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google Developers Console at
# https://console.developers.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                         CLIENT_SECRETS_FILE))

# This OAuth 2.0 access scope allows for read-only access to the authenticated
# user's account, but not other types of account access.
YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def start_youtube():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
        message=MISSING_CLIENT_SECRETS_MESSAGE,
        scope=YOUTUBE_READONLY_SCOPE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flags = argparser.parse_args()
        credentials = run_flow(flow, storage, flags)

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()))
    return youtube

#################################################################
###                  END OF TUTORIAL COPY                     ###
#################################################################

from  ura import *

# Lepši način je z list next.
# Torej namesto .list, greš .list_next(isto)
# glej python primer tukaj: https://developers.google.com/youtube/v3/docs/playlistItems/list
# Ki je verjetno iz kje je ta fajl nastal. Tako da lahko gledaš tudi below.


def get_video_duration(youtube, videoID, part='id, contentDetails'):
    return get_video_details(youtube,
                             videoID,
                             part=part
                            )['contentDetails']['duration']

def get_playlist_durations(youtube, playlistID):
    durations = []
    all_videos = get_all_videos_in_playlist(youtube,
                                            playlistID,
                                            part='snippet,id')
    for video in all_videos:
        #print('video in get_playlist_duration', video)
        duration = get_video_duration(youtube,
                                         video['snippet']['resourceId']['videoId'])
        durations += [duration_to_seconds(duration)]
    return durations

def get_playlist_duration(youtube, playlistID):
    d = get_playlist_durations(youtube, playlistID)
    return len(d), sum(d)

def get_video_details(youtube, videoID, part='id, snippet, contentDetails'):
    video = youtube.videos().list(id=videoID,
                                  part=part).execute()
    return video['items'][0]

def get_all_videos_in_playlist(youtube, playlistID, part='id, snippet'):
    pageToken = ''
    all_videos = []
    while True:
        ### ADD maxResults=50 v request
        list_of_videos = youtube.playlistItems().list(part=part,
                                                      playlistId=playlistID,
                                                      pageToken=pageToken).execute()

        for video in list_of_videos['items']:
            all_videos += [video]
        if 'nextPageToken' in list_of_videos:
            pageToken = list_of_videos['nextPageToken']
        else:
            break
    return all_videos
  

def get_all_playlists_my_channel(youtube, what_to_print):
    """
    Finds all playlists on my channel excluding automatically created ones
    like: liked videos, watch later, favourites, history, uploaded
    This is all so far.
    """
    pageToken = ''
    while True:
        ### ADD maxResults=50 v request
        list_of_playlists = youtube.playlists().list(part='id, snippet',
                                                     mine=True,
                                                     pageToken=pageToken,
                                                     maxResults=50).execute()
        for playlist in list_of_playlists['items']:
            print(playlist['snippet']['title'], playlist['id'])
        if 'nextPageToken' in list_of_playlists:
            pageToken = list_of_playlists['nextPageToken']
        else:
            break

#get_all_playlists_my_channel(youtube, 'a')
#for v in get_all_videos_in_playlist(youtube, 'FLp2jqHIbB9kavpnjrOo92eA'):
#    print(v['snippet']['title'], v['id'])

if False:
    # Retrieve the contentDetails part of the channel resource for the
    # authenticated user's channel.
    channels_response = youtube.channels().list(
      mine=True,
      part="contentDetails"
    ).execute()

    print(channels_response["items"])

            
                
    for channel in channels_response["items"]:
        # From the API response, extract the playlist ID that identifies the list
        # of videos uploaded to the authenticated user's channel.
        print(channel)
        print()
        
        uploads_list_id = channel["contentDetails"]["relatedPlaylists"]["watchLater"]

        print ("Videos in list %s" % uploads_list_id)

        # Retrieve the list of videos uploaded to the authenticated user's channel.
        playlistitems_list_request = youtube.playlistItems().list(
          playlistId=uploads_list_id,
          part="snippet",
          maxResults=50
        )

        while playlistitems_list_request:
          playlistitems_list_response = playlistitems_list_request.execute()

          # Print information about each video.
          for playlist_item in playlistitems_list_response["items"]:
            title = playlist_item["snippet"]["title"]
            video_id = playlist_item["snippet"]["resourceId"]["videoId"]
            print ("%s (%s)" % (title, video_id))

          playlistitems_list_request = youtube.playlistItems().list_next(
            playlistitems_list_request, playlistitems_list_response)

        print()
