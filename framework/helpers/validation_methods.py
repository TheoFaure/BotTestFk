import re
import urllib.error
import urllib.parse
import urllib.request

from framework.helpers.api_calls import send_request


def is_valid_true(s1, s2):
    return True


def is_valid_spellcheck(sentence_orig, sentence_mut):
    params = urllib.parse.urlencode({
        'hl': "en",
        'q': sentence_mut,
        'gws_rd': 'ssl'
    })
    data, headers, status = send_request("GET", "www.google.ie", "/search", params=params)
    html = data.decode('ISO-8859-1')
    match = re.search(r'(?:Showing results for|Did you mean|Including results for)[^\0]*?<a.*?>(.*?)</a>', html)

    if match is None:
        return False
    else:
        fix = match.group(1)
        fix = re.sub(r'<.*?>', '', fix)
        if fix in sentence_orig:
            return True
        else:
            return False
