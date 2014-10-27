# Try this module in the terminal by typing
# python -m scrapyts.parser.youtube


from scrapyts.jsinterp import JSInterpreter
from scrapyts.exceptions import (DownloadError, ParseError)

import re
import json
import urllib.parse
import scrapyts.utils as utils


class Youtube:
    """Youtube is class that retrieve information about a video for example its url of videos
    from a given valid url of youtube.com."""

    def __init__(self, url, logger=None):
        self.url = url
        #self._logger = logger # instance of utils.Logger class

        try:
            html = utils.get_html(self.url)
        except:
            raise DownloadError("Could not download web page {}".format(url))
        else:
            m = re.search(r'ytplayer.config(?: +)=(?: +)(?P<config>{.+?})(?=;)', html)
            if m is None: raise ParseError('Failed to find ytplayer.config from the source code.')

            txt = m.group('config')

            try:
                self._config = json.loads(txt) # returns a dict
            except:
                raise ParseError('Could not load json.')
            else:
                try:
                    self.title = self._parse_attr('title')
                    self.video_id = self._parse_attr('video_id')
                except:
                    raise


    def _parse_attr(self, attr):
        try:
            value = self._config['args'][attr]
        except:
            raise ParseError('Could not find {} of the stream.'.format(attr))
        else:
            return value


    def _parse_sig_js(self, jscode):
        m = re.search(r'signature=(?P<funcname>[$a-zA-Z]+)', jscode)
        if m is None:
            raise ParseError('Could not find the name of the function for decoding the signature.')

        funcname = m.group('funcname')

        jsi = JSInterpreter(jscode)
        try:
            initial_function = jsi.extract_function(funcname)
        except ParseError:
            raise
        else:
            return lambda s: initial_function([s])


    def parse_all(self):
        try:
            stream_list = self.parse()
        except:
            raise # DownloadError or ParseError
        else:
            youtube_info = {
                "title": self.title,   # Title of the video.
                "url": self.url,       # The original url of the video.
                "streams": stream_list  # A list of videos
            }

            return youtube_info


    def to_json(self):
        """Method that return a representation of this class as a json string.

        Returns:
            json string or raise DownloadError or ParseError when an error occured.
        """
        try:
            info = self.parse_all()
        except:
            raise # DownloadError or ParseError
        else:
            try:
                text = json.dumps(info)
            except:
                raise ParseError("Could not make a json string.")
            else:
                return text


    def parse(self):
        """Parses the urls of the video and audio and then return it as a list.

        Returns:
            returns list of url of video/audio or if an error occurred raise DownloadError or ParseError.
        """
        try:
            stream_maps = self._parse_stream_maps()
        except:
            raise
        else:
            streams = [] # list of url of videos and audios.

            for key, urls in stream_maps.items():
                #urls = video_urls[key]  # return a list of urls
                
                # This regex will be test 2x just to make sure that
                # both 'adaptive_fmts' & 'url_encoded_fmt_stream_map'
                # either use or does not use encoding for its signatures.
                decode_sig = None
                if re.search(r'(?=signature)', urls[0]) is None:
                    try:
                        js_url = self._config['assets']['js']
                    except KeyError:
                        raise ParseError('Failed to find html5 player js file.')

                    js_url = 'http:%s' % js_url
                    page = utils.get_html(js_url)
                    if page is None: raise ParseError('Failed to download html5 js file. %s' % js_url)
                    try:
                        decode_sig = self._parse_sig_js(page)
                    except ParseError:
                        raise # Re-raise it again.

                if key == 'url_encoded_fmt_stream_map':
                    try:
                        fmt_list = self._config['args']['fmt_list']
                    except KeyError:
                        raise ParseError('Could not find fmt_list.')
                    else:
                        sizes = [] # list of video sizes
                        fmt_list = re.split(r',', fmt_list)
                        if len(fmt_list) > 1:
                            for value in fmt_list:
                                size = re.split(r'/', value)
                                if len(size) > 1:
                                    sizes.append(size[1])
                                else:
                                    raise ParseError('Failed to get the size.')
                        else:
                            raise ParseError('Failed to split fmt_list. %s' % fmt_list)
                
                for i in range(len(urls)):
                    # This will arrange the url.
                    try:
                        urls[i] = self._arrange_url(urls[i], decode_sig)
                        #utils.write_to_file(urls[i], 'urls.log', 'a')
                    except ParseError:
                        raise
                    else:
                        pass # log here...
                    
                    try:
                        itag = re.search(r'[&?]itag=(?P<itag>\d+)', urls[i]).group('itag')
                    except AttributeError:
                        raise ParseError("Could not find 'itag'.")
                    
                    try:
                        type = re.search(r'[&?]type=(?P<type>[^&;]+)', urls[i]).group('type')
                    except AttributeError:
                        raise ParseError("Could not find 'type'.")
                    
                    if key == 'adaptive_fmts':
                        try:
                            clen = re.search(r'[&?]clen=(?P<clen>\d+)', urls[i]).group('clen')
                        except AttributeError:
                            raise ParseError("Could not find 'clen'.")

                        try:
                            size = re.search(r'[&?]size=(?P<size>\w+)', urls[i]).group('size')
                        except AttributeError:
                            # Interestingly there are some audio that the type is video/mp4;+codecs="unknown"
                            # When I try to download it I found out that it is an audio/webm.
                            # Hmmm... It seems that Youtube is doing something new today.
                            # example: https://www.youtube.com/watch?v=ngJo6p-lzg8
                            # .....................................................
                            # Haha, I found out that the unknown codec is A_OPUS (.opus) which can be played by
                            # Firefox >= 15 & Chrome >= 33 & Opera >= 20 & others.
                            # Like Vorbis Codec it also uses OGG container, so it can be referred to as audio/ogg.
                            # reference: http://caniuse.com/opus
                            if type.startswith('audio') or urls[i].find('video/mp4;+codecs="unknown"'):
                                size = None
                            else:
                                raise ParseError("Failed to determine its size.")
                    else:
                        try:
                            headers = utils.get_headers(urls[i], True)
                        except:
                            raise DownloadError("Could not get the headers of %s" % urls[i])
                        
                        try:
                            clen = headers['Content-Length']
                        except KeyError:
                            raise ParseError("Could not get 'clen' from headers: %s" % headers)

                        try:
                            size = sizes[i]
                        except KeyError:
                            raise ParseError("Total number of size is not same with the url of the videos - %s." % key)
                    
                    streams.append(
                    {
                        'itag': itag,
                        'url': urls[i],
                        'type': type,
                        'len': clen,
                        'size': size
                    })
                
                #del urls

            return streams   # return the list of videos and audios


    def _parse_stream_maps(self):
        args = [
        'adaptive_fmts',
        'url_encoded_fmt_stream_map'
        ]

        stream_maps = {}
        # Example:
        # stream_urls = {
        # 'adaptive_fmts': [...],
        # 'url_encoded_fmt_stream_map': [...]
        # }

        for fmts in args:
            try:
                url_map = self._config['args'][fmts] # raises KeyError when key not found in the dict.
            except KeyError:
                raise ParseError('Could not find %s' % fmts)

            urls = re.split(r',', url_map)  # returns a list
            
            if len(urls) == 1: raise ParseError("Could not split %s using ','" % fmts)
            
            stream_maps[fmts] = urls    # Add the list of urls into the stream dict
        
        return stream_maps


    def _arrange_url(self, url, decode_sig=None):
        """Method that arrange the segments of the url to its proper position."""
        m = re.search(r'(?=url=)', url)
        if m is None: raise ParseError("Could not find 'url=' from the url: %s" % url)
        
        if m.start() == 0:
            url = re.sub('url=', '', url, 1)
        else:
            p2 = re.compile(r'&url=([^&]+)')
            m = p2.search(url)
            if m is None: raise ParseError("Could not find r'&url=([^&]+)' from the url: %s" % url)
            url = m.group(1) + '&' + p2.sub('', url)

        url = urllib.parse.unquote(url)
        
        #def remove_tag(matchobj):
        #    if matchobj.group('joiner') == '&': return ''
        #    else: return matchobj.group()
        
        pattern = [
        r'(?<=[&?])itag=\d+&?',
        r'(?<=[&?])clen=\d+&?',
        r'(?<=[&?])lmt=\d+&?',
        ]
        
        for p in pattern:
            ptrn = re.compile(p)
            #iterr = ptrn.finditer(urls[index]) # This will return a callable-iterator
            list1 = ptrn.findall(url) # This will return a list            
            if not list1: continue #raise ParseError("Could not find %s" % p)
            
            # url: http://stackoverflow.com/questions/3347102/python-callable-iterator-size
            #l = len(iterr) # Length of the iterator (This is wrong because iterators doesn't have a len)
            l = len(list1) # Length of the list
            
            if l > 1: url = ptrn.sub('', url, l-1)    # minimum of 2
        
        if decode_sig is not None:    # If it is a function.
            regexobj = re.compile(r'(?<=[&?])s=(?P<sig>[^&]+)')
            try:
                sig = regexobj.search(url).group('sig')
            except AttributeError:
                raise ParseError('Could not find the encoded signature. Maybe youtube change its key.')
            else:
                sig = str(sig)  # Need to determine if this will throw an error.
                sig = decode_sig(sig)
                url = regexobj.sub('signature=%s' % sig, url)

        return url
        
        
