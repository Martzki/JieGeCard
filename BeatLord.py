#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding=utf8  
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')
from JieGeCard import BeatLord
from JieGeCard import BeatLordRet

import sys
import argparse
import errno
import urlparse
import urllib
import json
import time
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

PORT = 6655

InputTransfer = {
    '3': 0,
    '4': 1,
    '5': 2,
    '6': 3,
    '7': 4,
    '8': 5,
    '9': 6,
    '10': 7,
    'J': 8,
    'j': 8,
    'q': 9,
    'k': 10,
    'a': 11,
    '2': 12,
    'sj': 13,
    'bj': 14
}


class BeatLoadServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        HTTPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate=True)
        self.game = None
        self.players = []


class BeatLordHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.splitquery(self.path)
        api = query[0]
        args = query[1].split('&') if query[1] is not None else []

        if api == '/join':
            self.join_handler(args)
        elif api == '/play':
            self.play_handler(args)
        elif api == '/show':
            self.show_handler(args)
        else:
            self.response(-1, "Invalid request %s." % (api))

    def join_handler(self, args):
        if self.server.game is not None:
            self.response(-1, "Game is already started.")
            return

        if len(self.server.players) >= 3:
            self.response(-1, "Players can't larger than 3.")
            return

        username = ''
        if len(args) == 1 and args[0].startswith('username='):
            username = args[0].split('=')[1]
        else:
            username = 'player' + str(len(self.server.players))

        for player in self.server.players:
            if username == player['username']:
                self.response(-1, "Player %s is already in game." % (username))
                return

        self.server.players.append({
            'username': username,
            'id': -1,
            'cards': None
        })

        self.response(0, 'Join game with username: %s successfully.' % (username))

        if len(self.server.players) == 3:
            self.server.game = BeatLord()
            self.server.game.start()

            for player in range(3):
                self.server.players[player]['id'] = player
                self.server.players[player]['cards'] = self.server.game.get_player_cards(player)

    def play_handler(self, args):
        username = ''
        player_id = -1
        input_cards = []
        cards = []

        if self.server.game is None:
            self.response(-1, 'The game is not started.')
            return

        if len(args) != 2:
            self.response(-1, 'play require 2 arguments.')
            return

        if args[0] is None or not args[0].startswith('username='):
            self.response(-1, "Can't get valid username from request args: %s." % (args))
            return

        username = args[0].split('=')[1]
        player_id = self.username_to_id(username)

        if args[1] is None or not args[1].startswith('cards='):
            self.response(-1, "Can't get valid cards from request args: %s." % (args))
            return

        input_cards = args[1].split('=')[1]
        tmp_cards = self.server.game.get_player_cards(player_id)[:]

        if input_cards != '':
            for each in input_cards.split('+'):
                if each.lower() not in InputTransfer:
                    self.response(-1, "Invalid card: %s" % (each))
                    return

                found = False
                for card in tmp_cards:
                    if card['value'] == InputTransfer[each]:
                        cards.append(card)
                        found = True
                        break

                if found:
                    tmp_cards.remove(card)
                else:
                    self.response(-1, "Card : %s is not in his cards." % (each))
                    return

        ret = self.server.game.play(player_id, cards)
        if ret == BeatLordRet.InvalidCards:
            self.response(-1, "Invalid Cards.")
        elif ret == BeatLordRet.NotHisRound:
            self.response(-1, "Not your round.")
        else:
            self.response(0, "Success.")

    def show_handler(self, args):
        username = ''

        if self.server.game is None:
            self.response(-1, 'The game is not started.')
            return

        if len(args) == 0 or not args[0].startswith('username='):
            self.response(-1, "Can't get valid username from request args: %s." % (args))
            return

        username = args[0].split('=')[1]

        info = {
            'cards number': {},
            'last cards': [],
            'last cards player': '',
            'now player': '',
            'player cards': [],
            'lord': ''
        }

        last_cards = self.server.game.get_last_cards()
        last_cards_player = last_cards['player']
        last_player = self.server.game.get_now_player()
        lord = self.server.game.get_lord()

        for player in self.server.players:
            info['cards number'][player['username']] = len(player['cards'])
            if player['username'] == username:
                info['player cards'] = player['cards']

            if player['id'] == last_cards_player:
                info['last cards player'] = player['username']

            if player['id'] == last_player:
                info['now player'] = player['username']

            if player['id'] == lord:
                info['lord'] = player['username']

        info['last cards'] = last_cards['cards']

        self.response(0, 'Success.', info)

    def response(self, ret, msg, info=None):
        resp = {
            'result': ret,
            'msg': msg,
            'info': info
        }
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp))

    def username_to_id(self, username):
        for player in self.server.players:
            if player['username'] == username:
                return player['id']


