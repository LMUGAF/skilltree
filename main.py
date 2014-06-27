#!/usr/bin/python



import dep
import file
import tokenx
import json
import io
import subprocess
import tempfile





class DotComposer:
	def __init__(self, root, dotBuffer, jsonBuffer = None):
		self.__indent = 0
		self.__edges = []
		self.__json = {}
		
		self.__dotBuffer = dotBuffer
		self.__writeDot("digraph G {", +1)
		self.__writeDot("compound = true;")
		self.__writeDot("bgcolor=transparent;")
		self.__writeDot("fontname=\"sans-serif\";")
		self.__writeDot("node [style= \"rounded,filled\", shape=box, height=0,fontname=\"sans-serif\"];")
		
		self.__vis(root)
		
		for edge in self.__edges:
			self.__writeDot(edge)
		
		self.__writeDot("}", -1)
		
		if jsonBuffer is not None:
			jsonBuffer.write("var nodeData = ");
			json.dump(self.__json, jsonBuffer, indent = "\t")
			jsonBuffer.write(";\n");
	
	
	
	def __writeDot(self, line, indent = 0):
		if indent == -1:
			self.__indent -= 1
		
		self.__dotBuffer.write(bytes("%s%s\n" % ("\t"*self.__indent, line), "UTF-8"))
		
		if indent == +1:
			self.__indent += 1
	
	
	def __collapse(self, node, l):
		if isinstance(node, dep.Container) and node.name is not None and node.getStatus() == "done":
			return [node]
		else:
			return l
	
	
	def __vis(self, node):
		status = node.getStatus()
		if  status == "blocked":
			color = "fillcolor = red"
		
		elif status == "done":
			color = "fillcolor = gray"
		
		elif status == "open":
			color = "fillcolor = green"
		
		self.collapsed = False
		if isinstance(node, dep.Container):
			if node.name is not None:
				if status == "done":
					self.collapsed = True
					self.__writeDot("%s [style= \"filled\", label=\"%s\", %s];" % (node.getFqn(), node.getDisplayName(), color))
				else:
					self.__writeDot("subgraph cluster_%s {" % node.getFqn(), +1)
					self.__writeDot("label = \"%s\";" % node.getDisplayName())
					self.__writeDot("%s;" % color)
		elif isinstance(node, dep.VirtualDep):
			self.__writeDot("%s [shape=point,height=0.15, width=0.15, %s];" % (node.getFqn(), color))
		else:
			self.__writeDot("%s [label=\"%s\", %s];" % (node.getFqn(), node.getDisplayName(), color))
			self.__json[node.getFqn()] = node.settings
		
		if not self.collapsed:
			for child in node.children:
				self.__vis(child)
		
		for d in node.getDeps():
			for exit in self.__collapse(node, node.getExits()):
				for entry in self.__collapse(d, d.getEntries()):
					options = []
					
					#if isinstance(entry, dep.Container):
						#options.append("ltail=cluster_%s" % entry.getFqn())
					
					#if isinstance(exit, dep.Container):
						#options.append("lhead=cluster_%s" % exit.getFqn())
					
					self.__edges.append("%s -> %s [%s];" % (exit.getFqn(), entry.getFqn(), ", ".join(options)))
		
		if isinstance(node, dep.Container):
			if node.name is not None:
				if status != "done":
					self.__writeDot("}", -1)




tc = file.tokenComposer("deps/main.dep")
dc = tokenx.DepComposer(tc.getRoot())

svgBuffer = open("main.svg", "w")
p = subprocess.Popen(["dot", "-Tsvg"], stdin=subprocess.PIPE, stdout = svgBuffer)

jsonBuffer = open("data.json.js", "w")
dotBuffer  = p.stdin
DotComposer(dc.getRoot(), dotBuffer, jsonBuffer)

