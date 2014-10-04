#!/usr/bin/env python

from gi.repository import GObject, Gtk, Gdk

import Defaults.widget, Widgets.SubWidgetManager, output

from simplemath import *

class Widget(Gtk.Window):
	def __init__(self, name, configurationFile):
		Gtk.Window.__init__(self, skip_pager_hint=True, skip_taskbar_hint=True)
		
		#Set the window properties to look like a gadget. These cannot be changed through the configuration file
		self.set_name(name)
		self.name=name
		self.set_wmclass(Defaults.widget.wmClass, Defaults.widget.wmClass)
		self.set_type_hint(Gdk.WindowTypeHint.DOCK)
		self.set_keep_below(True)
		self.stick()

		self.pantoflaWidgetManager = Widgets.SubWidgetManager.SubWidgetManager()

		self.styleProvider=Gtk.CssProvider()
		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.styleProvider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

		self.currentCss=[]

		self.grid = Gtk.Grid()
		self.grid.set_row_spacing(3)
		self.grid.set_column_spacing(3)
		self.YHeight=0

		self.add(self.grid)

		self.applyConfigurationFile(configurationFile)

		#Show all the parts
		self.show_all()

	def commandForReceiver(self, receiver, command, lineCount, configurationFile):
		"""Sends the command (property) to the appropriate widget (receiver)"""
		if receiver not in self.pantoflaWidgetManager.receivers:
			for widget in self.pantoflaWidgetManager.widgets:
				if receiver.startswith(widget.receiver):
					self.pantoflaWidgetManager.receivers[receiver]=widget.Widget(receiver, self.name)
					self.pantoflaWidgetManager.receivers[receiver].runCommand(command, lineCount, configurationFile)
					break
		else:
			self.pantoflaWidgetManager.receivers[receiver].runCommand(command, lineCount, configurationFile)

	def applyConfigurationFile(self, configurationFile):
		try:
			f = open(configurationFile, 'r')
		except:
			output.stderr("Could not open configuration file '"+configurationFile+"'. Default settings will be loaded")

		receiver = None #The receiver of the properties
		lastReceiver = None

		lineCount=0

		#Some values that have to be set
		sizeSet=False
		positionSet=False
		backgroundColorSet=False
		updateIntervalSet=False

		for line in f:
			lineCount+=1

			if(line.startswith("#")):
				continue #Line starts with '#', so it is a comment

			line=line.rstrip()
			line=line.lstrip()

			if(line==""):
				continue

			if(line.startswith("[")):
				#New receiver
				if not line.endswith("]"):
					output.stderr(configurationFile+", line "+str(lineCount)+": Syntax error: Expected ']' at the end of the line.\nSkipping...")
					continue
				receiver=line[1:-1]


				#Add the last receiver to the window, because now there is a new one. The old one has finished its properties
				if(lastReceiver!="Widget" and lastReceiver!=None):
					print "ADDING TO GRID", self.pantoflaWidgetManager.receivers[lastReceiver].widget(), self.YHeight
					self.grid.attach(self.pantoflaWidgetManager.receivers[lastReceiver].widget(), 0, self.YHeight, 1, 1)
					self.YHeight+=1
					#self.add(self.pantoflaWidgetManager.receivers[lastReceiver].widget())

				#Add the new receiver to the list
				if(receiver!="Widget"):
					if receiver not in self.pantoflaWidgetManager.receivers:
						for widget in self.pantoflaWidgetManager.widgets:
							if receiver.startswith(widget.receiver):
								self.pantoflaWidgetManager.receivers[receiver]=widget.Widget(receiver, self.name)
								lastReceiver=receiver
								break

				continue

			#Remove the spaces between the property and the value
			if('=' in line):
				parts=line.split("=")
				if(len(parts)>=2):
					parts[0]=parts[0].rstrip()
					parts[0]=parts[0].lstrip()
					parts[1]=parts[1].lstrip()
					line=parts[0]+'='+parts[1]
					if(len(parts)>2):
						for i in range(2, len(parts)):
							line+='='+parts[i]

			if(receiver==None):
				output.stderr(configurationFile+", line "+str(lineCount)+": Unexpected command: I do not know the receiver of '"+line+"'.\nSkipping...")
				continue

			if(receiver=="Widget"):
				#The special receiver Widget
				if(line.startswith("position=")):
					parts=line.split("=")
					if(len(parts)!=2):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'position': Format: position = x,y.\nSkipping...")
						continue
					coords=parts[1].split(",")
					if(len(coords)!=2):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'position': Format: position = x,y.\nSkipping...")
						continue

					if((not representsInt(coords[0]) and coords[0]!="middle") or (not representsInt(coords[1]) and coords[1]!="middle")):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'position': Format: position = x,y.\nSkipping...")
						continue
					if(coords[0]=="middle"):
						coords[0]=Defaults.widget.defaultScreen.get_width()/2-self.get_size()[0]/2
					if(coords[1]=="middle"):
						coords[1]=Defaults.widget.defaultScreen.get_height()/2-self.get_size()[1]/2

					self.move(int(coords[0]), int(coords[1]))
					positionSet=True

				elif(line.startswith("size=")):
					parts=line.split("=")
					if(len(parts)!=2):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'size': Format: size = w,h.\nSkipping...")
						continue
					size=parts[1].split(",")
					if(len(size)!=2):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'size': Format: size = w,h.\nSkipping...")
						continue

					if((not representsInt(size[0]) and size[0]!="half") or (not representsInt(size[1]) and size[1]!="half")):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'size': Format: size = w,h.\nSkipping...")
						continue

					if(size[0]=="half"):
						size[0]=Defaults.widget.defaultScreen.get_width()/2
					if(size[1]=="half"):
						size[1]=Defaults.widget.defaultScreen.get_height()/2

					self.set_default_size(int(size[0]), int(size[1]))
					sizeSet=True

				elif(line.startswith("bgColor=")):
					parts=line.split("=")
					if(len(parts)!=2):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'bgColor': Format: bgColor = R,G,B,A.\nSkipping...")
						continue
					values=parts[1].split(",")
					if(len(values)!=4):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'bgColor': Format: bgColor = R,G,B,A.\nSkipping...")
						continue

					if(not representsInt(values[0]) or not representsInt(values[1]) or not representsInt(values[2]) or not representsFloat(values[3])):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'bgColor': Format: bgColor = R,G,B,A.\nSkipping...")
						continue

					self.set_visual(self.get_screen().get_rgba_visual())
					self.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(int(values[0]), int(values[1]), int(values[2]), float(values[3])))

					backgroundColorSet=True
				elif(line.startswith("border=")):
					parts=line.split("=")
					if(len(parts)!=2):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'border': Format: border = width, #RRGGBB.\nSkipping...")
						continue

					values=parts[1].split(",")

					if(len(values)!=2 or not representsInt(values[0])):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'border': Format: border = width, #RRGGBB.\nSkipping...")
						continue

					self.currentCss.append("border: "+values[0]+"px solid "+values[1]+";")
					self.updateCss()
				elif(line.startswith("borderRadius=")):
					parts=line.split("=")
					if(len(parts)!=2):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'borderRadius': Format: borderRadius = pixels/percentage.\nSkipping...")
						continue

					isPercentage=False

					if(parts[1].endswith("%")):
						if(representsInt(parts[1][:-1])):
							isPercentage=True
						else:
							output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'borderRadius': Format: borderRadius = pixels/percentage.\nSkipping...")
							continue
					elif not representsInt(parts[1]):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'borderRadius': Format: borderRadius = pixels/percentage.\nSkipping...")
						continue

					if not isPercentage:
						self.currentCss.append("border-radius: "+parts[1]+"px")
					else:
						self.currentCss.append("border-radius: "+parts[1])
					self.updateCss()
				elif(line.startswith("updateInterval=")):
					parts=line.split("=")
					if(len(parts)!=2):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'updateInterval': Format: updateInterval = ms.\nSkipping...")
						continue
					if(not representsInt(parts[1])):
						output.stderr(configurationFile+", line "+str(lineCount)+": Badly formatted command 'updateInterval': Format: updateInterval = ms.\nSkipping...")
						continue
					if(int(parts[1])<800):
						output.stderr(configurationFile+", line "+str(lineCount)+": Too small interval set for command 'updateInterval': Interval cannot be set less than 800. Setting to 800.")
						parts[1]=800
					self.pantoflaWidgetManager.setUpdateInterval(int(parts[1]))

					updateIntervalSet=True
				else:
					output.stderr(configurationFile+", line "+str(lineCount)+": Unknown command '"+line+"'")
			else:
				#The receiver is not 'Widget'
				self.commandForReceiver(receiver, line, lineCount, configurationFile)

		f.close()

		#Add the last receiver to the window. This is the last receiver as the file has ended
		if(lastReceiver!="Widget" and lastReceiver!=None):
			#self.add(self.pantoflaWidgetManager.receivers[lastReceiver].widget())
			print "ADDING TO GRID", self.pantoflaWidgetManager.receivers[lastReceiver].widget(), self.YHeight
			self.grid.attach(self.pantoflaWidgetManager.receivers[lastReceiver].widget(), 0, self.YHeight, 1, 1)
			self.YHeight+=1

		#Set the default values to the ones that have to be set

		if not sizeSet:
			self.set_default_size(Defaults.widget.defaultWidth, Defaults.widget.defaultHeight)

		if not positionSet:
			self.move(Defaults.widget.defaultScreen.get_width()/2-self.get_size()[0]/2, Defaults.widget.defaultScreen.get_height()/2-self.get_size()[1]/2)

		if not backgroundColorSet:
			self.set_visual(self.get_screen().get_rgba_visual())
			self.override_background_color(Gtk.StateFlags.NORMAL, Defaults.widget.defaultBgColor)

		if not updateIntervalSet:
			self.pantoflaWidgetManager.setUpdateInterval(1000)

		#TO REMOVE START
		# self.YHeight=0
		# for child in self.grid:
		# 	self.grid.remove(child)
		# 	self.pantoflaWidgetManager.receivers={}
		# 	print "PERNAW1"
		# 	self.grid.attach(Gtk.Label("Hello"+str(self.YHeight)), 0, self.YHeight, 1, 1)
		# 	self.YHeight+=1
		#TO REMOVE END

		self.pantoflaWidgetManager.startUpdating()

	def updateCss(self):
		self.styleProvider.load_from_data("""
			#"""+self.name+""" {
				"""+' '.join(self.currentCss)+"""
			}
		""")