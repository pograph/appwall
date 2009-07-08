#!/usr/bin/env python

""" 
Your own app wall. v1.1
pograph.wordpress.com
"""
import pygame
from pygame.locals import *
import Image

import feedparser
import re, os, sys, urllib, copy, random
from math import *
from time import time

app_rss_urls = ('http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/ws/RSS/toppaidapplications/sf=143441/limit=300/xml',
	'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/ws/RSS/toppaidapplications/sf=143441/limit=300/genre=6014/xml',
	'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/ws/RSS/toppaidapplications/sf=143441/limit=300/genre=6016/xml',
	'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/ws/RSS/topfreeapplications/sf=143441/limit=100/genre=6005/xml',
	'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/ws/RSS/topfreeapplications/sf=143441/limit=100/genre=6014/xml')
ICON_DIR = 'icons'
ICON_HEIGHT = 53
ICON_WIDTH = 53
	
icon_pattern = re.compile('<img.* src=\"(.*100x100-75\.jpg)\"')
grid_width = 0
grid_height = 0

def id_to_xy(id):
	return id % grid_width, id / grid_width

def xy_to_id(x, y):
	return x + y * grid_width
	
def download_icons(url):
	""" download icons from Apple appstore """
	feed = feedparser.parse(url)
	for item in feed.entries:
		match = icon_pattern.search(item.content[0].value)
		if match:
                        icon_url = match.groups()[0]	# extract icon link
                        icon_url = icon_url.replace('100x100', '53x53')						# get the smallest one
                        icon_file = os.path.join('icons', icon_url.rpartition('/')[2])
                        if not os.path.exists( icon_file):
                                print icon_url, ' => ', icon_file
                                urllib.urlretrieve(icon_url, icon_file)
		
class Icon(pygame.sprite.Sprite):
	def __init__(self, filename):
		pygame.sprite.Sprite.__init__(self)
		
		# load image and add alpha channel
		rgb_chan = Image.open(filename).split()
		alpha_chan = Image.open('template.png').split()
                if len(rgb_chan) >= 3: 
                        image = Image.merge('RGBA', (rgb_chan[0], rgb_chan[1], rgb_chan[2], alpha_chan[0]))
                else:
                        image = Image.merge('RGBA', (rgb_chan[0], rgb_chan[0], rgb_chan[0], alpha_chan[0]))
		
		# convert to pygame image
		image2 = pygame.image.fromstring(image.tostring(), image.size, 'RGBA')
		self.image = image2.convert_alpha()
		self.rect = self.image.get_rect()
		self.orig_rect = copy.deepcopy(self.rect)
		self.z = 0
		
	def move(self, wave, time):
		self.z += wave.delta(self.x, self.y, time);
		if self.z > 1.0:
			self.z = 1.0
		elif self.z < -1.0:
			self.z = -1.0

	def update_pos(self):
		""" fake 3D effect """
		self.rect.left = self.orig_rect.left + self.z * -0.866 * 50
		self.rect.top = self.orig_rect.top + self.z * -0.5 * 50
		
	def sort(x, y):
		if x.z > y.z:
			return 1
		if x.z == y.z:
			return 0
		return -1
	
	
class Wave:
	def __init__(self, x, y, time):
		self.x, self.y, self.time = x, y, time
		self.C = 1.5;
		self.V = 8.0 / self.C;
		self.MAX_TIME = self.C * 1.5;
		self.OMIGA = 2 * pi / self.C;
		self.ET = log(8) / self.C;
		self.ED = log(1.4);
		self.R = 5;
		
	def delta(self, x, y, tnow):
		t = tnow - self.time
		if t > self.MAX_TIME:
			return 0.0
			
		r = sqrt((x - self.x) * (x - self.x) + (y - self.y) * (y - self.y))
			
		if r < self.R and r / self.V <= t <= self.MAX_TIME:
			return sin(self.OMIGA * (t - r / self.V)) * exp(-self.ED * r - self.ET * t)
			
		return 0.0

