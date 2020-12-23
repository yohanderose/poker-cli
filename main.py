import time
import os
import sys
from random import shuffle

import ueberzug.lib.v0 as ueberzug
from multiprocessing import Pool

from itertools import groupby
from more_itertools import consecutive_groups
from operator import itemgetter
from PIL import Image
import subprocess

class Card(object):

	def __init__(self, suit, rank, image):
		self.suit = suit
		self.rank = rank
		self.image = image
		try:
			self.num = int(self.rank)
		except ValueError:
			if self.rank == "K":
				self.num = 13
			if self.rank == "Q":
				self.num = 12
			if self.rank == "J":
				self.num = 11
			if self.rank == "A":
				self.num = 14

	def __str__(self):
		return str(self.rank) + str(self.suit)

	def __repr__(self):
		return str(self.rank) + str(self.suit)

	def __lt__(self, other):
		return self.num < other.num
    
	def __gt__(self, other):
		return self.num > other.num


def display_card(path, displace=(0,0)):
	with ueberzug.Canvas() as c:

		demo = c.create_placement(path, x=0, y=0, scaler=ueberzug.ScalerOption.COVER.value)
		demo.path = path
		demo.visibility = ueberzug.Visibility.VISIBLE

		with c.lazy_drawing:
			demo.x = 0
			demo.y = 0
			demo.path = path
		time.sleep(2)

def display_table(house, hand, displace=(0,0)):
	house_images = [Image.open(x) for x in house]
	hand_images = [Image.open(x) for x in hand]
	widths, heights = zip(*(i.size for i in house_images))

	total_width = sum(widths)
	total_height = house_images[0].height * 2

	final_img = Image.new('RGB', (total_width, total_height))
	x_offset = 0
	for im in house_images:
		final_img.paste(im, (x_offset, 0))
		x_offset += im.width

	x_offset = 0
	y_offset = hand_images[0].height
	for im in hand_images:
		final_img.paste(im, (x_offset, y_offset))
		x_offset += im.width

	# Find aspect ratio of final image and resize to terminal width
	rows, cols = os.popen('stty size', 'r').read().split()
	rows = int(rows) * 8.5
	cols = int(cols) * 8.5
	aspect = final_img.height/final_img.width
	new_width = int(cols)
	new_height = int(cols * aspect)

	final_img = final_img.resize((new_width, new_height))
	final_img.save('heyo.png')

	with ueberzug.Canvas() as c:

		demo = c.create_placement('heyo.png', x=0, y=0, 
								scaler=ueberzug.ScalerOption.COVER.value)
		demo.path = 'heyo.png'
		demo.width = final_img.width
		demo.height = final_img.height
		demo.visibility = ueberzug.Visibility.VISIBLE

		tmp = input()

	# TODO: make this only able to remove this file (in root project dir)
	# subprocess.run('rm heyo.png'.split())

def reset():
	deck = []
	
	for filename in os.listdir('./cards'):

		rank = "".join(list(filename.split('.')[0])[:-1])
		suit = list(filename.split('.')[0])[-1]
		
		deck.append(Card(suit, rank, './cards/' + filename))

	shuffle(deck)
	return deck
		

def analyse_play(play, suits_inplay, nums_inplay):
	result = ""
	for suit in suits_inplay.keys():
		# Flush, same suit, not in sequence
		if len(suits_inplay[suit]) > 4:
			result = "5/10 flush"
			l = sorted(suits_inplay[suit])

			# Straight Flush, same suit in sequence
			if l == list(range(min(l), max(l)+1)):
				result = "2/10 straight flush"
			
			if l[-5:] == range(10, 14):
				result = "1/10 royal flush"

			return result

	two_kind = 0
	three_kind = 0
	four_kind = 0
	for num in nums_inplay.keys():
		if nums_inplay[num] == 2:
			two_kind += 1
		if nums_inplay[num] == 3:
			three_kind += 1
		if nums_inplay[num] == 4:
			four_kind += 1

	if four_kind > 0:
		result = "3/10 four of a kind"
	elif three_kind > 0:
		result = "7/10 three of a kind"
		if two_kind > 0:
			result = "4/10 full house"
	elif two_kind > 0:
		result = "9/10 pair" 
		if two_kind > 1:
			result  = "8/10 two pair" 

	nums = [card.num for card in play]
	grouped = [list(i) for i in consecutive_groups(nums)]

	if len(max(grouped, key=len)) > 5:
		result = "6/10 straight"

	if result == "":
		result = "10/10 " + str(play[-1])

	return result

if __name__ == '__main__':
	# paths = ['./cards/3D.png', './cards/8C.png']
	deck = reset()

	while True:
		if len(deck) < 7:
			deck = reset()

		house = deck[:5]
		deck = deck[5:]
		hand = deck[:2]
		deck = deck[2:]

		play = sorted(house + hand)
		suits = "C H S D"
		suits_inplay = dict(zip(suits.split(), [[], [], [], []]))
		nums_inplay = dict(zip(range(1,15), [0]*14))

		for card in play:
			suits_inplay[card.suit].append(card.num)
			nums_inplay[card.num] += 1

		result = analyse_play(play, suits_inplay, nums_inplay)

		display_table([card.image for card in house], [card.image for card in hand])

		# print(play)
		# print(suits_inplay)
		# print(nums_inplay)

		print(result)
