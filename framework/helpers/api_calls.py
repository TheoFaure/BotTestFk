import http.client, urllib.request, urllib.parse, urllib.error
import json
from html.parser import HTMLParser
from xml.etree import ElementTree
import re
import six
# from google.cloud import translate
import requests
from google.cloud import language
import apiai


#### API CALLS ####
###################
# This file contains the methods to make calls to external APIs.
# The api keys are stored in a file "api_keys".
###################


yandex_api_key = open('/home/theo/Projects/MuTest/api_keys/yandex_translation').readline()
translation_api_key = open('/home/theo/Projects/MuTest/api_keys/microsoft_translation').readline()
token_translation = ''
luisai_key = open('/home/theo/Projects/MuTest/api_keys/luisai').readline()
apiai_token = open('/home/theo/Projects/MuTest/api_keys/apiai').readline()
google_trans_token = open('/home/theo/Projects/MuTest/api_keys/google_translation').readline()
# spellcheck_microsoft_key = open('~/Projects/MuTests/api_keys/microsoft_spellcheck').readline()


def send_request(method, host, url, body=None, params=None, headers=None):
    try:
        conn = http.client.HTTPSConnection(host)
        if params is None:
            if body is None:
                conn.request(method, url, headers=headers)
            else:
                conn.request(method, url, body=body, headers=headers)
        else:
            if body is None and headers is None:
                conn.request(method, "%s?%s" % (url, params))
            else:
                conn.request(method, "%s?%s" % (url, params), body=body, headers=headers)
        response = conn.getresponse()
        data = response.read()
        headers = response.getheaders()
        status = response.status
        conn.close()
        return data, headers, status
    except Exception as e:
        print("Error. HTML Response: ")
        print(response.status)
        print(response.read().decode('utf-8'))
        print(response.getheaders())
        raise e


def translate_yandex(text, language):
    params = urllib.parse.urlencode({
        'key': yandex_api_key,
        'text': text,
        'lang': language,
    })

    try:
        data, headers, status = send_request("GET", 'translate.yandex.net', "/api/v1.5/tr.json/translate", params=params)
        json_obj = json.loads(data.decode('utf-8'))
        return json_obj['text'][0]
    except Exception as e:
        raise e


def get_token_translation():
    print("Getting access token for text translation")
    headers = {
        'Ocp-Apim-Subscription-Key': translation_api_key,
        'Content-Length': 0,
    }
    global token_translation

    try:
        data, headers, status = send_request("POST", 'api.cognitive.microsoft.com', "/sts/v1.0/issueToken", headers=headers)
        token_translation = data.decode('utf-8')
        print(token_translation)
    except Exception as e:
        raise e


def get_microsoft_translation(text, language):
    headers = {
        'Authorization': 'Bearer {token}'.format(token=token_translation)
    }

    params = urllib.parse.urlencode({
        'text': text,
        'to': language,
    })

    try:
        data, headers, status = send_request("GET", 'api.microsofttranslator.com', "/v2/http.svc/Translate",
                                             headers=headers, params=params)
        tree = ElementTree.fromstring(data.decode('utf-8'))
        return "".join((tree.text.split('\n')[0].rsplit('\xa0')))
    except Exception as e:
        raise e


def spellcheck_microsoft(sentence):
    " Not working... Because I have no API key. So no tested. "
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        # 'Ocp-Apim-Subscription-Key': spellcheck_microsoft_key,
    }

    sentence = "Text=%s"%sentence
    try:
        data, headers, status = send_request("POST", "api.cognitive.microsoft.com", "/bing/v5.0/spellcheck",
                                headers=headers, body=sentence)
        json_obj = json.loads(data.decode('utf-8'))
        if json_obj['flaggedTokens'] == []:
            return True
        else:
            return False
    except Exception as e:
        raise e


def get_luis(request):
    url = 'https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/' \
          'cadfc107-9c94-455c-96c9-cb82dc171256?subscription-key=%s' \
          '&timezoneOffset=0&verbose=true&spellCheck=true&q=%s'%(luisai_key, request)
    luis_json = requests.get(url).json()
    # print(luis_json)
    # intent = str(luis_json['topScoringIntent']['intent'])
    # entities = [(e['entity'], e['type']) for e in luis_json['entities']]
    return luis_json


def get_api_ai(sentence, arg):
    ai = apiai.ApiAI(apiai_token)

    request = ai.text_request()
    request.lang = 'en'  # optional, default value equal 'en'
    request.query = sentence
    response = json.loads(request.getresponse().read().decode())
    intent = response['result']['action']
    entities = [i for i in response['result']['parameters'].values()]
    return intent, entities


def syntax_text(text):
    """Detects syntax in the text."""
    language_client = language.Client()

    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')

    # Instantiates a plain text document.
    document = language_client.document_from_text(text)

    # Detects syntax in the document. You can also analyze HTML with:
    #   document.doc_type == language.Document.HTML
    tokens = document.analyze_syntax().tokens
    return tokens


def translate_google2(text, target):
    # translate_client = translate.Client()
    # if isinstance(text, six.binary_type):
    #     text = text.decode('utf-8')
    #
    # translation = translate_client.translate(
    #     text,
    #     target_language=target)
    #
    # return translation['translatedText']
    return "", ""


def translate_google(text, source, target):
    headers = {
        'Authorization': 'Bearer {token}'.format(token=google_trans_token)
    }

    params = urllib.parse.urlencode({
        'Content-Type': 'text/json'
    })

    body = ("{'q': \'%s\', 'source': \'%s\', 'target': \'%s\', 'format': 'text'}" % (text, source, target))

    try:
        data, headers, status = send_request("POST", 'translation.googleapis.com', "/language/translate/v2",
                                             headers=headers, params=params, body=body)
        json_obj = json.loads(data.decode('utf-8'))
        return json_obj['data']['translations'][0]['translatedText']
    except Exception as e:
        print("Caught error: " + repr(e))
        print(data, headers, status)
        raise
