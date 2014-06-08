####################################################

#		import all the necessary dependencies

####################################################

import nose
import unittest
import mock
import json
import io
from httpretty import HTTPretty, httprettified
import pytumblr
from urlparse import parse_qs
import urllib
from BeautifulSoup import BeautifulSoup
from sets import Set
import re
import unicodedata
import sys
import nltk
import numpy
from nltk.tree import *
import collections
import words_to_remove

####################################################

#		initialize some global variables

####################################################

#the main class that allows us to access to the api
client = pytumblr.TumblrRestClient('o5sbJulJuIsZPa3CZEPhRWxLGUAxLYhuaQiPuWT1smcJIgwkOd')
#a sexuality score
is_gay = 0
#one of several hundred predetermined porn categories
category = "big titties"

####################################################

#			create the video class

####################################################

#subclass of video 
#holds all related strings for analysis
#maintains all information in the form of a list
class text_information:
	def __init__(self, slug, caption, tags):
		self.slug = slug #list
		self.tags = tags #list
		self.caption = caption #list
		self.comments = [] #list

#video object 
class video:
	def __init__(self, e_code, p_url, form, text_i):
		self.embed_code = e_code
		self.post_url = p_url
		self.format = form
		self.text_info = text_i #text_information objects
		self.rebloggers = [] #stack of reblogger objects
		self.total_rebloggers = 0
		self.total_NSFW = 0

	####################################################

	#				video methods

	####################################################
	def getRebloggers(self):
		#error handling if the link does not work
		try:
			htmltext = urllib.urlopen(self.post_url)
		except:
			print("this link did not work")
			return
		#create soup object of html
		soup = BeautifulSoup(htmltext)
		#nested function for building blogger object and appending them to video.rebloggers
		def reblogStackBuilder(blog): #blog is a string of the form http://someblog.tumblr.com/
			newBlog = bloggerObjectBuilder(urlSterilizer(blog))
			self.rebloggers.append(newBlog)
			self.total_bloggers = self.total_rebloggers + 1
			print newBlog.b_name
		for li in soup.findAll(True, {'class': re.compile(r'\breblog\b')}):
			for a in li.findAll(True, {'class': re.compile(r'\btumblelog\b')}):
				self.rebloggers.append(a.text)
			for a in li.findAll(True, {'class': re.compile(r'\bsource_tumblelog\b')}):
				if a.text not in self.rebloggers:
					self.rebloggers.append(a.text)

####################################################

#					blogger class

####################################################

class blogger:
	def __init__(self, bname, url, title, isNsfw, btype, isGay=0):
		self.b_name = bname
		self.b_url = url
		self.b_title = title
		self.b_nsfw = isNsfw
		self.b_gayAsso = isGay
		self.b_totalAsso = 1
		self.b_type = {btype : 1} #starting value of 1 for first category
		self.unvisited_posts = []

	####################################################

	#					blogger methods

	####################################################
	def getVideos(self):
		posts = client.posts(self.b_name + ".tumblr.com", limit=20, filter='text', type='video')['posts']
		i=0
		while i<len(posts):
			#create the video object	
			embed_code = posts[i]['player'][2]['embed_code']
			post_url = posts[i]['post_url']
			da_format = posts[i]['format']
			#for slug: replace hyphens with spaces, ntlk tokenize
			slug = nltk.word_tokenize(posts[i]['slug'].replace('-', ' '))
			#for caption: use beautiful soup to get ONLY text in p tag, tokenize
			caption = nltk.word_tokenize(posts[i]['caption'])
			tags = posts[i]['tags']
			tag_holder = [str(t) for t in tags]
			#store the video objects in the unvisited_posts list
			self.unvisited_posts.insert(0, video(embed_code, post_url, da_format, text_information(slug, caption, tag_holder)))
			#print(self.unvisited_posts[i].post_url)
			i=i+1


####################################################

#				global functions

####################################################

#this function's input is of the form http://somepornblog.tumblr.ocm
#its output would would be somepornblog
def urlSterilizer(url):
	url = re.sub(r"http://", "", url)#replace the http:// with nothing
	url = re.match(r"^.*?\.com", url).group(0)#idk but it removes .tumblr.com
	return url

#creates a string of nouns and verbs
def nltkAnalysis(string):
	tokenized = nltk.word_tokenize(string)
	tagged = nltk.pos_tag(tokenized)
	spare = []
	#define our chunks here
	chunkGram = r"""NP: {<DT>?<JJ>*<NN>}
					VERB: {<VB.*>}"""
	chunkParser = nltk.RegexpParser(chunkGram)
	chunked = chunkParser.parse(tagged)
	for a in chunked:
		if type(a) is nltk.Tree and (a.node == 'NP' or a.node == 'VERB'): # This climbs into your NVN tree
			chunk_list = a.leaves()
			#reconstruct the string
			temp = []
			for c in chunk_list:
				temp.append(c[0])
			#remove all trailing white space and return
			spare = spare + temp
	return spare

#takes in a url and returns a blogger object
def bloggerObjectBuilder(blog):
	meta = client.blog_info(blog)['blog']
	#retrieve the variable data and create the blogger object
	b = blogger(meta['name'], meta['url'], meta['title'], meta['is_nsfw'], category, is_gay)
	return b

####################################################

#					tests

####################################################

#print json.dumps(your_json_object_here, indent=1)

start = bloggerObjectBuilder("onlyamsexvids.tumblr.com")
start.getVideos()
start.unvisited_posts[0].getRebloggers()
print start.unvisited_posts[0].post_url