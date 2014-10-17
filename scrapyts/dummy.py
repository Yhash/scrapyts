def download(url, filename):
    """This function will download the video and save it into a file."""
    try:
        response = requests.get(url, headers=headers, stream=True, verify=certifi.where())
        response.raise_for_status() # 4XX | 5XX
    except:
        raise
    else:
        content_length = response.headers.get("Content-Length")
        if content_length is None:
                f = open(filename, 'wb')
                try:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                except:
                    raise # Timeout or ConnectionError?
                else:
                    return # Completed Successfully
                finally:
                    f.close()
        else:
            blocks = 1024
            dl_count = 0
            content_length = int(content_length)

            # is there a better way to do this?
            with Bar(expected_size=(content_length/blocks)) as bar:
                with open(filename, 'wb') as f:

                    i = 0

                    while True:
                        try:
                            data = response.raw.read(blocks)
                        except requests.packages.urllib3.exceptions.ReadTimeoutError as e:
                            timeout = True
                        except: # Other exception should be raise.
                            raise
                        else:
                            if data:
                                dl_count += len(data)
                                i += 1
                                bar.show(i)
                                f.write(data)
                            else:
                                return # Completed Successfully

                        if timeout == True:

                            timeout = False

                            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36',
                                       'Range': 'bytes={}-{}'.format(dl_count, content_length)}
                            
                            try:
                                response = requests.get(url, headers=headers, stream=True, verify=certifi.where())
                                response.raise_for_status() # 4XX | 5XX
                            except:
                                raise
                            else:
                                if response.status_code != 206:
                                    raise DownloadError('Could not download the partial file. Status code: {}'.format(response.status_code))