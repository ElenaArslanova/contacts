import argparse
import csv
import getpass
import os.path

from modules.clients import Client, VkClient, TwitterClient
from modules.matcher import Matcher
from modules.template_writer import Writer


def create_parser():
    parser = argparse.ArgumentParser(prog='contacts',
                                     description='''Export contacts
                                     from VK and Twitter to csv''')
    parser.add_argument('--vk_name', help='vk screen name',
                        required=True)
    parser.add_argument('-id', type=positive, help='vk id')
    parser.add_argument('--twitter_name', help='twitter screen name',
                        required=True)
    parser.add_argument('--file', default='profiles',
                        help='saving exported profiles to csv file')
    parser.add_argument('--template', help='template file')
    parser.add_argument('--auto_merge', action='store_true', default=True,
                        help='''Automatic merge in case of conflict
                        (VK data is preferred)''')
    return parser


def positive(value):
    int_value = int(value)
    if int_value <= 0:
        raise argparse.ArgumentTypeError('%s is invalid positive int value' %
                                         value)
    return int_value


def write_to_csv(profiles, filename):
    if os.path.isabs(filename):
        path = filename
        root, ext = os.path.splitext(path)
        if ext != 'csv':
            path = '{}.csv'.format(root)
    else:
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
    template = namespace.template
    auto_merge = namespace.auto_merge
    print('Log into VK')
    email = input('Email: ')
    password = getpass.getpass('Password: ')
    try:
        vk_client = VkClient(email, password, screen_name=vk_screen_name)
        vk_data = vk_client.get_friends_info()
        twitter_client = TwitterClient(twitter_screen_name)
        twitter_data = twitter_client.get_friends_info()
        matcher = Matcher(vk_data, twitter_data, auto_merge)
        profiles = matcher.match_profiles()
        write_to_csv(profiles, filename)
        print('Exporting profiles is finished!')
        if template:
            writer = Writer(template)
            writer.write_filled_template(profiles)
            print('Templates are written!')
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