def z_to_alpha(z):
	if z < -0.5:
		light = 1.0 / 3
	elif z < 0:
		light = (1.0 - z) / 3
	elif z < 0.5:
		light = 0.5 + z
	else:
		light = 1.0
	return (1.0 - light) * 255

def load_files(files):
	img_ext = ('.jpg')
	sprites = []
	print "Loading icons"
	for f in files:
		if len(sprites) == grid_width * grid_height:
			return sprites
		if f[-4:] in img_ext:
                        try:
        			sprites.append(Icon(os.path.join('icons', f)))
        		except:
                                print "ignore error on parsing ", f
                                print sys.exc_info()
                                pass
	return sprites

def assign_sprites(sprites):	
	for i in range(len(sprites)):
		sprites[i].id = i;
		sprites[i].rect.top = (i / grid_width) * ICON_HEIGHT
		sprites[i].rect.left = (i % grid_width) * ICON_WIDTH
		sprites[i].orig_rect = copy.deepcopy(sprites[i].rect)
		sprites[i].x , sprites[i].y = id_to_xy(i)
		
def main():
	global grid_width, grid_height
	print "Welcome to your own App Wall."
	
	pygame.init()
	
	# init grid
	info = pygame.display.Info()
	grid_width = info.current_w / ICON_WIDTH + 1
	grid_height = info.current_h / ICON_HEIGHT + 1
	icons_needed = grid_width * grid_height
	
	# init
	clock = pygame.time.Clock()
	rand = random.Random()
	start_time = time()
	last_change_time = start_time
	waves = []
		
	# download icons if necessary
	if not os.path.exists(ICON_DIR):
		os.mkdir(ICON_DIR)
		
	files = os.listdir('icons')
	if len(files) < icons_needed:
                print "Downloading icons..."
		for url in app_rss_urls:
			download_icons(url)
		files = os.listdir('icons')
		
	if len(files) < icons_needed:
		raise SystemExit, "not enough icons"
		
	# turn into fullscreen mode
	screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
	pygame.mouse.set_visible(False)
	
	# create a black image, use it to simulate lighting effects
	black_image = pygame.Surface((ICON_WIDTH, ICON_HEIGHT))
	black_image = black_image.convert()
	black_image.fill((0, 0, 0))

	# load icons
	sprites = load_files(files)
	if len(sprites) < icons_needed:
                raise SystemExit, "not enough icons"
        
	random.shuffle(sprites)
	assign_sprites(sprites)
	
	while 1:
		clock.tick(60)
                tnow = time()
		for s in sprites:
			s.z = 0
			
		if tnow - last_change_time > 3600:	# re arrange icons every 1 hr
			del waves[:]
			random.shuffle(sprites)
			assign_sprites(sprites)
			last_change_time = tnow
			
		# generate wave
		# remove old one first
		if len(waves) and tnow - waves[0].time > waves[0].MAX_TIME:
			del waves[0]
			
		r1 = random.randint(0, 300)
		if r1 % 149 == 0:
			wave = Wave(random.randint(0, grid_width), random.randint(0, grid_height), tnow)
			waves.append(wave)
		
		# move sprites
		for wave in waves:
			for x in range(wave.x - wave.R, wave.x + wave.R):
				for y in range(wave.y - wave.R, wave.y + wave.R):
					if x >= 0 and x < grid_width and y >=0 and y < grid_height:
						sprites[xy_to_id(x, y)].move(wave, tnow)

		for s in sprites:
			s.update_pos()
			
		# draw sprites
		sprites2 = sprites[:]
		sprites2.sort(Icon.sort)
		
		screen.fill((0, 0, 0))		
		for s in sprites2:
			screen.blit(s.image, s.rect)
			# draw black image above sprite to simulate lighting
			black_image.set_alpha(z_to_alpha(s.z))
			screen.blit(black_image, s.rect)
			
		# process events
		for event in pygame.event.get():
			if event.type == QUIT:
				return
			elif event.type == KEYDOWN and event.key == K_ESCAPE:
				return

		pygame.display.flip()

if __name__ == '__main__':
	main()
