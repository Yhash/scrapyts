from scrapyts.parser.youtube import Youtube
from scrapyts.parser.playlist.youtube import YoutubePlaylist
from scrapyts.exceptions import DownloadError, ParseError

import sys
import re
import scrapyts.utils as utils
import scrapyts.helpers.youtube as ythelper


class CLIDownloader:
    """A commandline downloader for Youtube"""


    def _validate_url(self, url, as_list=False):
        list_id = ythelper.is_playlist_url(url)

        if list_id:
            return (url, 'playlist')
        elif ythelper.is_video_url(url):
            if as_list:
                list_id = ythelper.get_playlist_id(url)
                if list_id:
                    return (ythelper.create_playlist_url(list_id), 'playlist')
            else:
                return (url, 'video')

        return (url, None)

        
    def run(self, url, tag=None, first=None, last=None, display=False, download=True, add_index=False, as_list=False):
        tp = self._validate_url(url, as_list)
        url = tp[0]
        parser = tp[1]        

        total_download = 0 # total count of downloaded video or audio.

        if parser == 'playlist':
            if first is None:
                first = 1   # index of the video in a playlist
                
            if first < 1: raise ValueError('Invalid first index {}'.format(first))

            if last and last < first:
                raise ValueError('Invalid last index {}'.format(last))

            try:
                playlist = YoutubePlaylist(url)
            except:
                raise
            else:
                print('Playlist Title: {}\nPlaylist User:  {}'.format(self._replace_unicode(playlist.title), self._replace_unicode(playlist.user)))
                # TODO: Add e which is a reference to an exception.
                for index, thumbnail, url, title, owner, timestamp in playlist:
                    if first <= index:
                        if last and index > last:
                            break

                        # Some terminal does not support unicode character.
                        # For example in Windows 7 the unicode character \u2026
                        # ca not be displayed in the command prompt using print.
                        # http://www.youtube.com/watch?v=wqzlJb7hTsc&list=PLbpi6ZahtOH4gS5723HVtUgByxFtlG0u_
                        # Somewhere to look for...
                        # http://stackoverflow.com/questions/3263672/python-the-difference-between-sys-stdout-write-and-print
                        print("\nIndex: {}\nThumbnail: {}\nURL: {}\nTitle: {}\nOwner: {}\nTimestamp: {}".format(
                            index, thumbnail, url, self._replace_unicode(title), self._replace_unicode(owner), timestamp))

                        try:
                            if add_index == True:
                                tmp = len(str(playlist.vid_total))
                                prefix = '(%0{}d) '.format(tmp) % index
                                # self._download(url, tag=tag, display=display, download=download, prefix='(%05d) '%index)
                                self._download(url, tag=tag, display=display, download=download, prefix=prefix)
                            else:
                                self._download(url, tag=tag, display=display, download=download)
                        except (DownloadError, ParseError) as e:
                            # You should not raise an error unless
                            # you want CLIDownloader not to download
                            # the next video from the playlist
                            # raise
                            print(e, file=sys.stderr)
                        else:
                            total_download += 1 # increment total download
        elif parser == 'video':
            print()

            try:
                self._download(url, tag=tag, display=display, download=download)
            except (DownloadError, ParseError) as e:
                raise
            else:
                total_download += 1 # increment total download
        else:
            raise ParseError('Invalid url {}'.format(url))

        return total_download
    
    def _replace_unicode(self, text):
        if text is None: return text
        return text.encode('ascii', 'xmlcharrefreplace').decode('utf-8')


    def _download(self, url, tag=None, display=False, download=True, prefix=''):
        # Silently ignore first and last args.
        try:
            youtube = Youtube(url)
        except:
            raise
        else:
            try:
                media_info = youtube.parse()
            except:
                raise
            else:
                print("Title: {}\nVideo ID: {}".format(self._replace_unicode(youtube.title), youtube.video_id))

                if display == True:
                    self._display(media_info)


                if download == True:
                    media = None
                    
                    if tag is None:
                        for t in [17, 36, 5, 18, 43, 22]:
                            media = self._get_media(t, media_info)
                            if media: break
                    else:
                        media = self._get_media(tag, media_info)
                    
                    if media:
                        url = media.get('url')
                        filename = utils.create_fname(prefix + youtube.title, media.get('type'))
                        
                        try:
                            utils.download(filename, url)
                        except Exception as e:
                            raise DownloadError(e)
                    else:
                        raise ParseError("Could not found video or audio with itag={}".format(tag))


    def _get_media(self, tag, media_info):
        for media in media_info:
            itag = int(media.get('itag'))
            if itag == tag:
                return media
        return None


    def _display(self, media_info):
        print('-'*50)
        print(" %-4s\t%-15s\t%-15s\t%-15s" % ('TAG', 'TYPE', 'LENGTH', 'SIZE'))
        print('-'*50)
        for media in media_info:
            print(" %-4s\t%-15s\t%-15s\t%-15s" % (
                media['itag'],
                media['type'],
                media['len'],
                media['size']
            ))


if __name__ == '__main__':
    # Blood Ransom Official International Movie Trailer 
    # Starring Anne Curtis and Alexander Dreymon 2014
    # url = "https://www.youtube.com/watch?v=CUKcSzITIKg"
    #url = "https://www.youtube.com/watch?v=pVY-2Fqdum0"     # FlipTop - Tipsy D vs Sinio
    # url = "https://www.youtube.com/watch?v=et_MRWnEuz8"     # DANIEL PADILLA - Simpleng Tulad Mo (Official Music Video)
    #url = "https://www.youtube.com/watch?v=WI5yHAmcH2g&list=PLeGljrPoR_9BKLLE7XP9TGbjM-Xb1AwDz"     # UFO News: UFO Over Hong Kong Protests. (Smoking Gun Footage) 
    url = "https://www.youtube.com/watch?v=7lhXOgJ8ahA&index=2&list=PLeGljrPoR_9BKLLE7XP9TGbjM-Xb1AwDz"     # First iPhone 6 sold in Perth is dropped by kid during an interview

    #https://www.youtube.com/channel/UC-9-kyTW8ZkZNDHQJ6FgpwQ/featured

    # user home page can have an embeded video. For example...
    # https://www.youtube.com/user/phpacademy

    # https://www.youtube.com/user/phpacademy/playlists - It can contain a load more button

    # https://www.youtube.com/playlist?list=PLfdtiltiRHWGr4dOMCX2ZQv77jVY03zBv - Playlist page
    # https://www.youtube.com/watch?v=e2MLepOlT9Q&list=PLfdtiltiRHWGr4dOMCX2ZQv77jVY03zBv&index=1
    # https://www.youtube.com/watch?v=e2MLepOlT9Q&list=PLfdtiltiRHWGr4dOMCX2ZQv77jVY03zBv&index=1

    # url = "https://www.youtube.com/playlist?list=PLfdtiltiRHWGr4dOMCX2ZQv77jVY03zBv"
    # Top Hip Hop Music Tracks
    # url = "http://www.youtube.com/playlist?list=PLH6pfBXQXHECUaIU3bu9rjG2L6Uhl5A2q"
    # Popular Music Videos 
    # url = "http://www.youtube.com/playlist?list=PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI"
    # url = 'https://www.github.com/'

    # PHP Object Oriented Programming (OOP)
    # url = 'http://www.youtube.com/playlist?list=PLfdtiltiRHWF0RicJb20da8nECQ1jFvla'
    
    downloader = CLIDownloader()
    try:
        downloader.run(url, tag=18, first=1, last=2, display=True, as_list=True)
    except (ValueError, DownloadError, ParseError) as e:
        print(e, file=sys.stderr)