if __name__ == '__main__':
    # Blood Ransom Official International Movie Trailer 
    # Starring Anne Curtis and Alexander Dreymon 2014
    url = "https://www.youtube.com/watch?v=CUKcSzITIKg"
    #url = "https://www.youtube.com/watch?v=pVY-2Fqdum0"     # FlipTop - Tipsy D vs Sinio
    #url = "https://www.youtube.com/watch?v=et_MRWnEuz8"     # DANIEL PADILLA - Simpleng Tulad Mo (Official Music Video)
    #url = "https://www.youtube.com/watch?v=WI5yHAmcH2g&list=PLeGljrPoR_9BKLLE7XP9TGbjM-Xb1AwDz"     # UFO News: UFO Over Hong Kong Protests. (Smoking Gun Footage) 
    #url = "https://www.youtube.com/watch?v=7lhXOgJ8ahA&index=2&list=PLeGljrPoR_9BKLLE7XP9TGbjM-Xb1AwDz"     # First iPhone 6 sold in Perth is dropped by kid during an interview

    #https://www.youtube.com/channel/UC-9-kyTW8ZkZNDHQJ6FgpwQ/featured

    yt = Youtube(url)
    print(yt.title)
    print(yt.video_id)
    #print(yt.parse())
    #print(yt.parse_all())
    print(yt.to_json())