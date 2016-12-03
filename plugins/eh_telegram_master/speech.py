import requests
import pydub
import base64
import uuid
import os

class BingSpeech:
    keys = None
    access_token = None
    full_token = None
    lang_list = ['de-DE', 'zh-TW', 'zh-HK', 'ru-RU', 'es-ES', 'ja-JP', 'ar-EG', 'da-DK', 'en-GB', 'en-IN', 'fi-FI', 'nl-NL', 'en-US', 'pt-BR', 'pt-PT', 'ca-ES', 'fr-FR', 'ko-KR', 'en-NZ', 'nb-NO', 'it-IT', 'fr-CA', 'pl-PL', 'es-MX', 'zh-CN', 'en-AU', 'en-CA', 'sv-SE']

    def __init__(self, keys):
        self.keys = keys
        d = {
            "grant_type": "client_credentials",
            "client_id": keys[0],
            "client_secret": keys[1],
            "scope": "https://speech.platform.bing.com"
        }
        r = requests.post("https://oxford-speech.cloudapp.net/token/issueToken", data=d).json()
        self.access_token = r['access_token']
        self.full_token = r

    def recognize(self, path, lang="zh-CN"):
        if isinstance(path, str):
            file = open(path, 'rb')
        else:
            return ["ERROR!", "File must by a path string."]
        if lang not in self.lang_list:
            return ["ERROR!", "Invalid language."]

        audio = pydub.AudioSegment.from_file(file)
        audio = audio.set_frame_rate(16000)
        audio.export("%s.wav" % path, format="wav")
        header = {
            "Authorization": "Bearer %s" % self.access_token,
            "Content-Type": "audio/wav; samplerate=16000"
        }
        d = {
            "version": "3.0",
            "requestid": str(uuid.uuid1()),
            "appID": "D4D52672-91D7-4C74-8AD8-42B1D98141A5",
            "format": "json",
            "locale": lang,
            "device.os": "Telegram",
            "scenarios": "ulm",
            "instanceid": uuid.uuid3(uuid.NAMESPACE_DNS, 'com.1a23.ehforwarderbot'),
            "maxnbest": 5
        }
        with open("%s.wav" % path, 'rb') as f:
            r = requests.post("https://speech.platform.bing.com/recognize", params=d, data=f.read(), headers=header)
        os.remove("%s.wav" % path)
        try:
            rjson = r.json()
        except:
            return ["ERROR!", r.text]
        if r.status_code == 200:
            return [i['name'] for i in rjson['results']]
        else:
            return ["ERROR!", r.text]


class BaiduSpeech:
    key_dict = None
    access_token = None
    full_token = None
    lang_list = ['zh', 'ct', 'en']

    def __init__(self, key_dict):
        self.key_dict = key_dict
        d = {
            "grant_type": "client_credentials",
            "client_id": key_dict['api_key'],
            "client_secret": key_dict['secret_key']
        }
        r = requests.post("https://openapi.baidu.com/oauth/2.0/token", data=d).json()
        self.access_token = r['access_token']
        self.full_token = r

    def recognize(self, file, lang="zh"):
        if hasattr(file, 'read'):
            pass
        elif isinstance(file, str):
            file = open(file, 'rb')
        else:
            return ["ERROR!", "File must by a path string or a file object in `rb` mode."]
        if lang.lower() not in self.lang_list:
            return ["ERROR!", "Invalid language."]

        audio = pydub.AudioSegment.from_file(file)
        audio = audio.set_frame_rate(16000)
        d = {
            "format": "pcm",
            "rate": 16000,
            "channel": 1,
            "cuid": "testing_user",
            "token": self.access_token,
            "lan": lang,
            "len": len(audio.raw_data),
            "speech": base64.b64encode(audio.raw_data).decode()
        }
        r = requests.post("http://vop.baidu.com/server_api", json=d)
        rjson = r.json()
        if rjson['err_no'] == 0:
            return rjson['result']
        else:
            return ["ERROR!", rjson['err_msg']]
