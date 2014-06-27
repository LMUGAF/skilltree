import re
import json
import tokenx


class File():
	def __init__(self, fileName):
		self.__fileName = fileName
		
		self.__lineParser = re.compile(r"""
			^(?P<indent>\t*)
			 (?P<comment>|\#)
			 (?P<name>\S*)
			 (?P<remaining>.*)$""", re.VERBOSE)
		self.__root = tokenx.Token(self, 0, None)
		self.__uppertokens = [self.__root]
		self.__emptyLine = False
		
		self.__parse()
	
	
	def getRoot(self):
		return self.__root
	
	
	def getFileName(self):
		return self.__fileName
	
	
	def __parse(self):
		self.__curLineNr = 1
		
		with open(self.__fileName) as f:
			for line in f.readlines():
				self.__parseLine(line.replace("\n", ""))
				self.__curLineNr += 1
	
	
	def __parseLine(self, line):
		m = self.__lineParser.match(line)
		if(m):
			self.__createDepFromMatch(m)
		else:
			raise Exception("Can't parse line %i '%s'" % (self.__curLineNr, line))
	
	
	def __parseConfig(self, text):
		if(text.strip() == ""):
			return []
		else:
			return json.loads(text)
	
	
	def __createDepFromMatch(self, m):
		## Check for comments
		if(m.group("comment") == "#"):
			return
		
		## Check for empty lines
		if(m.group("name") == ""):
			if(m.group("remaining") != ""):
				raise Exception("Empty line is not empty")
			
			self.__emptyLine = True
			return
		
		## Get Parts
		level = len(m.group("indent"))
		name  = m.group("name")
		conf  = self.__parseConfig(m.group("remaining"))
		
		
		t = tokenx.Token(self, self.__curLineNr, name, conf)
		
		lastLevel = len(self.__uppertokens) - 2
		
		## Old Position:      x
		## New Position:        xxxxx
		if level > lastLevel + 1:
			raise Exception("We went do fast to deep")
		
		## Old Position:      x
		## New Position:       x
		elif level == lastLevel + 1:
			self.__uppertokens[lastLevel + 1].addToCurList(t)
			self.__uppertokens.append(t)
		
		## Old Position:      x
		## New Position: xxxxxx
		else:
			if self.__emptyLine:
				self.__uppertokens[level].switchToNewList()
			
			self.__uppertokens[level].addToCurList(t)
			self.__uppertokens[level + 1] = t
			
			if level < lastLevel:
				self.__uppertokens = self.__uppertokens[:level + 2]
		
		self.__emptyLine = False







class tokenComposer:
	def __init__(self, fileName):
		self.__fileName = fileName
		self.__files = {}
	
	
	
	def getRootFromFile(self, name):
		if not name in self.__files:
			self.__files[name] = File(name)
			self.getRoot().finish(self)
		
		return self.__files[name].getRoot()
	
	
	
	def getRoot(self):
		return self.getRootFromFile(self.__fileName)