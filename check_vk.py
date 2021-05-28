#!/opt/conda/envs/py36/bin/python3

import datetime as dt
import json
import os
from pathlib import Path

import pip._vendor.requests as requests
from app import Config, Database


class Vk:
    last_res_path = Path('last_res.txt')
    error_path = Path('error.txt')

    def __init__(self, vk_config):
        self.vk_config = vk_config

    def call_get_method(self, method_name, params=None):
        # We don't want to bother VK with requests that result in errors
        # Thus, in case of an error we dump the error into the error_path file and raise an exception.
        # After that the error dump becomes the regular output from the call until the file is removed.
        if self.error_path.exists():
            with self.error_path.open(encoding='utf-8') as f1:
                return json.load(f1)

        url = 'https://api.vk.com/method/' + method_name
        _params = {'v': self.vk_config.api_version, 'access_token': self.vk_config.access_token}
        if params:
            _params.update(params)
        res = requests.get(url, params=_params)

        # keep the last response to look for something interesting
        with self.last_res_path.open('w', encoding='utf-8') as f1:
            f1.write(res.text)
        res.raise_for_status()
        res_dict = res.json()

        if 'error' in res_dict:
            with self.error_path.open('w', encoding='utf-8') as f1:
                f1.write(res.text)
            raise Exception(res_dict['error'].get('error_msg'))
        return res_dict

    def wall_get(self, owner_id: str) -> dict:
        result = self.call_get_method('wall.get', params={'owner_id': owner_id})
        return result.get('response', {}).get('items', [])


# dict keys for posts I saw
# dict_keys(['id', 'from_id', 'owner_id', 'date', 'marked_as_ads', 'post_type', 'text', 'post_source', 'comments', 'likes', 'reposts'])
# dict_keys(['id', 'from_id', 'owner_id', 'date', 'marked_as_ads', 'post_type', 'text', 'copy_history', 'post_source', 'comments', 'likes', 'reposts'])
# dict_keys(['id', 'from_id', 'owner_id', 'date', 'marked_as_ads', 'post_type', 'text', 'attachments', 'post_source', 'comments', 'likes', 'reposts'])

class VkMessageFormatter:
    def __init__(self, users, groups):
        self.users = {int(key): value for key, value in users.items()}
        self.groups = {int(key): value for key, value in groups.items()}

    def format_message(self, post):
        owner_id = post['owner_id']
        post_id = post['id']
        date = str(dt.datetime.fromtimestamp(post['date']))[:-3]
        user_name = self.users.get(post['from_id'], str(post['from_id']))
        group_name = self.groups.get(owner_id, str(owner_id))
        tags = []
        if 'copy_history' in post:
            tags.append('repost')
        if 'attachments' in post:
            tags.append('has_attachments')
        if tags:
            tags_text = '---\ntags: ' + ' '.join(tags)
        else:
            tags_text = ''

        post_url = 'https://vk.com/wall{}_{}'.format(owner_id, post_id)
        subject = f"Новое сообщение в группе {group_name} ({user_name})"

        message = (
            f"{post_url}, {date}, {user_name}\n\n"
            f"{post['text']}\n"
            f"{tags_text}"
        )
        return {
            'owner_id': owner_id,
            'post_id': post_id,
            'subject': subject,
            'body': message,
        }


# outputs nothing if there are no new posts so that cron wouldn't create any messages
def main():
    os.chdir(Path(__file__).parent.absolute())
    config = Config()
    formatter = VkMessageFormatter(config.vk.users, config.vk.groups)
    database = Database(config.database.path)

    vk = Vk(config.vk)
    for group_id in config.vk.groups:
        posts = vk.wall_get(group_id)

        # check the last id for the group we have and take only those that are greater
        last_post_id = database.get_max_post_id_for_owner(group_id)

        # with vk.last_res_path.open() as f1:
        #    posts = json.load(f1)['response']['items']

        posts = sorted((post for post in posts if post['id'] > last_post_id), key=lambda x: x['id'])

        for post in posts:
            msg = formatter.format_message(post)
            database.insert_post(msg)

            print(msg['subject'] + '\n')
            print(msg['body'])
            print('-' * 20)


if __name__ == '__main__':
    main()
