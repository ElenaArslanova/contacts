import argparse
from clients import VkClient, TwitterClient
import getpass
from vk_auth import auth
import twitter_auth
from matcher import Matcher
import metrics


def create_parser():
    parser = argparse.ArgumentParser(prog='contacts', description='Export contacts from vk.com to Google Contacts')
    parser.add_argument('screen_name', nargs=1, help='vk screen name')
    parser.add_argument('-id', type=int, help='vk id')
    return parser


def main():
    #parser = create_parser()
    #namespace = parser.parse_args()
    #screen_name = namespace.screen_name

    screen_name='contl'
    # email = input('Email: ')
    # password = getpass.getpass('Password: ')

    email = 'contilen@rambler.ru'
    password = 'LeGos1002PlTa'
    vk_client = VkClient(email, password, screen_name='contl')

    contact = vk_client.get_friends_info()[:6]
    n1 = contact[:3]
    n2 = contact[3:]


    twitter_client = TwitterClient('contilen')
    try:
        fr = twitter_client.get_friends_info()
        for f in fr:
            print(f)
    except Exception as e:
        print(e)

    # print(metrics.soft_tfidf('qwe rty', 'weqwe rtyr', 0.7))
    # matcher = Matcher(n1, n2)
    # pairs = matcher.get_pairs()
    # matcher.compare_pairs()
    # for p in matcher.pairs:
    #     print(p.first)
    #     print(p.second)
    #     print(p.score)
    #     print()

if __name__ == '__main__':
    main()
