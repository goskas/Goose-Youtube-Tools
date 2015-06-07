from youtubeAPIinterface import *
import datetime
import yaml

folder = 'PlaylistBackups/'

def beautify_playlist_item(item, converse):
    try: 
        item['snippet'].pop('thumbnails')
    except: 
        if converse and not(item['snippet']['title'] == 'Deleted video' or
                item['snippet']['title'] == 'Private video'):
            print('Could not remove thumbnails of', item)
    
    try: 
        item.pop('id')
        item['snippet'].pop('playlistId')
    except: 
        if converse:
            print('Could not remove [Playlist] id of', item)
    
    try: 
        item['snippet'].pop('channelId')
        item['snippet'].pop('channelTitle')
    except: 
        if converse:
            print('Could not remove channelInfo of', item)
    
    try: 
        item.pop('kind')
    except: 
        if converse:
            print('Could not remove "kind" of', item)

    try: 
        item['snippet'].pop('resourceId')
    except: 
        if converse:
            print('Could not remove "kind" of', item)
    return item

if __name__ == '__main__':
    youtube = start_youtube(YOUTUBE_READONLY_SCOPE)
    all_playlists = get_all_playlists_my_channel(youtube)
    beautify = True ## Removes unvanted things.
    converse = True ## Printd stuff. Not implemented yet.
    for name, ID in all_playlists.items():
        print('Started', name)
        f = open(folder + name + \
            datetime.datetime.now().strftime("%Y-%m-%d__%H-%M-%S") + \
            '.txt', 'w')
        this_playlist_items = get_all_videos_in_playlist(youtube, ID,
                                part='id, snippet, contentDetails')
        for i in range(len(this_playlist_items)):
            if beautify:
                this_playlist_items[i] = beautify_playlist_item(this_playlist_items[i], converse=converse)
        f.write(yaml.dump(this_playlist_items, default_flow_style=False))
        print('Done', name, 'with', len(this_playlist_items), 'items.')
        f.close()