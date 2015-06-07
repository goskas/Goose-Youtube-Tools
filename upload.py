#!/usr/bin/python

import http.client
import httplib2
import os
import random
import sys
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
    http.client.IncompleteRead, http.client.ImproperConnectionState,
    http.client.CannotSendRequest, http.client.CannotSendHeader,
    http.client.ResponseNotReady, http.client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google Developers Console at
# https://console.developers.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#     https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#     https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "../PlaylistDuration/client_secrets.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

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

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


def get_authenticated_service(args):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
        scope=' '.join([YOUTUBE_UPLOAD_SCOPE, YOUTUBE_READONLY_SCOPE]),
        message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    print ('getting authenticated', args)
    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()))

def initialize_upload(youtube, options):
    tags = None
    if options.keywords:
        tags = options.keywords.split(",")

    body=dict(
        snippet=dict(
            title=options.title,
            description=options.description,
            tags=tags,
            categoryId=options.category
        ),
        status=dict(
            privacyStatus=options.privacyStatus
        )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )

    resumable_upload(insert_request)

def initialize_upload_simplified(youtube, filename, body, chunksize):
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(filename, 
                                   chunksize=chunksize,
                                   resumable=True)
    )
    resumable_upload(insert_request)

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print ("Uploading file...")
            status, response = insert_request.next_chunk()
            if 'id' in response:
                print ("Video id '%s' was successfully uploaded." % response['id'])
            else:
                exit("The upload failed with an unexpected response: %s" % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                                                                         e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = ("A retriable error occurred: %s" % e)

        if error is not None:
            print (error)
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print ("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)


import os
import datetime
import yaml
import youtubeAPIinterface

def get_database_of_videos(youtube):
    uploaded = youtubeAPIinterface.get_uploaded_playlist(youtube)
    all_videos = youtubeAPIinterface.get_all_videos_in_playlist(youtube, uploaded)
    extracted = [
                 [
                  i['snippet']['title'], 
                  i['snippet']['description']
                 ] for i in all_videos
                ]

def size_to_units(size):
    '''
    WiP : Ni še čist OK. Returna 1.0 namesto 1.000
    '''
    units = list(' kMGTP')
    for i in range(len(units)):
        if size < 1024:
            return '%s' % float('%.4g' % size) + ' ' + units[i] + 'B'
        size /= 1024
    return '%s' % float('%.4g' % size) + ' units_overload'

def upload_folder(youtube, folder, other):
    """
    For now other is hardcoded here. Once in future, it will be costumizable.

    WiP - Readable size še ni čist OK. 1 zaokroži v 1.0 in ne 1.000. 
    """
    for root, dirs, files in os.walk(folder):
        if 'Frizer' not in root: continue
        for datoteka in files:
            if datoteka[-4:] != '.MP4': continue
            stats = os.stat(root + '/' + datoteka)
            description = dict([])
            description['size'] = stats.st_size
            description['Readable_size'] = size_to_units(stats.st_size)
            description['access_time'] = stats.st_atime
            description['modified_time'] = stats.st_mtime
            description['created_time'] = stats.st_ctime
            description['Readable_access_time'] = datetime.datetime.fromtimestamp(stats.st_atime).strftime("%Y-%m-%d %H:%M:%S")
            description['Readable_modified_time'] = datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            description['Readable_created_time'] = datetime.datetime.fromtimestamp(stats.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            description['filename'] = datoteka
            description['Main_folder'] = folder
            description['subfolders'] = root.strip(folder).replace('\\', '/')
            description['computername'] = os.environ['COMPUTERNAME']
            description['userdomain'] = os.environ['USERDOMAIN']
            #print(yaml.dump(description, default_flow_style=False))
            #print(datoteka, description['Readable_size'])
            #description = yaml.dump(description, default_flow_style=False)
            body=dict(
                snippet=dict(
                    title=description['subfolders'] + ' - ' + description['filename'],
                    description=yaml.dump(description, default_flow_style=False),
                    tags='backup',
                    categoryId=19
                ),
                status=dict(
                    privacyStatus='private'
                )
            )
            initialize_upload_simplified(youtube,
                                        root + '/' + datoteka,
                                        body, 1024**2)


if False:
    youtube = get_authenticated_service("Not providing this because I don't know what this does")
    upload_folder(youtube, 'Q:/Workspace/Vlog', 0)
    #get_database_of_videos(youtube)






if __name__ == '__main__' and 1:
    argparser.add_argument("--file", 
        required=True, 
        help="Video file to upload")
    argparser.add_argument("--title", 
        help="Video title",
        default="Test Title")
    argparser.add_argument("--description", 
        help="Video description",
        default="Test Description")
    argparser.add_argument("--category", 
        default="22",
        help="Numeric video category. " +
            "See https://developers.google.com/youtube/v3/docs/videoCategories/list")
    argparser.add_argument("--keywords", 
        help="Video keywords, comma separated",
        default="")
    argparser.add_argument("--privacyStatus", 
        choices=VALID_PRIVACY_STATUSES,
        default=VALID_PRIVACY_STATUSES[0],
        help="Video privacy status.")
    args = argparser.parse_args()

    if not os.path.exists(args.file):
        exit("Please specify a valid file using the --file= parameter.")
    print(argparser)
    print(args)
    print(args.keywords)
    youtube = get_authenticated_service(args)
    try:
        initialize_upload(youtube, args)
    except HttpError as e:
        print ("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))