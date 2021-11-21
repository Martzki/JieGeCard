#!/usr/bin/python
# -*- coding: utf-8 -*-  
import random
from enum import Enum

ColorName = ['Spade', 'Heart', 'Club', 'Diamond']
ValueName = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2', 'Small Joker', 'Big Joker']
DEBUGON = True


def debug(str):
	if DEBUGON:
		print str

class BeatLordRet(Enum):
	UnknownFailed = 0
	InvalidCards = 1
	NotHisRound = 2
	GameOver = 3
	ValidPass = 4
	ValidSingle = 5
	ValidDouble = 6
	ValidTriple = 7
	ValidSingleSequnce = 8
	ValidDoubleSequnce = 9
	ValidTripleSequnce = 10
	ValidTripleSingle = 11
	ValidTripleDouble = 12
	ValidQuadrupleDouble = 13
	ValidPlane = 14
	ValidBomb = 15


class CardType(Enum):
	Invalid = -1
	Single = 0
	Double = 1
	Triple = 2
	SingleSequnce = 3
	DoubleSequnce = 4
	TripleSequnce = 5
	TripleSingle = 6
	TripleDouble = 7
	QuadrupleDouble = 8
	Plane = 9
	Bomb = 10
	Pass = 11

def card_type_transfer_to_ret(card_type):
	if card_type == CardType.Invalid:
		return BeatLordRet.InvalidCards
	elif card_type == CardType.Single:
		return BeatLordRet.ValidSingle
	elif card_type == CardType.Double:
		return BeatLordRet.ValidDouble
	elif card_type == CardType.Triple:
		return BeatLordRet.ValidTriple
	elif card_type == CardType.SingleSequnce:
		return BeatLordRet.ValidSingleSequnce
	elif card_type == CardType.DoubleSequnce:
		return BeatLordRet.ValidDoubleSequnce
	elif card_type == CardType.TripleSequnce:
		return BeatLordRet.ValidTripleSequnce
	elif card_type == CardType.TripleSingle:
		return BeatLordRet.ValidTripleSingle
	elif card_type == CardType.TripleDouble:
		return BeatLordRet.ValidTripleDouble
	elif card_type == CardType.QuadrupleDouble:
		return BeatLordRet.ValidQuadrupleDouble
	elif card_type == CardType.Plane:
		return BeatLordRet.ValidPlane
	elif card_type == CardType.Bomb:
		return BeatLordRet.ValidBomb
	elif card_type == CardType.Pass:
		return BeatLordRet.ValidPass

class Cards():
	def __init__(self):
		self.cards = []
		for color in range(4):
			for value in range(13):
				self.cards.append({
						'color': color,
						'value': value,
						'name': ValueName[value]
					})

		self.cards.append({'color': None,
						   'value': 13,
						   'name': ValueName[13]})
		self.cards.append({'color': None,
			               'value': 14,
			               'name': ValueName[14]})

	def alloc_cards(self, is_lord):
		if len(self.cards) == 0:
			return None

		if is_lord:
			return self.cards
		else:
			cards = []
			for i in range(17):
				card = random.choice(self.cards)
				cards.append(card)
				self.cards.remove(card)

			return cards


