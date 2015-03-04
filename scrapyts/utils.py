from clint.textui import progress
from scrapyts.exceptions import DownloadError

import re
import sys
import os.path
import certifi
import urllib3


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}

# http://stackoverflow.com/questions/9384474/in-chrome-how-many-redirects-are-too-many
retry = urllib3.Retry(300, redirect=20)
timeout = urllib3.Timeout(connect=3.05, read=10)
http = urllib3.PoolManager(headers=headers,
                           timeout=timeout, 
                           cert_reqs='CERT_REQUIRED', 
                           ca_certs=certifi.where())


def get_html(url):
    try:
        response = http.request('GET', url, preload_content=True, retries=retry)
    except:
        raise
    else:
        if response.status == 200:
            raw_data = response.data
            content_type = response.headers.get('content-type', None)

            if content_type:
                # RFC 2616
                # Format:
                # media-type     = type "/" subtype *( ";" parameter )
                # type           = token
                # subtype        = token
                # type, subtype and param names are case-insensitive
                # while param values might or might not be case-sensitive
                if content_type.startswith("text/html"):
                    # <meta charset="character_set">
                    p = re.compile(br'<meta\s+charset=(["\'])(?P<charset>.+?)\1', re.IGNORECASE)
                    m = p.search(raw_data)

                    if m:
                        encoding = m.group('charset').strip()

                        try:
                            html = raw_data.decode(encoding)
                        except:
                            pass # If this failed then try the next procedure.
                        else:
                            return html
                    else:
                        # <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
                        p = re.compile(br'<meta\s+http-equiv=(["\'])Content-Type\1\s+content=(["\'])text/html;\s?charset=(?P<charset>.+?)\2', re.IGNORECASE)
                        m = p.search(raw_data)

                        if m:
                            encoding = m.group('charset').strip()

                            try:
                                html = raw_data.decode(encoding)
                            except:
                                pass # If this failed then try the next procedure.
                            else:
                                return html


                elif content_type.startswith("application/xml"):
                    pass #TODO: Add support for xml?


                # Try to find out the encoding using the content-type.
                p = re.compile(r'charset=(?P<charset>[^;]+)')
                m = p.search(content_type)
                if m:
                    try:
                        html = raw_data.decode(m.group('charset'))
                    except:
                        pass # If this failed then try the next procedure.
                    else:
                        return html

            # If Content-Type not found then try another way.
            # Maybe I will use chardet module for this task.
            # For now I will just decode it using utf-8.

            return raw_data.decode('utf-8')

    raise DownloadError("Failed to download the page {}".format(url))


def get_headers(url, redirect=False):
    """This function will return the HTTP response headers of a given url or raise an theme-custom if an error occurred.

    Arguments:
        url: The url of web page to be downloaded.
        redirect: Set to True to allow redirection. Default is False.

    Returns:
        Returns a dictionary of HTTP headers.
    """

    if redirect == True:
        redirect = 20 # Firefox && Chrome

    retry = urllib3.Retry(300, redirect=redirect)

    try:
        response = http.request('HEAD', url, retries=retry)
    except:
        raise
    else:
        if response.status == 200: # OK
            return response.headers # I think this is compatible to Python dict. So I will just return it.
        else:
            response.release_conn()

    raise DownloadError("Failed to download the message headers of {}. Status code: {}".format(url, response.status))



