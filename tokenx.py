import re
import json
import copy
import dep



class Token:
	def __init__(self, f, line, name = None, config = {}):
		self.f = f
		self.line = line
		self.name = name
		
		self.__lists = []
		self.listProvider = self
		
		self.__config = {
			"n": 0,
			"forceDep": False,
			"include": None
		}
		self.__config.update(config)
		self.__useNewList = True
	
	
	def addToCurList(self, t):
		if self.__useNewList:
			self.__lists.append([])
			self.__useNewList = False
		
		self.__lists[-1].append(t)
	
	
	def switchToNewList(self):
		self.__useNewList = True
	
	
	def getConfig(self):
		return self.__config
	
	
	def getLists(self):
		return self.__lists
	
	
	def getListst(self):
			return self.__lists
	
	
	def finish(self, composer):
		if self.__config["include"] is not None:
			if len(self.__lists):
				raise Exception("Can't merge include with lists")
			
			self.listProvider = composer.getRootFromFile(self.__config["include"])
		else:
			self.listProvider = self
		
		for l in self.__lists:
			for token in l:
				token.finish(composer)

	
	def genBaseList(self, base, composer):
		if self.__config["n"] > 0:
			self.__outerContainer = dep.Container(self.name, base)
			composer.addUid(self.__outerContainer)
			composer.addUid(self.__outerContainer.getStart())
			composer.addUid(self.__outerContainer.getEnd())
			
			lastContainer = self.__outerContainer.getStart()
			for i in range(self.__config["n"]):
				newContainer = dep.Container("%i" % (i+1), self.__outerContainer)
				
				composer.addUid(newContainer)
				composer.addUid(newContainer.getEnd())
				composer.addUid(newContainer.getStart())
				
				composer.addDepLink(
					lastContainer.getFqn(), ## base
					newContainer.getFqn(),  ## dependency
					self
				)
				lastContainer = newContainer
				
				yield newContainer
			
			composer.addDepLink(
				lastContainer.getFqn(), ## base
				self.__outerContainer.getEnd().getFqn(),  ## dependency
				self
			)
		
		else:
			## If I look like a container and no one say I'm not a container:
			##  I'm the container
			if len(self.__lists) > 0 and self.__config["forceDep"] == False or self.__config["include"] is not None:
				self.__outerContainer = dep.Container(self.name, base)
				composer.addUid(self.__outerContainer.getEnd())
				composer.addUid(self.__outerContainer.getStart())
			
			else:
				self.__outerContainer = dep.Dep(self.name, base)
			
			
			composer.addUid(self.__outerContainer)
			
			yield self.__outerContainer
	
	
	
	def genDep(self, composer, base):
		for b in self.genBaseList(base, composer):
			for tokens in self.listProvider.getLists():
				lastBase = b.getStart()
				for token in tokens:
					lastDep = token.genDep(composer, b)
					
					composer.addDepLink(
						lastBase.getFqn(), ## base
						lastDep.getFqn(),  ## dependency
						self
					)
					
					lastBase = lastDep
				
				composer.addDepLink(
					lastBase.getFqn(),    ## base
					b.getEnd().getFqn(),  ## dependency
					self
				)
		
		return self.__outerContainer



class DepLink:
	def __init__(self, base = None, dependency = None, token = None):
		self.base = base
		self.dependency = dependency
		self.token = token



class DepComposer:
	def __init__(self, rootToken):
		self.__uids = {}
		self.__providers = {}
		self.__depLinks = []
		self.__settings = dep.Settings("settings")
		
		## First run
		self.__rootDep = rootToken.genDep(self, None)
		
		## Second run
		for link in self.__depLinks:
			base       = self.getUid(link.base, link.token)
			dependency = self.getUid(link.dependency, link.token)
			
			base.addDep(dependency)
	
	
	
	def addUid(self, dep):
		uid = dep.getFqn()
		
		if (uid in self.__uids) and (self.__uids[uid] != dep):
			raise Exception("Duplicate '%s'" % uid)
		
		self.__uids[uid] = dep
		
		settings = self.__settings.getSettingsFor(uid)
		if settings is not None:
			dep.applySettings(settings)
	
	
	
	def addProvider(self, dep, provides):
		for name in provides:
			if name not in  self.__providers:
				self.__providers[name] = []
			
			self.__providers[name].append(dep)
	
	
	
	def addUidProvider(self, dep, providers):
		self.addUid(dep)
		self.addProvider(dep, providers)
	
	
	
	def getUid(self, uid, token):
		if uid not in self.__uids:
			raise Exception("'%s' not found. Required by %s:%i" % (uid, token.getFile().getFileName(), token.getLine()))
		
		return self.__uids[uid]
	
	
	
	def addDepLink(self, base, dependency, token):
		self.__depLinks.append(DepLink(base, dependency, token))
	
	
	
	def getRoot(self):
		return self.__rootDep