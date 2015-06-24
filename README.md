#This is the README of scrapyt

##Description

scrapyts is a simple audio/video downloader for the popular video streaming website youtube.com. It can be used to download only one video or audio or an entire playlist. It also support resuming of partial/broken download.

##Terminology:

<url>          - The url of a video in youtube
<playlist_url> - The url of a playlist in youtube

##Usage:
  If you want to download a video. Just type:
    `python scrapyts.py <url>`
  This will download the video in the specified url. Note that by default scrapyts will try to download the lowest available resolution of that video. If you don't like the default behaviour you can used `-t` option to specify your preferred resolution.
    `python scrapyts.py <url> -t 18`
  From the example above scrapyts will download the video from the specified url that have a resolution of 360p when it is available in the server of youtube.
  
  You can determine all available resolution and format of a video using -d or --display option and by adding `-nd` or `--nodownload` to it you can prevent downloading of a video.
    `python scrapyts.py <url> -d -nd`
  The result of the example above would be something like this.
 ```--------------------------------------------------
     TAG    TYPE            LENGTH          SIZE
    --------------------------------------------------
     22     video/mp4       712604673       1280x720
     43     video/webm      262142073       640x360
     18     video/mp4       201634651       640x360
     5      video/x-flv     114278784       426x240
     36     video/3gpp      73750115        426x240
     17     video/3gpp      26634435        256x144
     137    video/mp4       1055271919      1920x1080
     248    video/webm      649032959       1920x1080
     136    video/mp4       556562337       1280x720
     247    video/webm      359919338       1280x720
     135    video/mp4       292257390       854x480
     244    video/webm      182855188       854x480
     134    video/mp4       152113574       640x360
     243    video/webm      107558959       640x360
     133    video/mp4       79850081        426x240
     242    video/webm      59388206        426x240
     160    video/mp4       35598574        256x144
     140    audio/mp4       41990608        None
     171    audio/webm      38458206        None
  ```

  Now can you used any TAG(only the number) from that list for the `-t` or `--tag` option just like from the previous example.
  
  You can also download an entire playlist for example.
    `python scrapyts.py <playlist_url>`

  Or just part of it using `-b/--begin` and `-e/--end`. For example if you only want to download the 1st and 2nd video from a playlist you can used something like this.
    `python scrapyts.py <playlist_url> -b 1 -e 2`
    
  Or much better using...
    `python scrapyts.py <playlist_url> -e 2`
    
  The latter example works because by default scrapyts will begin downloading from the 1st video. That is why you don't need to used -b or --begin.
  
  You can also add an auto generated index number in the front of every filename using `-i` or `--index`.
    `python scrapyts.py <playlist_url> -i`
    
  Lastly, you can resume a partial/broken download using -r or --resume option.
    `python scrapyts.py <playlist_url> -r`
    
  *Note:* Be careful when using -r option because you need to make sure that partial video and the part of the
  video that you are going to download from youtube are the same. It is to mess with this option so be very
  careful.
  
  If you want to learn more just used the `--help` option.
    `python scrapyts.py --help`
  or
    `python scrapyts.py -h`
    
  Sorry for my bad english I am not a native english speaker. But hopefully you understand it right.