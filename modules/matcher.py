from itertools import chain

from modules import metrics
from modules.clients import Client


class Matcher:
    def __init__(self, first_net_profiles, second_net_profiles, auto_merge):
        self.first_network = first_net_profiles
        self.second_network = second_net_profiles
        self.auto_merge = auto_merge
        self.tfidf_attributes = ['name', 'career', 'faculty_name',
                                 'university_name', 'location']
        self.compare_function = self.get_compare_function()
        self.matching_threshold = self.get_matching_threshold()
        self.matching_points = self.get_matching_points()
        self.non_matching_points = self.get_non_matching_points()
        self.pairs = self.get_pairs()
        self.matching_pairs = []

    def get_compare_function(self):
        compare_function = dict.fromkeys(chain(Client.BASIC,
                                               Client.SOCIAL_NETWORKS,
                                               Client.CONTACTS_PARAMS),
                                         lambda x, y: 1 if x == y else 0)
        compare_function.update(dict.fromkeys(Client.FIELDS, metrics.jaro))
        compare_function.update(dict.fromkeys(self.tfidf_attributes,
                                              metrics.soft_tfidf))
        return compare_function

    @staticmethod
    def get_matching_threshold():
        threshold = dict.fromkeys(chain(Client.FIELDS,
                                        Client.EDUCATION_PARAMS), 0.7)
        threshold.update({'person': 0.8, 'location': 0.7})
        return threshold

    @staticmethod
    def get_matching_points():
        matching_points = {'name': 1, 'location': 2, 'country': 1,
                           'career': 2, 'education': 2, 'site': 5}
        matching_points.update(dict.fromkeys(Client.EDUCATION_PARAMS, 2))
        matching_points.update(dict.fromkeys(Client.SOCIAL_NETWORKS, 10))
        return matching_points

    @staticmethod
    def get_non_matching_points():
        non_matching_points = {'name': -1, 'location': -1, 'country': -5,
                               'career': -1,
                               'education': -1, 'sex': -10, 'site': -1}
        non_matching_points.update(dict.fromkeys(Client.SOCIAL_NETWORKS, -3))
        return non_matching_points

    def get_pairs(self):
        return [Pair(user_1, user_2, self.auto_merge)
                for user_1 in self.first_network
                for user_2 in self.second_network]

    def merge_profiles(self):
        profiles = []
        for pair in self.pairs:
            profiles.extend((pair.first.info, pair.second.info))
        profiles = set(profiles)
        for pair in self.matching_pairs:
            profiles = profiles - {pair.first.info, pair.second.info}
            profile = pair.merge()
            profiles.add(profile)
        return list(profiles)

    def compare_pairs(self):
        for pair in self.pairs:
            for attribute in pair.common_attributes:
                self.compare_attribute(pair, attribute)
            pair.check_equality()
            if pair.equal:
                self.matching_pairs.append(pair)

    def compare_attribute(self, pair, attribute):
        if attribute not in pair.common_attributes:
            return
        if attribute in self.tfidf_attributes:
            threshold = self.matching_threshold.get(attribute)
            result = self.compare_function[attribute](getattr(pair.first.info,
                                                              attribute),
                                                      getattr(pair.second.info,
                                                              attribute),
                                                      threshold)
        else:
            result = self.compare_function[attribute](getattr(pair.first.info,
                                                              attribute),
                                                      getattr(pair.second.info,
                                                              attribute))
        if self.attributes_are_equal(result, attribute):
            if attribute in self.matching_points:
                pair.score += self.matching_points[attribute]
        else:
            if attribute in self.non_matching_points:
                pair.score += self.non_matching_points[attribute]

    def attributes_are_equal(self, comparison_result, attribute):
        return (attribute in self.matching_threshold and
                comparison_result > self.matching_threshold[attribute] or
                comparison_result == 1)

    def match_profiles(self):
        self.compare_pairs()
        return self.merge_profiles()


class Pair:
    def __init__(self, first_user, second_user, auto_merge):
        self.first = first_user
        self.second = second_user
        self.auto_merge = auto_merge
        self.score = 0
        self.common_attributes = self.get_common_attributes()
        self.equal = None

    def get_common_attributes(self):
        return [field for field in Client.FriendInfo._fields
                if (getattr(self.first.info, field) and
                    getattr(self.second.info, field))]

    def check_equality(self):
        points = Matcher.get_matching_points()
        max_score = sum(points[attr] for attr in self.common_attributes
                        if attr in points)
        if self.score > max_score * 0.8:
            self.equal = True
        else:
            self.equal = False

    def merge(self):
        available_attributes = [field for field in Client.FriendInfo._fields
                                if getattr(self.first.info, field) or
                                getattr(self.second.info, field)]
        profile_info = {}
        for attr in available_attributes:
            first = getattr(self.first.info, attr)
            second = getattr(self.second.info, attr)
            if attr in self.common_attributes:
                if self.auto_merge:
                    profile_info[attr] = first if self.first.vk else second
                else:
                    profile_info[attr] = self.user_choice(attr,
                                                          [first, second])
            else:
                profile_info[attr] = first if second is None else second
        return Client.FriendInfo(**profile_info)

    @staticmethod
    def user_choice(conflict_attribute, options):
        print('Merging {} field'.format(conflict_attribute))
        print('First option: {}\nSecond option: {}'.format(*options))
        option = input('Choose an option. Enter 1 or 2: ')
        while option not in ['1', '2']:
            option = input('Invalid option. Choose from 1 and 2: ')
        return options[int(option) - 1]

    def __repr__(self):
        return '{} - {}'.format(self.first.info.name, self.second.info.name)