class BeatLordClient(object):
    def __init__(self, server_address, username):
        self.server_address = server_address
        self.username = username
        self.over = False

    def send_request(self, api, args=''):
        url = self.server_address + '/' + api + '?' + args
        print 'url: ', url

        try:
            f = urllib.urlopen(url)
            ret = f.getcode()
            res = f.read()
            f.close()

            if ret == 200:
                return json.loads(res)
            else:
                print 'Request %s failed, ret: %s, res: %s.' % (url, ret, json.loads(res))
                return None
        except IOError as e:
            print 'Request %s failed: %s.' % (url, e)

            return None

    def poll_game_info(self):
        # print 'get info from server:', self.send_request('show', 'username=' + self.username)
        return self.send_request('show', 'username=' + self.username)

    def work_loop(self):
        if self.username is None:
            res = self.send_request('join')
        else:
            res = self.send_request('join', 'username=' + self.username)

        if res is not None:
            print 'Join result: %s.' % (res)
            if res['result'] != 0:
                return

        self.username = res['msg'].split(':')[1].split()[0]

        while not self.over:
            self.one_round()

    def one_round(self):
        res = self.poll_game_info()
        self.print_game_info(res['info'])

        while res['info'] is None or res['info']['now player'] != self.username:
            time.sleep(1)
            res = self.poll_game_info()
            self.print_game_info(res['info'])

        while True:
            user_input = raw_input('Your round now, input your cards: ')
            res = self.send_request('play', 'username=' + self.username + '&cards=' + user_input.strip().replace(' ', '+'))
            if res is not None:
                print 'Play result: %s' % (res)

                if res['result'] == 0:
                    break

                print 'Invalid input, press any key to try again.'
                raw_input()
                res = self.poll_game_info()
                self.print_game_info(res['info'])

    def print_line(self, str, center=False, pad=' ', head='┃', tail='┃'):
        tmp = ""
        if len(str) > 0:
            if center:
                length = (98 - len(str)) / 2
                for i in range(length):
                    tmp += pad

                out = head + tmp + str

                length = 98 - length - len(str)
                tmp = ""
                for i in range(length):
                    tmp += pad
                out += tmp + tail
            else:
                length = 98 - len(str)
                if str.startswith('\033['):
                    length += len('\033[5;37;42m\033[0m')

                for i in range(length):
                    tmp += pad

                out = head + str + tmp + tail
        else:
            for i in range(98):
                tmp += pad

            out = head + tmp + tail

        # print "str: %s, len: %d" % (str, len(str))
        print out

    def print_game_info(self, info):
        print '\033c'
        self.print_line("", pad='━', head='┏', tail='┓')
        self.print_line("JieGeCard", center=True)
        self.print_line("", pad='━', head='┣', tail='┫')
        if info is not None:
            self.print_line("Your username: %s" % (self.username))

            for player in info['cards number']:
                if player == info['lord']:
                    self.print_line("%s(Lord) has %d cards" % (player, info['cards number'][player]))
                else:
                    self.print_line("%s has %d cards" % (player, info['cards number'][player]))

            self.print_line("Last cards: [%s], played by %s" % (self.dump_cards(info['last cards']), info['last cards player']))
            self.print_line("\033[5;37;42mNow: %s's round\033[0m" % (info['now player']))
            self.print_line("Your Cards: [%s]" % (self.dump_cards(info['player cards'])))
            self.print_line("", pad='━', head='┣', tail='┫')
            self.print_line("Notice: Input your cards directly, seprated by ' ', case-insensitive.")
            self.print_line("        'bj/sj' stands for 'Big Joker/Small Joker'. Input Enter directly for passing.")
            self.print_line("         e.g. '3 3 3 a a' or 'bj sj'.")
        else:
            self.print_line("The game is not started yet.", center=True)
        self.print_line("", pad='━', head='┗', tail='┛')

        if info is not None and 0 in info['cards number'].values():
            self.over = True
            players = info['cards number'].keys()
            if info['cards number'][info['lord']] == 0:
                print "Game over, winner is %s." % (info['lord'])
            else:
                players.remove(info['lord'])
                print "Game over, winners are %s." % (players[0] + ' and ' + players[1])

            exit(0)

    def dump_cards(self, cards):
        if cards is None:
            return None

        cards_list = []
        for card in cards:
            cards_list.append(card['name'])

        out = ''
        for card in sorted(cards_list):
            out += card + '+'

        return out.strip().strip('+').replace('+', ', ')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", action="store_true", dest="server_mode", help="server mode")
    parser.add_argument("-n", dest="username", help="user name")
    parser.add_argument("server_address", nargs="?", help="server address")

    args = parser.parse_args()
    if args.server_mode:
        server = BeatLoadServer(('', PORT), BeatLordHandler)
        server.serve_forever()
    else:
        if args.server_address is None:
            print "clint mode must specify the server address."
            exit(errno.EINVAL)

        client = BeatLordClient(args.server_address, args.username)
        client.work_loop()
