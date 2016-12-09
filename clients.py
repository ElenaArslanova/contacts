from collections import namedtuple
from itertools import chain
import urllib.request
from urllib.parse import urlencode
import json
import vk_auth
import twitter_auth


class Client:
    VK = 'vk'
    TWITTER = 'twitter'

    FIELDS = ['name', 'city', 'home_town', 'contacts',
              'career', 'education', 'connections', 'location']
    GENDER = {0: 'unknown', 1: 'female', 2: 'male'}
    BASIC = ['bdate', 'sex', 'country', 'site']
    SOCIAL_NETWORKS = ['instagram', 'twitter', 'facebook_name', 'skype',
                       'livejournal']
    EDUCATION_PARAMS = ['faculty_name', 'university_name']
    CONTACTS_PARAMS = ['home_phone', 'mobile_phone']
    FriendInfo = namedtuple('Friend', ' '.join(chain(FIELDS, SOCIAL_NETWORKS,
                                                     EDUCATION_PARAMS,
                                                     CONTACTS_PARAMS, BASIC)))
    FriendInfo.__new__.__defaults__ = (None,) * len(FriendInfo._fields)

    def get_request_url(self, network, method, parameters):
        if network == self.VK:
            parameters['v'] = '5.8'
        return 'https://api.{}.com/{}?{}'.format(network, method,
                                               urlencode(parameters))

    @staticmethod
    def clear_friends_field(friends, field_parameters):
        for friend in friends:
            for param in field_parameters:
                if param in friend and not friend[param]:
                    friend.pop(param, None)

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
                title = friend[field]['title']
                friend[field] = title
            friends_with_field_specified.extend(remaining_friends)
            friends = friends_with_field_specified

    def get_friends_info(self):
        friends = []
        friends_request = self.request(self.VK, 'method/friends.get',
                                       {'user_id': self.id,
                                        'access_token': self.access_token,
                                        'fields': ','.join(chain(self.FIELDS, self.BASIC))})
        friends_info = json.loads(friends_request)['response']['items']
        for friend_info in friends_info:
            for param in ['id', 'deactivated', 'online', 'lists', 'university',
                          'faculty', 'facebook', 'graduation']:
                friend_info.pop(param, None)
            friend_info['name'] = "{} {}".format(friend_info.pop('last_name'), friend_info.pop('first_name'))
            friend_info['sex'] = self.GENDER[friend_info['sex']]
            if 'career' in friend_info and friend_info['career']:
                career_info = friend_info['career'][0]
                friend_info['career'] = '{}, {}'.format(career_info.get('company', ''), career_info.get('position', ''))
            friends.append(friend_info)
        self.process_friends_field(friends, ['city', 'country'])
        for friend in friends:
            friend['location'] = '{}, {}'.format(friend.get('city', ''), friend.get('country', ''))
        fields_to_clear = ['career', 'home_town', 'site']
        self.clear_friends_field(friends, list(chain(fields_to_clear, self.EDUCATION_PARAMS, self.CONTACTS_PARAMS)))
        return [self.FriendInfo(**friend) for friend in friends]

    @staticmethod
    def friends_filtered_by_field(friends_info, field):
        friends_with_specified_field = []
        remaining_friends = []
        for friend in friends_info:
            if field not in friend:
                remaining_friends.append(friend)
            else:
                friends_with_specified_field.append(friend)
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
        friends = []
        friends_data = self.request(self.TWITTER, '1.1/friends/list.json',
                           {'screen_name': self.screen_name,
                            'count': 200})
        for data in friends_data:
            if data['url']:
                site = data['entities']['url']['urls'][0]['expanded_url']
            else: site = None
            friends.append({'name': data['name'], 'site': site,
                            'location': data['location'], 'twitter': data['screen_name']})
        self.clear_friends_field(friends, ['location', 'site'])
        return [self.FriendInfo(**friend) for friend in friends]
