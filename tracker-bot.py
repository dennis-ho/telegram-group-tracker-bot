#!/usr/bin/python

from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
import cPickle as pickle
import re
import os.path

TOKEN = '' # TODO - Set your Telegram API key here
MSG_RE = '(?P<emoter>\w+)\s+%s\s+(?P<target>.+)'
RE_FLAGS = re.I
ENTRIES_FILE_PATH = 'entries.dat'
GET_COMMAND = 'get'
VERBS = [
    'loves',
    'hates'
]

entries = None

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
        
    def __eq__(self, other):
        return self.emoter.lower() == other.emoter.lower() \
           and self.verb.lower() == other.verb.lower() \
           and self.target.lower() == other.target.lower() \
           and self.chat_id.lower() == other.chat_id.lower()
           
    def __hash__(self):
        return hash(self.emoter.lower(), self.verb.lower(), self.target.lower(), self.chat_id.lower())

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
    
def handle_msg(bot, update):
    for verb in VERBS:
        save_if_type(bot, verb, update)

def send_list(bot, verb, chat_id, filter=None):
    lines = []
    global entries
    for entry in [entry for  entry in entries[verb] 
                        if   entry.chat_id == chat_id 
                        and (filter is None or entry.emoter.lower() == filter.lower())]:
        lines.append('{0} {1} {2}'.format(entry.emoter, verb, entry.target))
    if lines:
        bot.sendMessage(chat_id, text='\n'.join(lines))

def get(bot, update, args):
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

def main():
    global entries
    entries = load_file(ENTRIES_FILE_PATH)

    updater = Updater(TOKEN)
    
    dp = updater.dispatcher
    dp.addHandler(MessageHandler([Filters.text], handle_msg), group=0)
    dp.addHandler(CommandHandler(GET_COMMAND, get, pass_args=True), group=1)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()