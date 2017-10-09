#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot-probe for gobetween
"""

import logging
import config
from os import path
from telegram import ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Job
import json
import requests

# Configure logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Admin list
admin_list = [config.bot_master]
# Script directory
work_dir = path.dirname(path.realpath(__file__))
# Probe gobetween
gobetween_url = config.gobetween_url
# gobetween state
gobetween_state = True


"""
Probe
"""


def probe():
    query = requests.get(url=gobetween_url)
    result = json.loads(query.text)['backends'][0]['stats']['live']
    return result


"""
Bot
"""


def h_start(bot, update):
    """
    Welcome bot

    :param bot:
    :param update:
    :return:
    """
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    print('%s chat started' % update.message.chat_id)

    chat_id = update.message.from_user.id
    chat_name = '@%s - %s %s' % (
        update.message.from_user.username,
        update.message.from_user.first_name,
        update.message.from_user.last_name)

    if update.message.chat.type != 'private':
        chat_id = update.message.chat_id
        chat_name = '"%s" by %s' % (update.message.chat.title, chat_name)

    if update.message.from_user.id == config.bot_master:
        voice_file = '%s/%s' % (work_dir, 'resources/welcome.ogg')
        bot.sendVoice(chat_id=update.message.chat_id, voice=open(voice_file, 'rb'))
    else:
        msg = 'Запрос отправлен'
        bot.sendMessage(chat_id=update.message.chat_id, text=msg)
        msg = 'Поступил запрос от %s %s - %s' % (
            update.message.chat.type,
            chat_id,
            chat_name)
        bot.sendMessage(chat_id=config.bot_master, text=msg)


def h_help(bot, update):
    """
    Get help from bot

    :param bot:
    :param update:
    :return:
    """
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    msg = '/start: welcome bot'
    msg += '\n/probe: probe backend'

    if update.message.chat.type != 'private':
        msg += '\nfor @%s' % update.message.from_user.username

    bot.sendMessage(chat_id=update.message.chat_id, text=msg)


def h_probe(bot, update):
    """
    Probe backend

    :param bot:
    :param update:
    :return:
    """
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    if probe():
        status = 'online'
    else:
        status = 'offline'

    if update.message.from_user.id == config.bot_master:
        msg = 'Backend is %s' % status

        bot.sendMessage(chat_id=update.message.chat_id, text=msg)

    else:
        h_unknown(bot, update)


def h_unknown(bot, update):
    """
    Inform user about wrong command

    :param bot:
    :param update:
    :return:
    """
    bot.sendChatAction(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    bot.sendMessage(chat_id=update.message.chat_id, text='Спросите что-нибудь попроще.')


def j_probe(bot, update):
    """
    Probe gobetween in background

    :param bot:
    :param update:
    :return:
    """

    del update
    global gobetween_state

    state = probe()

    if state != gobetween_state:
        if probe():
            msg = 'Backend is online.'
        else:
            msg = 'Backend is offline!'
        for admin in admin_list:
            bot.sendMessage(chat_id=admin, text=msg)


# Initialize bot
updater = Updater(token=config.bot_token)
dispatcher = updater.dispatcher
jobs = updater.job_queue

# Initialize handlers
start_handler = CommandHandler('start', h_start)
help_handler = CommandHandler('help', h_help)
probe_handler = CommandHandler('probe', h_probe)
unknown_handler = MessageHandler(Filters.command, h_unknown)

# Add handlers
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(probe_handler)
dispatcher.add_handler(unknown_handler)

# Initialize jobs
probe_job = Job(j_probe, 60.0, repeat=True)

# Add jobs
jobs.put(probe_job, next_t=0.0)

# Run bot
updater.start_polling()

# Idle mode
updater.idle()
