from bs4 import BeautifulSoup
from scrapyts.exceptions import (
                                    ParseError,
                                    DownloadError
                                )

import scrapyts.utils as utils
import json
import re


class YoutubePlaylist:
    """Class that represent a Youtube Playlist."""


    def __init__(self, url):
        self.url = url

        try:
            html = utils.get_html(url)
        except:
            raise DownloadError("Could not download the playlist page {}".format(self.url))
        else:
            # Does BeautifulSoup can raise an error?
            # Maybe if it doesn't find the right parser?
            self._soup = BeautifulSoup(html, features="lxml")
            self.title = self._parse_title()
            self.user  = self._parse_user()
            self.vid_total = self._parse_vid_total()


    def _parse_vid_total(self):
        try:
            # <ul class="pl-header-details">
            #     <li></li>
            #     <li></li>    <-- Total of videos in the playlist. ex: 500 videos
            #     <li></li>
            # </ul>
            vid_total = self._soup.find("ul", class_="pl-header-details").contents[1].string
        except:
            pass # Maybe IndexError?
        else:
            m = re.match(r'(?P<total>\d+)\s+', vid_total)
            if m:
                return int(m.group('total'))

        raise ParseError("Could not find the total of videos in the playlist.")


    def _parse_title(self):
        try:
            playlist_title = self._soup.find("h1", class_="pl-header-title").string.strip()
        except:
            raise ParseError("Could not find the title of the playlist {}".format(self.url))
        else:
            return playlist_title


    def _parse_user(self):
        try:
            playlist_user = self._soup.find(class_="pl-header-details").li.a.string.strip()
        except:
            raise ParseError("Could not find the name of the user")
        else:
            return playlist_user


    def _parse_vid_thumbnail_url(self, pl_video):
        # This function expect a bs4 object including BeautifulSoup, Tag or NavigableString.
        try:
            vid_thumbnail_url = pl_video.find(class_="pl-video-thumbnail").find("img").get('src').strip()
        except:
            # Whatever exception occured, just raise ParseError.
            raise ParseError("Could not find the thumbnail")
        else:
            return vid_thumbnail_url


    def _parse_vid_title(self, pl_video):
        try:
            vid_title = pl_video.find(class_="pl-video-title").a.string.strip()
        except:
            raise ParseError("Could not find the title of the video.")
        else:
            return vid_title


    def _parse_vid_url(self, pl_video):
        try:
            vid_url = pl_video.find(class_="pl-video-title").a.get('href').strip()
        except:
            raise ParseError("Could not find the url of the video.")
        else:
            return vid_url


    def _parse_vid_owner(self, pl_video):
        try:
            vid_owner = pl_video.find(class_="pl-video-owner").a.string.strip()
        except:
            raise ParseError("Could not find the owner of the video.")
        else:
            return vid_owner


    def _parse_vid_timestamp(self, pl_video):
        try:
            vid_timestamp = pl_video.find(class_="timestamp").string.strip()
        except:
            raise ParseError("Could not find the timestamp of the video.")
        else:
            return vid_timestamp


    def __iter__(self):
        return self._parse()


    def _parse(self, soup=None, prev_index=0):
        # raise ParseError or DownloadError
        if soup is None: soup = self._soup

        pl_videos = soup.find_all(class_="pl-video")
        #print(pl_videos)

        for index, pl_video in enumerate(pl_videos):
            # If a video is deleted the owner and timestamp are
            # removed by youtube. While the thumbnail is replace
            # by the default image, http://s.ytimg.com/yts/img/no_thumbnail-vfl4t3-4R.jpg.
            # It is also true for a video or videos in a playlist that is mark as private.
            #
            # Tuple Pattern: (vid_index, vid_thumbnail_url, vid_url, vid_title, vid_owner, vid_timestamp)
            
            vid_index = index + 1 + prev_index

            try:
                vid_thumbnail_url = self._parse_vid_thumbnail_url(pl_video)
                #print(vid_thumbnail_url)
            except:
                # raise
                vid_thumbnail_url = None
            else:
                vid_thumbnail_url = self.fix_url(vid_thumbnail_url)

            try:
                vid_url = self._parse_vid_url(pl_video)
                #print(vid_url)
            except:
                # raise
                vid_url = None
            else:
                vid_url = self.fix_url(vid_url)

            try:
                #        [Deleted Video]     
                vid_title = self._parse_vid_title(pl_video)
                #print(vid_title)
            except:
                vid_title = None

            try:
                vid_owner = self._parse_vid_owner(pl_video)
                #print(vid_owner)
            except:
                vid_owner = None

            try:
                vid_timestamp = self._parse_vid_timestamp(pl_video)
                #print(vid_timestamp)
            except:
                vid_timestamp = None
            
            #print("{} {} {} {} {} {}".format(vid_index, vid_thumbnail_url, vid_url, vid_title, vid_owner, vid_timestamp))
            video_info = (vid_index, vid_thumbnail_url, vid_url, vid_title, vid_owner, vid_timestamp)
            yield (vid_index, vid_thumbnail_url, vid_url, vid_title, vid_owner, vid_timestamp)

        try:
            load_more_url = soup.find(class_="load-more-button").get('data-uix-load-more-href').strip()
        except Exception as e:
            pass # need to fix this...
        else:
            next_url = self.fix_url(load_more_url)
            #print(next_url)
            #print(type(next_url))

            try:
                html = utils.get_html(next_url)
            except:
                # raise DownloadError("Could not download the continuation url {}".format(next_url))
                pass
            else:
                # need to validate this...
                # I will raise an error here but part of tuple
                json_dict = json.loads(html)
                
                html = ""
                for text in json_dict.values():
                    html += text

                sopas = BeautifulSoup(html, features="lxml")

                for video in self._parse(soup=sopas, prev_index=vid_index):
                    yield video # tupple


    def fix_url(self, url):
        # A simple url validation.
        # Should I improve it?
        prefix = '' # assume that the url starts with http or https
        if url.startswith('//'):
            prefix = 'http:'
        elif url.startswith('/'):
            prefix = 'http://www.youtube.com'

        return prefix + url


