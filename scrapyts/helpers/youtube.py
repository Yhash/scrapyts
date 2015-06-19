# Most of the functions here assumes that the url
# pass as an argument is a valid youtube url.
import re


def create_playlist_url(list_id):
    return "http://www.youtube.com/playlist?list=" + list_id


def get_playlist_id(url):
    regexobj = re.compile(r'(?<=[&?])list=(?P<list_id>[^&?]+)')
    m = regexobj.search(url)

    if m:
        list_id = m.group('list_id')
        list_id_len = len(list_id)

        # (24) http://www.youtube.com/playlist?list=LLIWZ1_W5BqsvW9fm1cYFPpQ
        # (34) http://www.youtube.com/playlist?list=PLfdtiltiRHWFfn_e2wDRPPG3k_KDNFENE
        # Is there anymore valid length? I really don't know. Hmmm...
        if list_id_len == 24 or list_id_len == 34:
            return list_id

    return None


def get_video_id(url):
    regexobj = re.compile(r'(?<=[&?])v=(?P<video_id>[\w\-]{11})(?=&|$)')
    m = regexobj.search(url)

    if m:
        return m.group('video_id')
    else:
        return None


def is_playlist_url(url):
    regexobj = re.compile(r'^https?://www\.youtube\.com/playlist\?[_a-zA-Z]\w*=[\w\-]+(&[_a-zA-Z]\w*=[\w\-]+)*$')
    m = regexobj.match(url)
    
    if m:
        list_id = get_playlist_id(url)
        if list_id: return list_id

    return False


def is_video_url(url):
    regexobj = re.compile(r'^https?://www\.youtube\.com/watch\?[_a-zA-Z]\w*=[\w\-]+(&[_a-zA-Z]\w*=[\w\-]+)*$')
    m = regexobj.match(url)

    if m:
        video_id = get_video_id(url)
        if video_id:
            return video_id

    return False

def add_hl_to_url(url):
    """ A function that adds or change language query to english in the given url. """
    # Note: Used it before is_playlist_url() or is_video_url().
    # Why we need this? For consistency when scraping the information embeded on the page.
    # Because youtube support different languages for the same page and it makes it hard
    # to scrap it if we will not force youtube to just send to us a specific page.
    return re.sub(r'&hl=[^&]+', '', url) + '&hl=en'