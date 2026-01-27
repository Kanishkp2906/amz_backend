import pyshorteners

def url_shortner(url):
    tiny = pyshorteners.Shortener()
    short_url = tiny.tinyurl.short(url)
    return short_url