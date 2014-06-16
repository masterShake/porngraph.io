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
from py2neo import neo4j, node, rel
from collections import Counter
import unicodedata
import categories

####################################################

#		initialize some global variables

####################################################

#the main class that allows us access to the api
client = pytumblr.TumblrRestClient(
  'H3gOUtqVK9Q1wrfQYr3k5tZIBXEqQQ3JK90eS6oQcxtZDIEUYW',
  'HoB24u7inyC9dhdH3AZL9OxMhMHqSWTQHoUqsDaL4L0mQK985Q',
  'rgHNvDs8ulcuLe5Oo4FTR3pHQgejySzelt6OU5UGHp8hVWv7Pf',
  'a0QWSvyCM6fcgjeRxyLYs6c4TTolAgEdJhD0Pg8Er2eejO8oj9'
)
#the main class that allows us access the database
graph_db = neo4j.GraphDatabaseService("http://www.faprehab.com:7474/db/data/")
#a sexuality score
is_gay = 0
#one of several hundred predetermined porn categories
begin_category = {"amateur" : 1, "college": 1}

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
	def __init__(self, e_code, p_url, form, text_i, vtype, isGay=0):
		self.embed_code = e_code#.encode('ascii', 'ignore')
		self.post_url = p_url#.encode('ascii', 'ignore')
		self.format = form#.encode('ascii', 'ignore')
		self.text_info = text_i #text_information objects
		self.category = vtype #dictionary of starting values
		self.rebloggers = [] #stack of reblogger objects
		self.total_rebloggers = 0
		self.total_NSFW = 0
		self.percent_gay = isGay

	####################################################

	#				video methods

	####################################################

	#creates blogger objects and appends them to self.rebloggers list
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
				x = bloggerObjectBuilder(a.text)
				b = False
				for y in self.rebloggers:
					if x.b_name == y.b_name:
						b = True
				if b == False:
					self.rebloggers.append(x)
				b = False
			for a in li.findAll(True, {'class': re.compile(r'\bsource_tumblelog\b')}):
				x = bloggerObjectBuilder(a.text)
				b = False
				for y in self.rebloggers:
					if x.b_name == y.b_name:
						b = True
				if b == False:
					self.rebloggers.append(x)
				b = False

	#analyzes data and stores it in the database
	def analyzeAndUpload(self):
		#turn blog.category dictionary into a neo4j string
		def createPropString(d):#takes in a dictionary
			st = "{"
			for key, value in d.iteritems():
				st = st + key +': '+ str(value) +', '
			st = st[:-2]
			st = st + '}'
			return st #returns a string
		#turn the python boolean into a neo4j string
		def boolToString(boo):
			if(boo == True):
				boo = "true"
			else:
				boo = "false"
			return boo
		#match the video in database
		query = neo4j.CypherQuery(graph_db, "MATCH (v:Video) WHERE v.embed_code = '"+self.embed_code+"' RETURN v;").execute()
		if not query:
			neo4j.CypherQuery(graph_db, "CREATE (v:Video {embed_code: \'" + self.embed_code + "\', post_url: \'"+self.post_url+"\', format: \'"+self.format+"\'})").execute()
			print "new video added"
		#blogs in database
		for blog in self.rebloggers:
			#check if that reblogger already exists in the database
			query2 = neo4j.CypherQuery(graph_db, "MATCH (b:Blogger {name: \""+blog.b_name+"\"}) RETURN b").execute()
			#if blogger already exists
			if query2:
				for blog_key, blog_val in blog.category.iteritems():
					neo4j.CypherQuery(graph_db, """MATCH (b:Blogger {name: \""""+blog.b_name+"""\"}), (c:Category {name: \""""+blog_key+"""\"}) MERGE (b)-[r:PORN_TYPE]-(c) ON CREATE SET r.connections="""+str(blog_val)+""" ON MATCH SET r.connections= r.connections+"""+str(blog_val)).execute()
				print "blog found: "+blog.b_name
			else:
				#create the blogger node, create a relationship between the blogger and the video
				neo4j.CypherQuery(graph_db, """MATCH (v:Video) WHERE v.embed_code = '"""+self.embed_code+"""' 
													   CREATE (b:Blogger {name: \"""" + blog.b_name + """\", url: \""""+blog.b_url+"""\", title: \""""+blog.b_title+"""\", nsfw: """+boolToString(blog.b_nsfw)+""", total_videos: 1})-[r:REBLOGGED]->(v)""").execute()
				#create relationship between the categories and the blogger
				for key, value in begin_category.iteritems():
					neo4j.CypherQuery(graph_db, "MATCH (c:Category {name:'"+key+"'}) MATCH (b:Blogger) WHERE b.name = '"+blog.b_name+"' CREATE UNIQUE (c)-[r:PORN_TYPE {connections: "+str(value)+"}]-(b)").execute()
				print "new blog added: "+blog.b_name
		for blog in self.rebloggers:
			query4 = neo4j.CypherQuery(graph_db, """MATCH (b:Blogger {name: \""""+blog.b_name+"""\"})-[r:PORN_TYPE]-(c:Category) RETURN c.name, r.connections;""")
			for record in query4.stream():
				blog.category[record["c.name"]] = record["r.connections"]
			#add up all blogger dictionary values
			self.category = Counter(self.category) + Counter(blog.category)
		#use those values to create relationships between video and categories
		for key, value in self.category.iteritems():
			neo4j.CypherQuery(graph_db, """MATCH (v:Video {embed_code: '"""+self.embed_code+"""'}),
										(c:Category {name: '"""+key+"""'})
										MERGE (v)-[r:PORN_TYPE]-(c)
										ON CREATE SET r.connections="""+str(value)+""" 
										ON MATCH SET r.connections= r.connections+"""+str(value)).execute()

####################################################

#					blogger class

####################################################

class blogger:
	def __init__(self, bname, url, title, isNsfw, btype, isGay=0):
		self.b_name = bname
		self.b_url = url
		self.b_title = title
		self.b_nsfw = isNsfw
		self.percent_gay = isGay
		self.b_totalVideos = 1
		self.category = btype #dictionary of values starting value of 1 for first category
		self.unvisited_posts = []

	####################################################

	#					blogger methods

	####################################################
	def getVideos(self):
		posts = client.posts(self.b_name + ".tumblr.com", type='video', limit=20, filter='text')['posts']
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
			self.unvisited_posts.insert(0, video(embed_code, post_url, da_format, text_information(slug, caption, tag_holder), begin_category))
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
	b = blogger(meta['name'], meta['url'], meta['title'], meta['is_nsfw'], begin_category, is_gay)
	return b

####################################################

#					tests

####################################################

#print json.dumps(your_json_object_here, indent=1)

#clear and repopulate database with categories
# query = neo4j.CypherQuery(graph_db, "MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r").execute()
# query = neo4j.CypherQuery(graph_db, categories.cats).execute();

#python tests
start = bloggerObjectBuilder("a-little-alone-time.tumblr.com")
start.getVideos()
start.unvisited_posts[0].getRebloggers()
start.unvisited_posts[0].analyzeAndUpload()
# for x in start.unvisited_posts:
# 	x.getRebloggers()
# 	x.analyzeAndUpload()