#TODO: Add support for Range & If-Range (RFC 2616)
#TODO: Add support for Content-Encoding. I think urllib3 already have this feature.
def download(filename, url, byRange=False, partial_file_size=0, content_length=None):
    try:
        if byRange == True:
            if content_length is None:
                h = {'Range': 'bytes={}-'.format(partial_file_size)}
            else:
                h = {'Range': 'bytes={}-{}'.format(partial_file_size, content_length)}
            r = http.request('GET', url, retries=retry, preload_content=False, headers=h)
        else:
            r = http.request('GET', url, retries=retry, preload_content=False)
    except:
        raise # urllib3.exceptions.MaxRetryError or ???
    else:
        content_length = r.headers.get('Content-Length', None)
        blocks = 1024
        
        # Status: OK or Partial Content
        if r.status == 200 or r.status == 206:
            # Server does not support partial download
            if byRange == True and r.status == 200:
                raise DownloadError("Partial downloading not supported! Status: {}".format(r.status))
            elif byRange == True and r.status == 206:
                # Change mode to appending.
                # Note that the default is 'wb'.
                # See below...
                mode = 'ab'
                
                # content_length will be inaccurate when using byte range
                if content_length is not None:
                    content_length = int(content_length) + partial_file_size
            else:
                mode = 'wb' # default mode of 'open'
                
            if content_length is None:
                with open(filename, mode=mode) as f:
                    while True:
                        try:
                            data = r.read(blocks*2)
                        except:
                            raise
                        else:
                            if data:
                                f.write(data)
                            else:
                                return # download complete
            else:    
                content_length = int(content_length)
                timeout = False
                dl_count = 0

                # is there a better way to do this?
                with progress.Bar(expected_size=(content_length)) as bar:

                    with open(filename, mode=mode) as out:
                        # Only use the size of partial file when
                        # using byte range.
                        if byRange == True:
                            dl_count = partial_file_size

                        while True:
                            try:
                                data = r.read(blocks)
                            except urllib3.exceptions.ReadTimeoutError as e:
                                timeout = True
                            except:
                                raise # urllib3.exceptions.ProtocolError or urllib3.exceptions.DecodeError
                            else:
                                if data:
                                    # dl_count = int((dl_count + len(data)) / blocks)
                                    dl_count += len(data)
                                    bar.show(dl_count)
                                    out.write(data)
                                else:
                                    return # download complete

                            if timeout == True:
                                timeout = False

                                h = {'Range': 'bytes={}-'.format(dl_count)}
                                try:
                                    r = http.request('GET', url, retries=retry, preload_content=False, headers=h)
                                except:
                                    r.release_conn() # release first the connection
                                    raise
                                else:
                                    code = r.status

                                    if code == 206:
                                        continue
                                    # elif code == 200: # OK
                                        # out.seek(0)
                                        # out.truncate()
                                        # out.flush()
                                        
                                        # while True:
                                            # try:
                                                # data = r.read(blocks*2)
                                            # except:
                                                # raise
                                            # else:
                                                # if data:
                                                    # out.write(data)
                                                # else:
                                                    # return
                                    else:
                                        r.release_conn()
                                        raise DownloadError('Server does not support partial content. status code: {}'.format(code))

        else:   # For other status code...
            r.release_conn()    # release connection
            raise DownloadError('Could not download the file. Status code: {}'.format(r.status))


def write_to_file(filename='tmp.txt', text='', mode='wb'):
    """Write text to a file. The default will write this text file as binary - a series of 1 and 0.

    Arguments:
        filename: Filename of the file. Default is 'tmp.txt'.
        text: text to be written. Default is an empty string.
        mode: Mode of file. Default is 'wb'.
    """
    with open(filename, mode) as f:
        f.write(text)


# \/:*?"<>| -- List of characters not allowed in Windows filename
def valid_fname(fname):
    """Function that remove an invalid filename character(s)."""
    return re.sub(r'[\\/:*?"<>|]', '', fname)


def create_fname(title, type):
    """Function that create a valid filename.

    Arguments:
        title: the basename of the filename.
        type: the extension name of the file.

    Returns:
        Valid filename of a video.
    """
    title = valid_fname(title)
    
    if type == 'video/mp4':
        ext = '.mp4'
    elif type == 'video/webm':
        ext = '.webm'
    elif type == 'video/x-flv':
        ext = '.flv'
    elif type == 'video/3gpp':
        ext = '.3gp'
    elif type == 'audio/mp4':   # MPEG4 audio
        ext = '.m4a' # or maybe .aac
    elif type == 'audio/webm':  # vorbis
        ext = '.ogg'
    else:
        ext = '' # Unknown
    
    filename = title + ext
    
    i = 1
    while os.path.exists(filename):
        filename = "%s(%d)%s" % (title, i, ext)
        i = i + 1
    
    return filename


if __name__ == '__main__':
    # Blood Ransom Official International Movie Trailer 
    # Starring Anne Curtis and Alexander Dreymon 2014
    url = 'https://www.youtube.com/watch?v=CUKcSzITIKg'

    try:
        html = get_html(url)
    except Exception as e:
        print(e, file=sys.stderr)
    else:
        write_to_file('dummy.html', html.encode('utf-8'))