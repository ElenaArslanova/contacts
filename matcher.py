from clients import Client
from itertools import chain
import metrics


class Matcher:
    def __init__(self, first_net_profiles, second_net_profiles):
        self.first_network = first_net_profiles
        self.second_network = second_net_profiles
        self.tfidf_attributes = ['name', 'career', 'faculty_name', 'university_name', 'location']
        self.compare_function = self.get_compare_function()
        self.matching_threshold = self.get_matching_threshold()
        self.matching_points = self.get_matching_points()
        self.non_matching_points = self.get_non_matching_points()
        self.pairs = self.get_pairs()
        self.matching_pairs = []

    def get_compare_function(self):
        compare_function = dict.fromkeys(chain(Client.BASIC, Client.SOCIAL_NETWORKS, Client.CONTACTS_PARAMS),
                                         lambda x, y: 1 if x == y else 0)
        compare_function.update(dict.fromkeys(Client.FIELDS, metrics.jaro))
        compare_function.update(dict.fromkeys(self.tfidf_attributes, metrics.soft_tfidf))
        return compare_function

    @staticmethod
    def get_matching_threshold():
        threshold = dict.fromkeys(chain(Client.FIELDS, Client.EDUCATION_PARAMS), 0.7)
        threshold.update({'person': 0.8, 'location': 0.7})
        return threshold

    @staticmethod
    def get_matching_points():
        matching_points = {'person': 1, 'location': 2, 'country': 1, 'career': 2, 'education': 2, 'site': 5}
        matching_points.update(dict.fromkeys(Client.EDUCATION_PARAMS, 2))
        matching_points.update(dict.fromkeys(Client.SOCIAL_NETWORKS, 10))
        return matching_points

    @staticmethod
    def get_non_matching_points():
        non_matching_points = {'person': -10, 'location': -1, 'country': -5, 'career': -1,
                               'education': -1, 'sex': -10, 'site': -1}
        non_matching_points.update(dict.fromkeys(Client.SOCIAL_NETWORKS, -3))
        return non_matching_points

    def get_pairs(self):
        return [Pair(user_1, user_2) for user_1 in self.first_network for user_2 in self.second_network]

    def get_unique_profiles(self):
        profiles = set()
        for pair in self.matching_pairs:
            profile = pair.merge()
            profiles.add(profile)
        non_matching_pairs = set(self.pairs) - set(self.matching_pairs )
        for pair in non_matching_pairs:
            profiles.add(pair.first)
            profiles.add(pair.second)
        return profiles

    def compare_pairs(self):
        for pair in self.pairs:
            for attribute in pair.common_attributes:
                self.compare_attribute(pair, attribute)
            pair.check_equality()
            if pair.equal:
                self.matching_pairs.append(pair)

    def compare_attribute(self, pair, attribute):
        if attribute in self.tfidf_attributes:
            result = self.compare_function[attribute](getattr(pair.first, attribute), getattr(pair.second, attribute),
                                                      self.matching_threshold.get(attribute))
        else:
            result = self.compare_function[attribute](getattr(pair.first, attribute), getattr(pair.second, attribute))
        if self.attributes_are_equal(result, attribute):
            if attribute in self.matching_points:
                pair.score += self.matching_points[attribute]
        else:
            if attribute in self.non_matching_points:
                pair.score += self.non_matching_points[attribute]

    def attributes_are_equal(self, comparison_result, attribute):
        if (attribute in self.matching_threshold and comparison_result > self.matching_threshold[attribute]
                or comparison_result == 1):
            return True
        else:
            return False


class Pair:
    def __init__(self, first_user, second_user):
        self.first = first_user
        self.second = second_user
        self.score = 0
        self.common_attributes = self.get_common_attributes()
        self.equal = None

    def get_common_attributes(self):
        return [field for field in Client.FriendInfo._fields
                if getattr(self.first, field) and getattr(self.second, field)]

    def check_equality(self):
        points = Matcher.get_matching_points()
        max_score = sum(points[attr] for attr in self.common_attributes if attr in points)
        if self.score > max_score * 0.8:
            self.equal = True
        else:
            self.equal = False

    def merge(self):
        if not self.equal:
            return None
        available_attributes = [field for field in Client.FriendInfo._fields
                                if getattr(self.first, field) or getattr(self.second, field)]
        profile_info = {}
        for attribute in available_attributes:
            first = getattr(self.first, attribute)
            second = getattr(self.second, attribute)
            if attribute in self.common_attributes:
                profile_info[attribute] = first if len(first) > len(second) else second
            else:
                profile_info[attribute] = first if second is None else second
        return Client.FriendInfo(**profile_info)

    def __repr__(self):
        return '{} - {}'.format(self.first.name, self.second.name)
