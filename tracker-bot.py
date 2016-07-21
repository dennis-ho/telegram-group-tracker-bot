#!/usr/bin/python

from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
import cPickle as pickle
import re
import os.path
import random
import traceback
import google_api

TOKEN = '' # TODO - Set your Telegram API key here
MSG_RE = '(?P<emoter>\w+)\s+%s\s+(?P<target>.+)'
RE_FLAGS = re.I
ENTRIES_FILE_PATH = 'entries.dat'

GET_COMMAND         = 'get'
RANDOM_COMMAND      = 'random'
COUNT_COMMAND       = 'count'
PIC_REQUEST_TRIGGER = 'pic'

VERBS = [
    'loves',
    'hates'
]

entries = None
last_msg = None

class DirectedEmotion:
    emoter = None
    verb = None
    target = None
    chat_id = None
    
    def __init__(self, emoter, verb, target, chat_id):
        self.emoter = emoter
        self.verb = verb
        self.target = target
        self.chat_id = chat_id
    
    def __str__(self):
        return '{0} {1} {2}'.format(self.emoter, self.verb, self.target)
    
    def __eq__(self, other):
        return self.emoter.lower() == other.emoter.lower() \
           and self.verb.lower() == other.verb.lower() \
           and self.target.lower() == other.target.lower() \
           and self.chat_id.lower() == other.chat_id.lower()
    
    def __hash__(self):
        return hash(self.emoter.lower(), self.verb.lower(), self.target.lower(), self.chat_id.lower())
    
    def is_owned_by(self, emoter):
        return self.emoter.lower() == emoter.lower()

def save_if_type(bot, verb, update):
    match = re.match(MSG_RE % verb, update.message.text, RE_FLAGS)
    if not match:
        return
    
    global entries
    if verb not in entries:
        entries[verb] = []

    directed_emotion = DirectedEmotion(match.group('emoter'), verb, match.group('target'), update.message.chat_id)
    if directed_emotion not in entries[verb]:
        entries[verb].append(directed_emotion)
        pickle.dump(entries, open(ENTRIES_FILE_PATH, 'wb'))

def handle_verbs(bot, update):
    for verb in VERBS:
        save_if_type(bot, verb, update)
        
def handle_pic_req(bot, update):
    try:
        global last_msg
        
        if update.message.text.lower() == PIC_REQUEST:
            pic_url = google_api.GoogleApi().search_img(last_msg)
            send_msg(bot, update.message.chat_id, pic_url)
        else:
            last_msg = update.message.text
    except:
        pass

def handle_msg(bot, update):
    handle_verbs(bot, update)    
    handle_pic_req(bot, update)

def handle_pic_req(bot, update, args):
    global last_msg
    
    if update.message.text.lower() == PIC_REQUEST_TRIGGER.lower():
        if last_msg is None:
            return
        pic_url = google_api.GoogleApi().search_img(last_msg)
        send_msg(bot, update.message.chat_id, pic_url)
    else:
        last_msg = update.message.text

def send_msg(bot, chat_id, str):
    bot.sendMessage(chat_id, text=str)

def send_list(bot, verb, chat_id, filter=None):
    lines = []
    global entries
    for entry in [entry for  entry in entries[verb] 
                        if   entry.chat_id == chat_id 
                        and (filter is None or entry.is_owned_by(filter))]:
        lines.append(str(entry))
    if lines:
        send_msg(bot, chat_id, '\n'.join(lines))

def get_cmd_handler(bot, update, args):
    try:
        send_list(bot, args[0], update.message.chat_id, args[1] if len(args) >= 2 else None)
    except:
        pass

def load_file(path):
    if not os.path.isfile(path):
        return dict()
    try:
        with open(path, 'rb') as fp:
            return pickle.load(fp)
    except:
        pass
        
def random_cmd_handler(bot, update):
    try:
        global entries
        entry = random.choice(entries[random.choice(list(entries.keys()))])
        send_msg(bot, update.message.chat_id, str(entry))
    except:
        pass
    
def count_cmd_handler(bot, update, args):
    global entries
    emoter = args[0] if len(args) >= 1 else None
    verbs = [args[1]] if len(args) >= 2 else list(entries.keys())
    count = 0
    for verb in verbs:
        count = count + sum([1 for entry in entries[verb] if emoter is None or entry.is_owned_by(emoter)])
    send_msg(bot, update.message.chat_id, '{0} {1} entries: {2}'.format('All' if emoter is None else emoter, '/'.join(verbs), count))

def main():
    global entries
    entries = load_file(ENTRIES_FILE_PATH)

    updater = Updater(TOKEN)
    
    dp = updater.dispatcher
    dp.addHandler(MessageHandler([Filters.text],    handle_msg),                                    group=0)
    dp.addHandler(CommandHandler(GET_COMMAND,       get_cmd_handler,            pass_args=True),    group=1)
    dp.addHandler(CommandHandler(RANDOM_COMMAND,    random_cmd_handler),                            group=1)
    dp.addHandler(CommandHandler(COUNT_COMMAND,     count_cmd_handler,          pass_args=True),    group=1)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()