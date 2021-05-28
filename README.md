# watch_vk_groups
Simple scripts for cron to monitor new posts in VK.

Скрипт, чтобы получать нотификации о новых сообщениях в группе в VK. Висит у меня в cron и сообщает мне в консоль.

```
$ crontab -e
3 9-23 * * * PYTHONIOENCODING=utf-8 /Users/newtover/projects/watch_vk_groups/check_vk.py
```

Чтобы заработало, нужен персональный [токен](https://vk.com/dev/access_token), который надо поместить в `config.yaml`. Там же надо добавить группы.

Сообщения собираются в sqlite базу database.db в директории со скриптом.

