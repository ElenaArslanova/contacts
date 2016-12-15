import argparse
import csv
import getpass
import os.path

from modules.clients import Client, VkClient, TwitterClient
from modules.matcher import Matcher


def create_parser():
    parser = argparse.ArgumentParser(prog='contacts',
                                     description='''Export contacts
                                     from VK and Twitter to csv''')
    parser.add_argument('--vk_name', help='vk screen name',
                        required=True)
    parser.add_argument('-id', type=positive, help='vk id')
    parser.add_argument('--twitter_name', help='twitter screen name')
    parser.add_argument('--file', default='profiles',
                        help='saving exported profiles to csv file')
    return parser


def positive(value):
    int_value = int(value)
    if int_value <= 0:
        raise argparse.ArgumentTypeError('%s is invalid positive int value' %
                                         value)
    return int_value


def write_to_csv(profiles, filename):
    directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(directory, '{}.csv'.format(filename))
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(Client.FriendInfo._fields)
        for profile in profiles:
            writer.writerow(profile)


def main():
    parser = create_parser()
    namespace = parser.parse_args()
    vk_screen_name = namespace.vk_name
    twitter_screen_name = namespace.twitter_name
    filename = namespace.file
    print('Log into VK')
    email = input('Email: ')
    password = getpass.getpass('Password: ')
    try:
        vk_client = VkClient(email, password, screen_name = vk_screen_name)
        contact = vk_client.get_friends_info()
        twitter_client = TwitterClient(twitter_screen_name)
        fr = twitter_client.get_friends_info()
        matcher = Matcher(contact, fr)
        profiles = matcher.match_profiles()
        write_to_csv(profiles, filename)
        print('Exporting profiles is finished!')
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
