import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))

from modules.clients import Client
from modules import metrics
from modules.matcher import Matcher, Pair
from modules.template_writer import Writer


class TestMetrics(unittest.TestCase):
    def test_jaro(self):
        self.assertTrue(metrics.jaro('martha', 'marhta') > 0.9)
        self.assertTrue(metrics.jaro('abc', 'def') == 0)
        self.assertTrue(metrics.jaro('zxcvbn', 'zxcvbn') == 1)

    def test_soft_tfidf(self):
        self.assertAlmostEqual(metrics.soft_tfidf('Martha Lewis',
                                                  'Martha Lewis', 0.8),
                               1)
        self.assertAlmostEqual(metrics.soft_tfidf('Martha Lewis',
                                                  'Lewis Martha', 0.8),
                               1)
        self.assertTrue(metrics.soft_tfidf('Aleksandr Smith',
                                           'Alexander Smith', 0.8) > 0.8)
        self.assertTrue(metrics.soft_tfidf('Qwerty Plop',
                                           'Abcd Efgh', 0.8) == 0)


class TestPair(unittest.TestCase):
    def setUp(self):
        self.matcher = Matcher([], [], True)
        self.same_pair = Pair(Client.Friend(info=Client.FriendInfo(
                                                name='John Smith',
                                                bdate='12.10.90',
                                                twitter='Johny123'),
                                            vk=True),
                              Client.Friend(info=Client.FriendInfo(
                                  name='Smith John',
                                  location='Paris, France',
                                  twitter='Johny123'),
                                  vk=False), True)
        self.different_pair = Pair(Client.Friend(info=Client.FriendInfo(
                                                    name='Rosy Lee',
                                                    sex='female',
                                                    country='Finland'),
                                                 vk=True),
                                   Client.Friend(info=Client.FriendInfo(
                                                    city='Toronto',
                                                    bdate='12.12.12'),
                                                 vk=False), True)
        self.pairs = [self.same_pair, self.different_pair]

    def test_get_common_attributes(self):
        self.assertListEqual(['name', 'twitter'],
                             self.same_pair.get_common_attributes())
        self.assertListEqual([], self.different_pair.get_common_attributes())

    def test_check_equality(self):
        for pair in self.pairs:
            for attr in pair.common_attributes:
                self.matcher.compare_attribute(self.same_pair, attr)
        self.same_pair.check_equality()
        self.assertTrue(self.same_pair.equal)
        self.different_pair.check_equality()
        self.assertFalse(self.different_pair.equal)

    def test_merge(self):
        merged_info = self.same_pair.merge()
        expected_info = Client.FriendInfo(name='John Smith', bdate='12.10.90',
                                          twitter='Johny123',
                                          location='Paris, France')

        self.assertEqual(merged_info, expected_info)

    @patch('builtins.input', lambda x: '1')
    def test_user_choice(self):
            self.assertEqual(Pair.user_choice('Location', ['London', 'Paris']),
                             'London')


class TestMatcher(unittest.TestCase):
    def setUp(self):
        vk_first = Client.Friend(info=Client.FriendInfo(name='John Smith',
                                                        bdate='12.10.90',
                                                        twitter='Johny123'),
                                 vk=True)
        vk_second = Client.Friend(info=Client.FriendInfo(name='Louis Sun',
                                                         country='Norway',
                                                         location='Oslo, Norway'),
                                  vk=True)
        twitter_first = Client.Friend(info=Client.FriendInfo(name='Johny Star',
                                                             twitter='Johny123'),
                                      vk=False)
        twitter_second = Client.Friend(info=Client.FriendInfo(name='Dave Red',
                                                              location='Oslo, Norway'),
                                       vk=False)
        self.vk_profiles = [vk_first, vk_second]
        self.twitter_profiles = [twitter_first, twitter_second]
        self.matcher = Matcher(self.vk_profiles, self.twitter_profiles, True)

    def test_get_pairs(self):
        pairs = self.matcher.get_pairs()
        expected_pairs = [Pair(self.vk_profiles[0], self.twitter_profiles[0],
                               True),
                          Pair(self.vk_profiles[0], self.twitter_profiles[1],
                               True),
                          Pair(self.vk_profiles[1], self.twitter_profiles[0],
                               True),
                          Pair(self.vk_profiles[1], self.twitter_profiles[1],
                               True)]
        self.assertEqual(len(pairs), len(expected_pairs))
        for i in range(len(pairs)):
            self.assertEqual(pairs[i].first, expected_pairs[i].first)
            self.assertEqual(pairs[i].second, expected_pairs[i].second)

    def test_compare_pairs(self):
        self.matcher.compare_pairs()
        self.assertEqual(len(self.matcher.matching_pairs), 1)
        matching_pair = self.matcher.matching_pairs[0]
        pair = Pair(self.vk_profiles[0], self.twitter_profiles[0], True)
        self.assertEqual(matching_pair.first, pair.first)
        self.assertEqual(matching_pair.second, pair.second)

    def test_compare_attribute(self):
        pair = Pair(Client.Friend(info=Client.FriendInfo(name='John Smith',
                                                         bdate='12.10.90',
                                                         twitter='Johny123'),
                                  vk=True),
                    Client.Friend(info=Client.FriendInfo(name='Smith John',
                                                         twitter='Johny123'),
                                  vk=False), True)
        self.assertEqual(pair.score, 0)
        self.matcher.compare_attribute(pair, 'name')
        self.assertEqual(pair.score, 1)
        self.matcher.compare_attribute(pair, 'bdate')
        self.assertEqual(pair.score, 1)
        self.matcher.compare_attribute(pair, 'twitter')
        self.assertEqual(pair.score, 11)

    def test_attributes_are_equal(self):
        first_name = 'John Weasley'
        second_name = 'Weasleu Johny'
        name_comparison_result = self.matcher.compare_function['name'](
            first_name, second_name, self.matcher.matching_threshold['name'])
        self.assertTrue(self.matcher.attributes_are_equal(
            name_comparison_result, 'name'))
        first_screen_name = 'Johny123'
        second_screen_name = 'John123'
        screen_name_comparison_result = self.matcher.compare_function['twitter'](
            first_screen_name, second_screen_name)
        self.assertFalse(self.matcher.attributes_are_equal(
            screen_name_comparison_result, 'twitter'))

    def test_merge_profiles(self):
        self.matcher.compare_pairs()
        merged_profiles = self.matcher.merge_profiles()
        self.assertEqual(len(merged_profiles), 3)
        merged_profile = Pair(self.vk_profiles[0],
                              self.twitter_profiles[0], True).merge()
        profiles = [merged_profile, self.vk_profiles[1].info,
                    self.twitter_profiles[1].info]
        self.assertCountEqual(merged_profiles, profiles)


class TestTemplateWriter(unittest.TestCase):
    def setUp(self):
        self.writer = Writer('test_template.txt')
        self.friend = Client.FriendInfo(name='John', city='London')

    def test_extract_fields(self):
        self.assertCountEqual(['name', 'city', 'friend', 'mobile_phone'],
                         self.writer.fields)

    def test_get_unrecognized_fields(self):
        self.assertCountEqual(['friend', 'mobile_phone'],
                         self.writer.get_unrecognized_fields(self.friend))

    def test_fill_line(self):
        line = '{{name}}, nice to see you in {{city}}'
        self.writer.fields = ['name', 'city']
        self.assertEqual('John, nice to see you in London',
                         self.writer.fill_line(self.friend, line))

if __name__ == '__main__':
    unittest.main()
