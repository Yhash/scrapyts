# Used by other modules to determine if proxy will be
# used instead of direct connection.
proxy = None


def set_proxy(ip):
    global proxy

    import re

    # I thinks tcp ports are around 65000? What do you think?
    m = re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}$', ip)
    if m:
        proxy = 'http://' + m.group()
        return True
    else:
    	return False    # Well just inform the client that nothing has been change.