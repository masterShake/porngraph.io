import nose
import unittest
import mock
import json
import io
from httpretty import HTTPretty, httprettified
import pytumblr
from urlparse import parse_qs
from BeautifulSoup import BeautifulSoup
from sets import Set
import re
import unicodedata
import MySQLdb
import sys
import nltk
import numpy
from nltk.tree import *
import collections
#import words_to_remove

client = pytumblr.TumblrRestClient('o5sbJulJuIsZPa3CZEPhRWxLGUAxLYhuaQiPuWT1smcJIgwkOd')

#some required global variables
start_gay = 1
start_type = "amateur"

#initialize and populate dictionary/cache with sanitized blog urls and NSFW status
# NSFW = {}
# cursor.execute('''SELECT * FROM nsfw''')
# entries = cursor.fetchall()
# for entry in entries:
# 	NSFW[entry[1]] = entry[2]

#create a video class to instantiate video objects and their associated data
class text_information:
	def __init__(self, slug, caption, tags):
		self.slug = slug #list
		self.tags = tags #list
		self.caption = caption #list
		self.comments = [] #list

class video:
	def __init__(self, e_code, p_url, form, text_i):
		self.embed_code = e_code
		self.post_url = p_url
		self.format = form
		self.text_info = text_i #text_information objects
		self.rebloggers = [] #stack of reblogger objects
		self.total_rebloggers = 0
		self.total_NSFW = 0
	#locates all the rebloggers and processes their information
	#def rebloggerFinder(self):
		#retreive post notes


		#qqq = client.posts('amateurgay', limit=20, offset=20, notes_info='true', type='video')
		#print(json.dumps(qqq, indent=1))
		

		#place all rebloggers on the stack self.rebloggers
		#self.rebloggers.append(bloggerObjectBuilder(urlSterilizer(blog)))

		#place all comments in text information list object

		#perform count on ntlk comments
	#must sanitize the url by removing the http:// and ensuring it ends in .tumblr.com
	def recursiveRebloggerFinder(self, note_url, blog):
		#first get the HTML
		try:
			htmltext = urllib.urlopen(note_url).read()
		except:
			print("404 bitch we have a problem, bad note link")
			return
		soup = BeautifulSoup(htmltext)

		#THIS PIECE OF CODE IS RUNNING TWICE...
		#places the reblogger urls on the stack that it finds in the soup
		def r(rblog):
			nBlog = bloggerObjectBuilder(urlSterilizer(rblog))
			self.rebloggers.append(nBlog)
			self.total_rebloggers = self.total_rebloggers + 1
			print(nBlog.b_name)
			return
		for t in soup.find_all(class_=re.compile(r"note")):
			for tags in t.find_all(class_=re.compile(r"reblog")):
				#create blogger object
				rblogger = tags.a['href']
				# print(rblogger)
				if len(self.rebloggers) > 0:
					if next((x for x in self.rebloggers if x.b_url == rblogger), None) == None:
						r(rblogger)
				else:
					r(rblogger)

					#print(new_blog.b_url)
					#if blog is in cache, add to mysql xtable
					#if blog is not in cache, add to cache, add blog to db, add to xtable
					#update nsfw numbers for video object
					#update number of gay associaitions and total associations

		#grabs all the comments
		for blockquote in soup.find_all('blockquote'):
			for a in blockquote.find_all('a'):
				word_list = a.string.encode('ascii',errors='ignore')
				#filter out plugs
				urls = re.findall(r'http|\.com|\.co|\.net|\.tumblr|\.org|www', word_list)
				if len(urls)<1:
					#Separate key_words and add to list for furter analysis when complete
					key_words = nltkAnalysis(word_list.lower())
					if key_words != None:
						self.text_info.comments = self.text_info.comments + key_words

		#look for the next "show more notes" link recursively
		show_more_links = soup.find("a", { "class" : "more_notes_link" })# this line is broken!
		print type(show_more_links['onclick'])
		m = re.search(r"/notes/\d*/\w*\?from_c\=\d*", show_more_links['onclick'])
		print(type(m.group()))
		if m == "":
		
			print("total rebloggers: " + str(self.total_rebloggers))
			print("total NSFW: " + str(self.total_NSFW))

			#this is where we will perform statistical analysis on the text
			#decide whether or not this video is pornographic enough

			#insert into the database
			count = collections.Counter(self.text_info.comments)
			for d in words_to_remove.bad:
				if d in count:
					del count[d]
			print(count.most_common(30))
			return
		# m = soup.find_all(class_=re.compile(r"more_notes_link"))
		# print("HERE IS A NEW RECURSIVE CALL" + self.post_url + m[0])
		
		self.recursiveRebloggerFinder(self.post_url + m.group(), blog)


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

	#info for first 20 video posts
	def getVideos(self): # blog --> "someblog.tumblr.com"
		i=0
		posts = client.posts(self.b_name + ".tumblr.com", limit=20, type='video')['posts']
		while i<20:
			blood = True
			if blood == True:
				# #check if video is already in database
				# cursor.execute('''SELECT * FROM videos WHERE player=%s''', posts[i]['player'][0]['embed_code'])
				# rows = cursor.fetchall()
			
				# #this database insertion should be moved to the end of recursiveReblogger
				# if not any(posts[i]['player'][0]['embed_code'] in row for row in rows):
				# 	cursor.execute('''INSERT into videos(url, player, slug) VALUES("url placeholder", %s, %s)''', (posts[i]['player'][0]['embed_code'], posts[i]['slug']))
				# 	con.commit()

				#create the video object	
				embed_code = posts[i]['player'][0]['embed_code']
				post_url = posts[i]['post_url']
				da_format = posts[i]['format']
				#for slug: replace hyphens with spaces, ntlk tokenize
				slug = nltk.word_tokenize(posts[i]['slug'].encode('ascii',errors='ignore').replace('-', ' '))
				#for caption: use beautiful soup to get ONLY text in p tag, tokenize
				a = posts[i]['caption'].encode('ascii',errors='ignore')
				caption = []
				if a != "":
					b = BeautifulSoup(a)('p')[-1].extract().string
					if b != None:
						b.encode('ascii', errors='ignore')
						caption = caption + nltk.word_tokenize(b)
				tags = posts[i]['tags']
				tag_holder = [str(t) for t in tags]
				#store the video objects in the unvisited_posts list
				self.unvisited_posts.insert(0, video(embed_code, post_url, da_format, text_information(slug, caption, tag_holder)))
				#print(self.unvisited_posts[i].post_url)
				print()
			else:
				print(str(i) + ": this video didn't work")
			i=i+1

#THIS METHOD SHOULD BE UNIVERSALLY AVAILABLE
def urlSterilizer(url):
	url = re.sub(r"http://", "", url)
	url = re.match(r'^.*?\.com', url).group(0)
	return url

#THIS METHOD SHOULD BE UNIVERSALLY AVAILABLE
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

#THIS METHOD SHOULD BE UNIVERSALLY AVAILABLE
def bloggerObjectBuilder(blog):
	meta = client.blog_info(blog)['blog']
	#retrieve the variable data and create the blogger object
	b = blogger(meta['name'], meta['url'], meta['title'], meta['is_nsfw'], start_type, start_gay)
	return b


start = bloggerObjectBuilder("amateurgay.tumblr.com")
start.getVideos()
