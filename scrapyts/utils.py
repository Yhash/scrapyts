from clint.textui import progress
from scrapyts.exceptions import DownloadError

import re
import sys
import os.path
import certifi
import urllib3


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}

# http://stackoverflow.com/questions/9384474/in-chrome-how-many-redirects-are-too-many
retry = urllib3.Retry(60, redirect=20)
timeout = urllib3.Timeout(connect=3.05, read=2*60)
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
            content_type = response.headers.get('content-type', None)

            if content_type:
                # RFC 2616
                # Format:
                # media-type     = type "/" subtype *( ";" parameter )
                # type           = token
                # subtype        = token
                # type, subtype and param names are case-insensitive
                # while param values might or might not be case-sensitive

                p = re.compile(r'charset=(?P<charset>[^;]+)')
                m = p.search(content_type)
                if m:
                    # This can throw an error if encoding is not available.
                    try:
                        html = response.data.decode(m.group('charset'))
                    except: #TODO: Find out what error it will raise
                        raise
                    else:
                        return html
            
            b_html = r.data

            # m = re.search(rb'<meta[ \t\n]+charset=(["\'])(?P<charset>.+?)\1', r.content, re.IGNORECASE)
            p = re.compile(br'<meta[ \t\n]+charset=(["\'])(?P<charset>.+?)\1', re.IGNORECASE)
            m = p.search(b_html)
            if m:
                encoding = m.group('charset').strip()
                # This can throw an error if encoding is not available.
                try:
                    html = b_html.decode(encoding)
                except: #TODO: Find out what error it will raise
                    raise
                else:
                    return html

    raise DownloadError("Failed to download the page {}".format(url))


def get_headers(url, redirect=False):
    """This function will return the HTTP response headers of a given url or raise an exception if an error occurred.

    Arguments:
        url: The url of web page to be downloaded.
        redirect: Set to True to allow redirection. Default is False.

    Returns:
        Returns a dictionary of HTTP headers.
    """

    if redirect == True:
        redirect = 20 # Firefox && Chrome

    retry = urllib3.Retry(60, redirect=redirect)

    try:
        response = http.request('HEAD', url, retries=retry)
    except:
        raise
    else:
        if response.status == 200: # OK
            return response.headers # I think this is compatible to Python dict. So I will just return it.
        else:
            response.release_conn()

    raise DownloadError("Failed to download the message headers of {}".format(url))



#TODO: Add support for Range & If-Range (RFC 2616)
#TODO: Add support for Content-Encoding. I think urllib3 already have this feature.
def download(filename, url):
    try:
        r = http.request('GET', url, preload_content=False, retries=retry)
    except:
        raise # urllib3.exceptions.MaxRetryError or ???
    else:
        content_length = r.headers.get('Content-Length', None)
        blocks = 1024

        if r.status == 200:
            if content_length is None:
                with open(filename, 'wb') as f:
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
                with progress.Bar(expected_size=(content_length/blocks)) as bar:

                    with open(filename, 'wb') as out:
                        i = 0

                        while True:
                            try:
                                data = r.read(blocks)
                            except urllib3.exceptions.ReadTimeoutError:
                                timeout = True
                            except:
                                raise # urllib3.exceptions.ProtocolError or urllib3.exceptions.DecodeError
                            else:
                                if data:
                                    dl_count += len(data)
                                    i += 1
                                    bar.show(i)
                                    out.write(data)
                                else:
                                    return # download complete

                            if timeout == True:
                                timeout = False

                                h = {'Range': 'bytes={}-{}'.format(dl_count, content_length)}
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