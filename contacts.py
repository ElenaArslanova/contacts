import argparse
import os.path
import csv
from clients import Client, VkClient, TwitterClient
import getpass
from matcher import Matcher


def create_parser():
    parser = argparse.ArgumentParser(prog='contacts',
                                     description='Merge contacts from VK and Twitter')
    parser.add_argument('--vk_name', nargs=1, help='vk screen name',
                        required=True)
    parser.add_argument('-id', type=positive, help='vk id')
    parser.add_argument('--twitter_name', nargs=1, help='twitter screen name')
    return parser


def positive(value):
    int_value = int(value)
    if int_value <= 0:
        raise argparse.ArgumentTypeError('%s is invalid positive int value' %
                                         value)
    return int_value


def write_to_csv(profiles, filename):
    directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(directory, filename)
    with open(path, 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(Client.FriendInfo._fields)
        for profile in profiles:
            writer.writerow(profile)


def main():
    parser = create_parser()
    namespace = parser.parse_args()
    vk_screen_name = namespace.vk_name
    twitter_screen_name = namespace.twitter_name
    email = input('Email: ')
    password = getpass.getpass('Password: ')

    vk_client = VkClient(email, password, screen_name=vk_screen_name)
    #
    # contact = vk_client.get_friends_info()[:4]
    # twitter_client = TwitterClient(twitter_screen_name)
    # try:
    #     fr = twitter_client.get_friends_info()
    #     matcher = Matcher(contact, fr)
    #     profiles = matcher.match_profiles()
    #     write_to_csv(profiles, 'contacts.csv')
    # except Exception as e:
    #     print(e)


if __name__ == '__main__':
    main()