if __name__ == '__main__':
    # Laravel
    # url = "https://www.youtube.com/playlist?list=PLfdtiltiRHWGr4dOMCX2ZQv77jVY03zBv"

    # Top Hip Hop Music Tracks
    url = "http://www.youtube.com/playlist?list=PLH6pfBXQXHECUaIU3bu9rjG2L6Uhl5A2q"

    # Popular Music Videos 
    # url = "http://www.youtube.com/playlist?list=PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI"


    import sys
    from scrapyts.parser.youtube import Youtube

    
    try:
        playlist = YoutubePlaylist(url)
    except (DownloadError, ParseError) as e:
        print(e, file=sys.stderr)
    else:
        print("Playlist: {}".format(playlist.title))
        print("Owner:    {}".format(playlist.user))
        print("URL:      {}".format(playlist.url))

        for index, thumbnail, url, title, owner, timestamp in playlist:
            # The index of the video from the playlist
            if index > 2: break

            print("\n")

            try:
                youtube = Youtube(url)
            except (DownloadError, ParseError) as e:
                print(e, file=sys.stderr)
            else:
                try:
                    media_info = youtube.parse()
                except (DownloadError, ParseError) as e:
                    print(e, file=sys.stderr)
                else:
                    print("Index: {}\nThumbnail: {}\nURL: {}\nTitle: {}\nOwner: {}\nTimestamp: {}".format(
                            index, thumbnail, url, title, owner, timestamp))

                    for media in media_info:
                        if media.get('itag') == '18':
                            url = media.get('url')
                            filename = utils.create_fname(youtube.title, media.get('type'))
                            utils.download(url, filename)