class BeatLord():
	def __init__(self):
		self.last_cards = {}
		self.players = []
		self.over = False

	def start(self):
		self.players = []
		cards = Cards()
		for i in range(3):
			self.players.append({
					'is_lord': False,
					'cards': cards.alloc_cards(False)
				})

		self.lord = random.randint(0, 2)
		lord_cards = cards.alloc_cards(True)
		self.last_player = (self.lord - 1) % 3
		self.players[self.lord]['is_lord'] = True
		self.players[self.lord]['cards'].extend(lord_cards)
		self.last_cards = {
			'player': self.lord,
			'cards': None,
			'type': None
		}

		return {
			'lord': self.lord,
			'lord_cards': lord_cards
		}

	def is_over(self):
		return self.over

	def get_player_cards(self, player):
		return self.players[player]['cards']

	def get_last_cards(self):
		return self.last_cards

	def get_now_player(self):
		return (self.last_player + 1) % 3

	def get_lord(self):
		return self.lord

	def cards_are_valid_core(self, cards_type, player, cards):
		# type_func is used to test if cards are the corrosponding type.
		# cmp_func is used to compare cards with same type.
		type_func = None
		cmp_func = self.generic_compare
		if cards_type == CardType.Single:
			type_func = self.cards_are_single
			key_len = 1
		elif cards_type == CardType.Double:
			type_func = self.cards_are_double
			key_len = 2
		elif cards_type == CardType.Triple:
			type_func = self.cards_are_triple
			key_len = 3
		elif cards_type == CardType.SingleSequnce:
			type_func = self.cards_are_single_sequence
			key_len = 1
		elif cards_type == CardType.DoubleSequnce:
			type_func = self.cards_are_double_sequence
			key_len = 2
		elif cards_type == CardType.TripleSequnce:
			type_func = self.cards_are_triple_sequence
			key_len = 3
		elif cards_type == CardType.TripleSingle:
			type_func = self.cards_are_triple_single
			key_len = 3
		elif cards_type == CardType.TripleDouble:
			type_func = self.cards_are_triple_double
			key_len = 3
		elif cards_type == CardType.QuadrupleDouble:
			type_func = self.cards_are_quadruple_double
			key_len = 4
		elif cards_type == CardType.Plane:
			type_func = self.cards_are_plane
			key_len = 3
		elif cards_type == CardType.Bomb:
			type_func = self.cards_are_bomb
			key_len = -1
			cmp_func = self.bomb_compare

		debug("cards_type: %s, player: %s, cards: %s" % (cards_type, player, cards))
		debug("type_func: %s, self.last_cards['player']: %s, self.last_cards['type']: %s" % (type_func, self.last_cards['player'], self.last_cards['type']))
		# His round again.
		if self.last_cards['player'] == player and type_func(cards):
			return True
		# Only the same type of cards are allowed. 
		elif self.last_cards['type'] == cards_type and \
			 type_func(cards) and cmp_func(key_len, self.last_cards['cards'], cards):
			return True
		# Bomb is allowed beyond the constraint of type.
		elif cards_type == CardType.Bomb and \
		     self.last_cards['type'] != cards_type and type_func(cards):
			return True

		return False

	# e.g. A
	def cards_are_single(self, cards):
		return len(cards) == 1

	def cards_are_valid_single(self, player, cards):
		return self.cards_are_valid_core(CardType.Single, player, cards)

	# e.g. 22
	def cards_are_double(self, cards):
		return len(cards) == 2 and cards[0]['value'] == cards[1]['value']

	def cards_are_valid_double(self, player, cards):
		return self.cards_are_valid_core(CardType.Double, player, cards)

	# e.g. 333
	def cards_are_triple(self, cards):
		return len(cards) == 3 and cards[0]['value'] == cards[1]['value'] and \
			   cards[0]['value'] == cards[2]['value']

	def cards_are_valid_triple(self, player, cards):
		return self.cards_are_valid_core(CardType.Triple, player, cards)

	# e.g. 34567
	def cards_are_single_sequence(self, cards):
		length = len(cards)

		if length < 5:
			return False

		value_list = []
		for card in cards:
			value_list.append(card['value'])

		# 2 and Joker need to be excluded.
		if max(value_list) > 13:
			return False

		sorted_list = sorted(value_list)

		last = sorted_list[0]
		for i in range(1, length):
			if sorted_list[i] != last + 1:
				return False

			last = sorted_list[i]

		return True

	def cards_are_valid_single_sequence(self, player, cards):
		return self.cards_are_valid_core(CardType.SingleSequnce, player, cards)

	# e.g. 33445566
	def cards_are_double_sequence(self, cards):
		length = len(cards)

		if length % 2 != 0 or length < 6:
			return False

		value_list = []
		for card in cards:
			value_list.append(card['value'])

		# 2 and Joker need to be excluded.
		if max(value_list) > 13:
			return False

		group = length / 2
		sorted_list = sorted(value_list)

		if sorted_list[0] != sorted_list[1]:
			return False

		for i in range(2):
			last = sorted_list[i]
			for j in range(1, group):
				if sorted_list[i + j * 2] != last + 1:
					return False

				last = sorted_list[i + j * 2]

		return True

	def cards_are_valid_double_sequence(self, player, cards):
		return self.cards_are_valid_core(CardType.DoubleSequnce, player, cards)

	# e.g. 333444555
	def cards_are_triple_sequence(self, cards):
		length = len(cards)

		if length % 3 != 0 or length < 6:
			return False

		value_list = []
		for card in cards:
			value_list.append(card['value'])

		# 2 and Joker need to be excluded.
		if max(value_list) > 13:
			return False

		group = length / 3
		sorted_list = sorted(value_list)

		if sorted_list[0] != sorted_list[1]:
			return False

		for i in range(3):
			last = sorted_list[i]
			for j in range(1, group):
				if sorted_list[i + j * 3] != last + 1:
					return False

				last = sorted_list[i + j * 3]

		return True

	def cards_are_valid_triple_sequence(self, player, cards):
		return self.cards_are_valid_core(CardType.TripleSequnce, player, cards)

	# e.g. AAA2
	def cards_are_triple_single(self, cards):
		length = len(cards)

		if length != 4:
			return False

		value_list = []

		for card in cards:
			value_list.append(card['value'])
		value_list = sorted(value_list)

		return (value_list.count(value_list[0]) == 1 and value_list.count(value_list[3]) == 3) or \
		       (value_list.count(value_list[0]) == 3 and value_list.count(value_list[3]) == 1)

	def cards_are_valid_triple_single(self, player, cards):
		return self.cards_are_valid_core(CardType.TripleSingle, player, cards)

	# e.g. AAA22
	def cards_are_triple_double(self, cards):
		length = len(cards)

		if length != 5:
			return False

		value_list = []
		for card in cards:
			value_list.append(card['value'])

		value_set_list = list(set(value_list))
		if len(value_set_list) != 2:
			return False

		return (value_list.count(value_set_list[0]) == 2 and value_list.count(value_set_list[1]) == 3) or \
		       (value_list.count(value_set_list[0]) == 3 and value_list.count(value_set_list[1]) == 2)

	def cards_are_valid_triple_double(self, player, cards):
		return self.cards_are_valid_core(CardType.TripleDouble, player, cards)

	def cards_are_quadruple_double(self, cards):
		length = len(cards)

		if length != 6 or length != 8:
			return False

		value_list = []
		for card in cards:
			value_list.append(card['value'])
		
		value_set_list = list(set(value_list))

		if len(value_set_list) != 6:
			return False

		# Joker is not allowed.
		if max(value_set_list) > 13:
			return False

		if length == 6:
			# e.g. 346666
			if sorted_list.count(value_set_list[0]) == 1 and \
			   sorted_list.count(value_set_list[1]) == 1 and \
			   sorted_list.count(value_set_list[2]) == 4:
			   return True

			# e.g. 366667
			if sorted_list.count(value_set_list[0]) == 1 and \
			   sorted_list.count(value_set_list[1]) == 4 and \
			   sorted_list.count(value_set_list[2]) == 1:
			   return True

			# e.g. 333367
			if sorted_list.count(value_set_list[0]) == 4 and \
			   sorted_list.count(value_set_list[1]) == 1 and \
			   sorted_list.count(value_set_list[2]) == 1:
			   return True

		elif length == 8:
			# e.g. 33446666
			if sorted_list.count(value_set_list[0]) == 2 and \
			   sorted_list.count(value_set_list[1]) == 2 and \
			   sorted_list.count(value_set_list[2]) == 4:
			   return True

			# e.g. 33666677
			if sorted_list.count(value_set_list[0]) == 2 and \
			   sorted_list.count(value_set_list[1]) == 4 and \
			   sorted_list.count(value_set_list[2]) == 2:
			   return True

			# e.g. 33336677
			if sorted_list.count(value_set_list[0]) == 4 and \
			   sorted_list.count(value_set_list[1]) == 2 and \
			   sorted_list.count(value_set_list[2]) == 2:
			   return True

		return False

	def cards_are_valid_quadruple_double(self, player, cards):
		return self.cards_are_valid_core(CardType.QuadrupleDouble, player, cards)

	def cards_are_plane(self, cards):
		single_list = []
		double_list = []
		sequence_list = []
		value_list = []
		sorted_list = []

		for card in cards:
			value_list.append(card['value'])

		for value in set(value_list):
			if value_list.count(value) > 3:
				return False

			if value_list.count(value) == 1:
				single_list.append(value)

			if value_list.count(value) == 2:
				double_list.append(value)

			if value_list.count(value) == 3:
				sequence_list.append(value)

		if len(single_list) != 0 and len(double_list) != 0:
			return False

		# Joker is not allowed.
		if max(value_list) > 13:
			return False

		sorted_list = sorted(sequence_list)
		length = len(sorted_list)
		last = sorted_list[0]

		for i in range(1, length):
			if sorted_list[i] != last + 1:
				return False

			last = sorted_list[i]

		return True

	def cards_are_valid_plane(self, player, cards):
		return self.cards_are_valid_core(CardType.Plane, player, cards)

	def cards_are_bomb(self, cards):
		length = len(cards)

		# Joker Bomb
		if length == 2 and \
		   ((cards[0]['value'] == 13 and cards[1]['value'] == 14) or \
		   (cards[0]['value'] == 14 and cards[1]['value'] == 13)):
			return True
		elif length == 4 and \
			 cards[0]['value'] == cards[1]['value'] and \
			 cards[0]['value'] == cards[2]['value'] and \
			 cards[0]['value'] == cards[3]['value']:
			return True

		return False

	def cards_are_valid_bomb(self, player, cards):
		return self.cards_are_valid_core(CardType.Bomb, player, cards)

	def generic_compare(self, key_len, old, new):
		if len(old) != len(new):
			return False

		old_value_list = []
		new_value_list = []
		
		for i in range(len(old)):
			old_value_list.append(old[i]['value'])
			new_value_list.append(new[i]['value'])

		old_value_set = set(old_value_list)
		new_value_set = set(new_value_list)

		old_keys = []
		new_keys = []
		for each in old_value_set:
			if old_value_list.count(each) == key_len:
				old_keys.append(each)

		for each in new_value_set:
			if new_value_list.count(each) == key_len:
				new_keys.append(each)

		debug('old_keys: %s, new_keys: %s' % (old_keys, new_keys))
		return min(old_keys) < min(new_keys)

	def bomb_compare(self, unused, old, new):
		if len(new) == 2:
			return True

		if len(old) == 2:
			return False

		return old[0]['value'] < new[0]['value']

	def cards_are_valid(self, player, cards):
		if cards == []:
			# Passing forever is not allowed.
			if self.last_cards['player'] == player:
				return CardType.Invalid
			else:
				return CardType.Pass

		if self.cards_are_valid_single(player, cards):
			return CardType.Single
		elif self.cards_are_valid_double(player, cards):
			return CardType.Double
		elif self.cards_are_valid_triple(player, cards):
			return CardType.Triple
		elif self.cards_are_valid_single_sequence(player, cards):
			return CardType.SingleSequnce
		elif self.cards_are_valid_double_sequence(player, cards):
			return CardType.DoubleSequnce
		elif self.cards_are_valid_triple_sequence(player, cards):
			return CardType.TripleSequnce		
		elif self.cards_are_valid_triple_single(player, cards):
			return CardType.TripleSingle
		elif self.cards_are_valid_triple_double(player, cards):
			return CardType.TripleDouble
		elif self.cards_are_valid_quadruple_double(player, cards):
			return CardType.QuadrupleDouble
		elif self.cards_are_valid_plane(player, cards):
			return CardType.Plane
		elif self.cards_are_valid_bomb(player, cards):
			return CardType.Bomb

		return CardType.Invalid

	def play(self, player, cards):
		# Game is over.
		if self.over == True:
			return BeatLordRet.GameOver

		# Not this player's round.
		if player != (self.last_player + 1) % 3:
			return BeatLordRet.NotHisRound

		ret = self.cards_are_valid(player, cards)
		if ret != CardType.Invalid:
			if cards != []:
				self.last_cards = {
					'cards': cards,
					'player': player,
					'type': ret
				}
				debug('cards: %s to remove' % cards)
				debug("player's cards: %s" % self.players[player]['cards'])
				for card in cards:
					debug('remove1: %s' % (card))
					self.players[player]['cards'].remove(card)
				debug("player's cards: %s" % self.players[player]['cards'])
				debug("last_cards: %s" % (self.last_cards))

		else:
			return BeatLordRet.InvalidCards

		# Game over.
		if len(self.players[player]['cards']) == 0:
			self.over = True
			return BeatLordRet.GameOver

		self.last_player = player

		return card_type_transfer_to_ret(ret)
