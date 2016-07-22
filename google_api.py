import urllib2
import json
import traceback
from contextlib import closing

class GoogleApi:
    IMAGE_SEARCH_URL = 'https://www.googleapis.com/customsearch/v1?key={0}&cx={1}&q={2}&searchType=image&fileType=jpg&imgSize=large&alt=json'

    API_KEY = '' # TODO - Set your API key here
    CSE_ID = '' # TODO - Set your CSE_ID here

    def search_img(self, search_term):
        url = self.IMAGE_SEARCH_URL.format(self.API_KEY, self.CSE_ID, urllib2.quote(search_term))
        with closing(urllib2.urlopen(url)) as resp:
            html = resp.read()
            img_json = json.loads(html)
            img_url = img_json['items'][0]['link']
            return img_url
