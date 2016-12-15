import urllib.request
import json
from urllib.parse import urlencode


class AppAuthHandler:
    OAUTH_HOST = 'api.twitter.com'
    OAUTH_ROOT = '/oauth2/'

    def __init__(self):
        self.bearer_token = ''

        bearer_token_credentials = '''Umk0anhvd2JnbUNuMnkySWNiRUdlOHpxaTpua1E1W
        XZMOGVjV1p0VWFRd21hSHFvdjdJVmFDUHFSN2MxNnhKd0xYcERuYWNEbERyRw=='''

        request = urllib.request.Request(url=self.get_oauth_url('token'),
                                         headers={'Authorization':
                                                  'Basic {}'.format(
                                                      bearer_token_credentials)
                                                  },
                                         data=urlencode(
                                         {'grant_type': 'client_credentials'}
                                         ).encode())
        data = json.loads(urllib.request.urlopen(request).read().decode(
               'utf-8'))
        if data['token_type'] != 'bearer':
            raise RuntimeError('Expected bearer token, '
                               'got token of type {} instead'.format(
                data['token_type']))
        self.bearer_token = data['access_token']

    def get_oauth_url(self, endpoint):
        return 'https://{}{}{}'.format(self.OAUTH_HOST, self.OAUTH_ROOT,
                                       endpoint)

    def apply_auth(self):
        return OAuth2Bearer(self.bearer_token)


class OAuth2Bearer:
    def __init__(self, bearer_token):
        self.bearer_token = bearer_token

    def __call__(self, request: urllib.request.Request):
        request.add_header('Authorization',
                           'Bearer {}'.format(self.bearer_token))
        return request
