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

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def start_youtube(scope):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
        message=MISSING_CLIENT_SECRETS_MESSAGE,
        scope=scope)

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
    return get_video_details(
        youtube,
        videoID,
        part=part
    )['contentDetails']['duration']

def get_playlist_durations(youtube, playlistID):
    durations = []
    all_videos = get_all_videos_in_playlist(
        youtube,
        playlistID,
        part='snippet,id'
    )
    
    for video in all_videos:
        #print('video in get_playlist_duration', video)
        duration = get_video_duration(
            youtube,
            video['snippet']['resourceId']['videoId']
        )
        durations += [duration_to_seconds(duration)]
    return durations

def get_playlist_duration(youtube, playlistID):
    d = get_playlist_durations(youtube, playlistID)
    return len(d), sum(d)

def get_video_details(youtube, videoID, part='id, snippet, contentDetails'):
    video = youtube.videos().list(
        id=videoID,
        part=part
    ).execute()
    if len(video['items']) == 0:
        print('Found no videos vi ID:', videoID)
        print('Returning default')
        videoID = 'ySU703VXSNY'
        return get_video_details(youtube, videoID, part)
    return video['items'][0]

def get_all_videos_in_playlist(youtube, playlistID, part='id, snippet'):
    pageToken = ''
    all_videos = []
    while True:
        ### ADD maxResults=50 v request
        list_of_videos = youtube.playlistItems().list(
            part=part,
            playlistId=playlistID,
            pageToken=pageToken
        ).execute()

        for video in list_of_videos['items']:
            all_videos += [video]
        if 'nextPageToken' in list_of_videos:
            pageToken = list_of_videos['nextPageToken']
        else:
            break
    return all_videos
  

def get_all_playlists_my_channel(youtube):
    """
    Finds all playlists on my channel excluding automatically created ones
    like: liked videos, watch later, favourites, history, uploaded
    This is all so far.
    """
    pageToken = ''
    ret = dict()
    while True:
        ### ADD maxResults=50 v request
        list_of_playlists = youtube.playlists().list(
            part='id, snippet',
            mine=True,
            pageToken=pageToken,
            maxResults=50).execute()
        for playlist in list_of_playlists['items']:
            ret[playlist['snippet']['title']] = playlist['id']
        if 'nextPageToken' in list_of_playlists:
            pageToken = list_of_playlists['nextPageToken']
        else:
            break
    ret2 = youtube.channels().list(
        mine=True,
        part="contentDetails"
    ).execute()['items'][0]['contentDetails']['relatedPlaylists']
    for key, item in ret2.items():
        if key in ret:
            print("key already in ret", key, item, ret[key])
        ret[key] = item
    return ret

def get_ALL_playlists_my_channel(youtube):
    ''' Obsolete -- use get_all_playlists_my_channel '''
    playlists = youtube.channels().list(
        mine=True,
        part="contentDetails"
    ).execute()['items'][0]['contentDetails']['relatedPlaylists']
    print(playlists)

def get_uploaded_playlist(youtube):
    uploadedID = youtube.channels().list(
        mine=True,
        part="contentDetails"
    ).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    #print(uploadedID)
    return uploadedID

import yaml
if __name__ == '__main__':
    """
    Get all channels I am subscribed to.
    """

    youtube = start_youtube(YOUTUBE_READONLY_SCOPE)

    subscriptions = youtube.subscriptions().list(
        mine=True,
        part='id,snippet',
        maxResults = 50,
        ).execute()['items']
    for i, s in enumerate(subscriptions):
        subscriptions[i]['snippet'].pop('description')
        subscriptions[i]['snippet'].pop('thumbnails')
        subscriptions[i]['snippet']['resourceId'].pop('kind')
        subscriptions[i].pop('kind')
        subscriptions[i]['snippet'].pop('channelId') # to je moj channelID
    print()
    print (yaml.dump(subscriptions))

    """
    WiP - s searchom se verjetno da OK narest, da dobiš seznam videov.
    Edin ne vem kako dobro zna upoštevati razliko med published in created datomom.
    In kaj je kateri in tako.
    Pri ordering je - date = date created
    Pol maš pa še published before/after parametra.
    """

if __name__ == '__main__' and False:
    """
    Trying to get titles of deleted videos.
    """
    youtube = start_youtube(YOUTUBE_READONLY_SCOPE)
    playlistID = 'WLp2jqHIbB9kavpnjrOo92eA'
    all_videos = get_all_videos_in_playlist(youtube, playlistID)
    for i, video in enumerate(all_videos):
        try: video['snippet'].pop('thumbnails')
        except: print('Couldnt print', i)
        print(i, video['snippet'])


if __name__ == '__main__' and False:
    youtube = start_youtube(YOUTUBE_READONLY_SCOPE)
    uploaded = get_uploaded_playlist(youtube)
    all_videos = get_all_videos_in_playlist(youtube, uploaded)
    for video in all_videos:
        a = get_video_details(youtube, video['snippet']['resourceId']['videoId'], 'snippet,status')
        #print(video['snippet']['resourceId']['videoId'], a['snippet']["categoryId"], a['status']["privacyStatus"][:6], a['status']["publicStatsViewable"])
        if int(a['snippet']["categoryId"]) not in [1, 17, 19, 20, 22, 23, 24, 27, 28]:
            print (a['snippet']["categoryId"])
            print(video['snippet']['resourceId']['videoId'], a['snippet']["categoryId"], a['status']["privacyStatus"][:6], a['status']["publicStatsViewable"])
        continue
        try:
            print(video)
            #print(video['snippet']['title'], '\t', video['snippet']['description'])
        except:
            print()
            print('   '.join(video.keys()))
            print('--------------------------------------------------------------------')
            print(video['snippet']['resourceId'])

if False:
    # Retrieve the contentDetails part of the channel resource for the
    # authenticated user's channel.
    channels_response = youtube.channels().list(
        mine=True,
        part="contentDetails"
    ).execute()
        
    for channel in channels_response["items"]:
        uploads_list_id = channel["contentDetails"]["relatedPlaylists"]["watchLater"]

        playlistitems_list_request = youtube.playlistItems().list(
          playlistId=uploads_list_id,
          part="snippet",
          maxResults=50
        )
        while playlistitems_list_request:
          playlistitems_list_response = playlistitems_list_request.execute()
          for playlist_item in playlistitems_list_response["items"]:
            pass #do stuff

          playlistitems_list_request = youtube.playlistItems().list_next(
            playlistitems_list_request, playlistitems_list_response)

        print()
