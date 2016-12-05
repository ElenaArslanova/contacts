from collections import namedtuple
from itertools import islice, chain
import urllib.request
from urllib.parse import urlencode
import json
import vk_auth
import twitter_auth

class Client:
    VK = 'vk'
    TWITTER = 'twitter'

    FIELDS = ['bdate', 'sex', 'city', 'country', 'home_town', 'contacts',
              'career', 'education', 'site', 'connections']
    GENDER = {0: 'unknown', 1: 'female', 2: 'male'}
    # RELATION = {0: 'unknown', 1: 'single', 2: 'in a relationship',
    #             3: 'engaged', 4: 'married', 5: "it's complicated",
    #             6: 'actively searching', 7: 'in love'}
    SOCIAL_NETWORKS = ['instagram', 'twitter', 'facebook_name', 'skype',
                       'livejournal']
    EDUCATION_PARAMS = ['faculty_name', 'university_name', 'graduation']
    CONTACTS_PARAMS = ['home_phone', 'mobile_phone']
    FriendInfo = namedtuple('Friend', ' '.join(chain(FIELDS, SOCIAL_NETWORKS,
                                                     EDUCATION_PARAMS,
                                                     CONTACTS_PARAMS)))
    FriendInfo.__new__.__defaults__ = (None,) * len(FriendInfo._fields)

    def get_request_url(self, network, method, parameters):
        if network == self.VK:
            parameters['v'] = '5.8'
        return 'https://api.{}.com/{}?{}'.format(network, method,
                                               urlencode(parameters))

    def clear_friends_field(self, friends, field_parameters):
        for friend in friends:
            for param in field_parameters:
                if param in friends[friend] and not friends[friend][param]:
                    friends[friend].pop(param, None)

    def request(self, network, method, parameters):
        pass

class VkClient(Client):
    CLIENT_ID = '5743518'

    def __init__(self, email, password, vk_id=None, screen_name=None): # убрать ненужные параметры и методы
        self.screen_name = screen_name
        self.access_token = vk_auth.auth(email, password, self.CLIENT_ID,
                                         'friends')
        if vk_id is not None:
            self.id = vk_id
        else:
            self.id = self.get_vk_id()

    def request(self, network, method, parameters):
        url = self.get_request_url(network, method, parameters)
        return urllib.request.urlopen(url).read().decode('utf-8')

    def get_vk_id(self):
        id_request = self.request(self.VK, 'method/utils.resolveScreenName',
                                  {'screen_name': self.screen_name})
        return json.loads(id_request)['response']['object_id']

    def process_friends_field(self, friends, fields):
        for field in fields:
            friends_with_field_specified, remaining_friends = self.friends_filtered_by_field(
                friends, field)
            for friend in friends_with_field_specified:
                title = friends_with_field_specified[friend][field]['title']
                friends_with_field_specified[friend][field] = title
            friends_with_field_specified.update(remaining_friends)
            friends = friends_with_field_specified

    def get_friends_info(self): # учесть, что friends.get только 5000 выдает
        friends = {}
        friends_request = self.request(self.VK, 'method/friends.get',
                                       {'user_id': self.id,
                                        'access_token': self.access_token,
                                        'fields': ','.join(self.FIELDS)})
        friends_info = json.loads(friends_request)['response']['items']
        for friend_info in friends_info:
            for param in ['id', 'deactivated', 'online', 'lists', 'university',
                          'faculty', 'facebook']:
                friend_info.pop(param, None)
            person = "{} {}".format(friend_info.pop('last_name'),
                                    friend_info.pop('first_name'))
            friend_info['sex'] = self.GENDER[friend_info['sex']]
            friends[person] = friend_info
        self.process_friends_field(friends, ['city', 'country'])
        fields_to_clear = ['career', 'home_town', 'site']
        self.clear_friends_field(friends, list(chain(fields_to_clear,
                                                self.EDUCATION_PARAMS,
                                                self.CONTACTS_PARAMS)))
        for friend in friends:
            friends[friend] = self.FriendInfo(**friends[friend])
        return friends

    @staticmethod
    def friends_filtered_by_field(friends, field):
        friends_with_specified_field = {}
        remaining_friends = {}
        for friend in friends:
            info = friends[friend]
            if field not in info:
                remaining_friends[friend] = info
            else:
                friends_with_specified_field[friend] = info
        return friends_with_specified_field, remaining_friends


def cursor_handler(request):
    def handle_cursor(*args, **kwargs):
        all_data = []
        data = json.loads(request(*args, **kwargs))
        for user in data['users']:
            all_data.append(user)
        while data['next_cursor'] != 0:
            next_cursor = data['next_cursor_str']
            kwargs['cursor'] = next_cursor
            data = json.loads(request(*args, **kwargs))
            for user in data['users']:
                all_data.append(user)
        return all_data
    return handle_cursor


class TwitterClient(Client):
    def __init__(self, screen_name):
        self.screen_name = screen_name
        auth_handler = twitter_auth.AppAuthHandler()
        self.oauth2bearer = auth_handler.apply_auth()

    @cursor_handler
    def request(self, network, method, parameters, cursor=-1):
        parameters['cursor'] = cursor
        url = self.get_request_url(network, method, parameters)
        request = self.oauth2bearer(urllib.request.Request(url))
        return urllib.request.urlopen(request).read().decode('utf-8')

    def get_friends_info(self):
        friends = {}
        friends_data = self.request(self.TWITTER, '1.1/friends/list.json',
                           {'screen_name': self.screen_name,
                            'count': 200})
        for data in friends_data:
            person = data.pop('name')
            friends[person] = {'site': data['url'],
                               'location': data['location']}
        return friends