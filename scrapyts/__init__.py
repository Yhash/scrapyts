def main():
    from scrapyts.cdownloader import CLIDownloader
    from scrapyts.exceptions import (DownloadError, ParseError)
    
    import argparse
    import sys
    import traceback
    
    
    # python scrapyts.py url -t 18 --begin 4 --end 150 --step 2 --display --nodownload --index --prefix watch --sufix "by Yhash"
    parser = argparse.ArgumentParser(description="A simple youtube video/audio downloader.")
    parser.add_argument('url', help='youtube video url')
    parser.add_argument('-t', '--tag', help='Tag of the video to be downloaded', type=int)
    parser.add_argument('-b', '--begin', help='The index of the first video in a playlist that you want to download.', type=int)
    parser.add_argument('-e', '--end', help='The index of the last video in a playlist that you want to download.', type=int)
    parser.add_argument('-d', '--display', help='Display a table of available video/audio from the given url.', action='store_true')
    parser.add_argument('-nd', '--nodownload', help='Download the video or audio.', action='store_true')
    parser.add_argument('-i', '--index', help='Prefix filename with the index of the video from the playlist.', action='store_true')
    parser.add_argument('-ap', '--aslist', help='Treat url of a specific video as a url of a playlist.', action='store_true')
    args = parser.parse_args()
    
    try:
        CLIDownloader().run(args.url, tag=args.tag, 
                                      first=args.begin, 
                                      last=args.end, 
                                      display=args.display, 
                                      download=not args.nodownload, 
                                      add_index=args.index, 
                                      as_list=args.aslist)
    except (DownloadError, ParseError, ValueError) as e:
        traceback.print_exc()
        print(e, file=sys.stderr)