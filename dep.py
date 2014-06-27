import os


class AbstractDep:
	def __init__(self, name = None, parent = None):
		self.name = name
		
		self.__parent = None
		self.parent = parent
		self.children = []
		
		self.__deps = []
		self.blocks = []
		self.settings = {
			"status": "",
			"name": None,
			"description": None
		}
	
	
	@property
	def parent(self):
		return self.__parent
	
	
	@parent.setter
	def parent(self, parent):
		if self.__parent is not None:
			self.__parent.children.remove(self)
		
		self.__parent = parent
		
		if parent is not None:
			parent.children.append(self)
	
	
	def applySettings(self, settings):
		self.settings.update(settings)
	
	
	def getDisplayName(self):
		if self.settings["name"] is None:
			return self.name
		else:
			return self.settings["name"]
	
	
	def getStatus(self):
		for block in self.blocks:
			for exit in block.getExits():
				if exit.getStatus() != "done":
					return "blocked"
		
		if self.settings["status"] == "done":
			return "done"
		else:
			return "open"
	
	
	def getAncestors(self):
		ancestors = []
		curDep = self
		while curDep.parent is not None:
			ancestors.append(curDep.parent)
			curDep = curDep.parent
		
		ancestors.reverse()
		return ancestors
	
	
	def getFqn(self):
		ancestors = self.getAncestors()
		ancestors.append(self)
		
		return "_".join([ancestor.name for ancestor in ancestors[1:]])
	
	
	def addDep(self, dep):
		if dep not in self.__deps:
			self.__deps.append(dep)
			dep.blocks.append(self)
	
	
	def removeDep(self, dep):
		if dep in self.__deps:
			self.__deps.remove(dep)
			dep.blocks.remove(self)
	
	
	def getDeps(self):
		return self.__deps



class Dep(AbstractDep):
	def getEntries(self):
		return [self]
	
	
	def getExits(self):
		return [self]


class Container(AbstractDep):
	def __init__(self, name = None, parent = None):
		super().__init__(name, parent)
		self.__start = VirtualDep("_start", self, self)
		self.__end   = VirtualDep("_end", self)
	
	
	def getStatus(self):
		return self.__end.getStatus()
	
	
	def getStart(self):
		return self.__start
	
	
	def getEnd(self):
		return self.__end
	
	
	def getEntries(self):
		return [self.__start]
	
	
	def getExits(self):
		return [self.__end]


class VirtualDep(Dep):
	def __init__(self, name = None, parent = None, blockSource = None):
		super().__init__(name, parent)
		
		if blockSource is None:
			self.__blockSource = self
		else:
			self.__blockSource = blockSource
	
	def getStatus(self):
		for block in self.__blockSource.blocks:
			for exit in block.getExits():
				if exit.getStatus() != "done":
					return "blocked"
		
		return "done"



class SettingsFile:
	def __init__(self, path):
		self.path = path
		self.__curLineNr = 1
		self.__multiline = False
		self.__multilineText = None
		self.settings = {}
		self.parse()
	
	
	def parse(self):
		with open(self.path) as f:
			for line in f.readlines():
				self.__parseLine(line.replace("\n", ""))
				self.__curLineNr += 1
		
		if self.__multiline:
			raise Exception(
				"Multiline block was not closed properly by ~~~ in file '%s'" %
				self.path
			)
	
	
	def __parseLine(self, line):
		if self.__multiline:
			self.__parseMultiline(line)
		else:
			self.__parseSingleline(line)
	
	
	def __parseSingleline(self, line):
		## More multiline text
		if line != "~~~":
			if self.__multilineText is None:
				self.__multilineText = line
			else:
				self.__multilineText += "\n%s" % line
		
		## End
		else:
			if self.__multilineText is None:
				self.settings[self.key] = ""
			else:
				self.settings[self.key] = self.__multilineText
			self.__multilineText = None
			self.__multiline = False
	
	
	def __parseSingleline(self, line):
		parts = line.split(":", 1)
		if len(parts) < 2:
			if line.strip() != "":
				raise Exception("Can't parse line %i in file '%s' (%s)" % (
					self.__curLineNr,
					self.path,
					line
				))
			
			return
		
		key = parts[0]
		if key != key.strip():
			raise Exception("Unknown key \"%s\" on line %i in file '%s'" % (
				key,
				self.__curLineNr,
				self.path
			))
		
		value = parts[1].strip()
		if value != "":
			self.settings[key] = value
		else:
			self.__multiline = True


class Settings:
	def __init__(self, d = "."):
		self.__d = d
		self.__settings = {}
		self.__check()
	
	
	def __pathDsc(self, d, name):
		path = os.path.join(d, name)
		relPath = os.path.relpath(path, self.__d)
		
		if os.path.isfile(path):
			return "file '%s'" % relPath
		else:
			return "directory '%s'" % relPath
	
	
	def __checkTupel(self, dirname, a, b):
		if a.startswith(b):
			raise Exception("%s is part of %s" % (
				self.__pathDsc(dirname, b),
				self.__pathDsc(dirname, a)
			))
		
		if b.startswith(a):
			raise Exception("%s is part of %s" % (
				self.__pathDsc(dirname, a),
				self.__pathDsc(dirname, b)
			))
	
	
	
	def __check(self):
		#    F F F F D D D D
		#   +----------------+
		# F |        ********|
		# F |        ********|
		# F |        ********|
		# F |        ********|
		# D |********  ******|
		# D |**********  ****|
		# D |************  **|
		# D |**************  |
		#   +----------------+
		for dirname, ds, fs in os.walk(self.__d):
			for f in fs:
				for d in ds:
					self.__checkTupel(dirname, f, d)
			
			for i in range(1, len(ds)):
				for j in range(i):
					self.__checkTupel(dirname, ds[i], ds[j])
			
			for f in fs:
				path = os.path.join(dirname, f)
				uid = os.path.relpath(path, self.__d).replace("/", "_")
				self.__settings[uid] = path
	
	def getSettingsFor(self, name):
		if name in self.__settings:
			sf = SettingsFile(self.__settings[name])
			return sf.settings
		
		else:
			return {}
	
	
