#!/usr/bin/env python
# -*- coding: utf-8 -*-

###########################################################################
#    Copyright (C) 2008 by Ing. Tomáš Košan                                      
#    <t.kosan@k25.cz>                                                             
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################


from PyQt5.QtGui import * 
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from ut2XXX import utils
import logging

class DSO_View(QGraphicsView):

	def __init__(self, scene=None, parent=None):
		QGraphicsView.__init__(self, parent=parent)
		self.anim = QTimeLine(350, self)
		self.anim.setUpdateInterval(20)
		self.anim.valueChanged.connect(self.scalingTime)
		self.anim.finished.connect(self.animFinished)
		self._numScheduledScalings = 0

	def scalingTime(self, x):
		factor = 1.0 + self._numScheduledScalings/300.0
		self.scale(factor, factor)

	def wheelEvent(self, event):
		print(event)
		numDegrees = event.angleDelta().y()
		numSteps = numDegrees/15
		self._numScheduledScalings += numSteps
		if (self._numScheduledScalings * numSteps < 0):
			self._numScheduledScalings = numSteps
		self.anim.start()

	def animFinished(self):
		pass


# main scene class with prerendered grid

class DSO_Scene(QGraphicsScene):
	
	def __init__(self):
		QGraphicsScene.__init__(self, 0,0,540,440)

		# we want black background
		bg = QBrush()
		bg.setColor(QColor(Qt.black))
		bg.setStyle(Qt.SolidPattern)
		self.setBackgroundBrush(bg)
		
		# create paint grid
		self.grid = DSO_grid(self)
		self.addItem(self.grid)
		
		# create 3 cursors
		self.ch1_cursor = DSO_cursor(self, "1", Qt.cyan, "Y")
		self.addItem(self.ch1_cursor)
		self.ch2_cursor = DSO_cursor(self, "2", Qt.yellow, "Y")
		self.addItem(self.ch2_cursor)
		self.chX_cursor = DSO_cursor(self, "T", Qt.red, "X")
		self.addItem(self.chX_cursor)
		
		# create text boxes to show V/div s/div 
		self.ch1_range = DSO_range(self, "CH1", Qt.cyan)
		self.ch1_range.setPos(20,430)
		self.addItem(self.ch1_range)

		self.ch2_range = DSO_range(self, "CH2", Qt.yellow)
		self.ch2_range.setPos(195,430)
		self.addItem(self.ch2_range)

		self.time_range = DSO_range(self, "TIME", Qt.white)
		self.time_range.setPos(370,430)
		self.addItem(self.time_range)

		self.time_offset = DSO_range(self, "Pos:", Qt.black, Qt.white)
		self.time_offset.setPos(0,0)
		self.addItem(self.time_offset)

		self.wave1 = DSO_wave(self, Qt.cyan)
		self.wave1.hide()
		self.addItem(self.wave1)

		self.wave2 = DSO_wave(self, Qt.yellow)
		self.wave2.hide()
		self.addItem(self.wave2)
		
		# finally update screen
		self.update()
		
		self.pixmap = QGraphicsPixmapItem(None)
		self.addItem(self.pixmap)
		
	def updateScreen(self, ch1_data, ch2_data):
		self.grid.show()
		if ch1_data["active"]:
			self.wave1.repaint(ch1_data["samples"])
			self.ch1_cursor.setP(2*(106-ch1_data["y_offset"]))
			self.ch1_cursor.show()
			bw_lim = ""
			if ch1_data["Bw_limit"]:
				bw_lim = ", Bw"
			self.ch1_range.setText("CH1: "+str(ch1_data["V_div"])+"V/div, "+ch1_data["couple"]+bw_lim)
		else:
			self.wave1.hide()
			self.ch1_cursor.hide()
			self.ch1_range.setText("CH1: OFF")
				
		if ch2_data["active"]:	
			self.wave2.repaint(ch2_data["samples"])	
			self.ch2_cursor.setP(2*(106-ch2_data["y_offset"]))
			self.ch2_cursor.show()
			bw_lim = ""
			if ch2_data["Bw_limit"]:
				bw_lim = ", Bw"
			self.ch2_range.setText("CH2: "+str(ch2_data["V_div"])+"V/div, "+ch1_data["couple"]+bw_lim)
		else:
			self.wave2.hide()
			self.ch2_cursor.hide()
			self.ch2_range.setText("CH2: OFF")
		
		#print "Debug:",ch2_data["x_offset"]
		if ch2_data["x_offset"] in range(0,250):		
			self.chX_cursor.setP(2*(ch2_data["x_offset"])+14)
			self.time_offset.setPos(2*(ch2_data["x_offset"]),-15)
			self.time_offset.setText("Pos: "+utils.float2engstr((125-ch2_data["x_offset"])*ch1_data["s_div"]/25)+"s")
#		elif ch2_data["x_offset"] in range(0,3):
#			self.chX_cursor.setP(20)
#			self.time_offset.setPos(0,-15)
		elif ch2_data["x_offset"] > 250:
			self.chX_cursor.setP(270)
			self.time_offset.setPos(270,-15)
			
		self.time_range.setText("TIME: "+utils.float2engstr(ch1_data["s_div"])+"s/div")
		# hide screenshot	
		self.pixmap.hide()
		self.update()	
			
	def showPixmap(self, pixmap):
		
		self.wave1.hide()
		self.ch1_cursor.hide()
		self.wave2.hide()
		self.ch2_cursor.hide()
		self.grid.hide()
		
		print("Inf: Showing pixmap")
		#self.pixmap = QGraphicsPixmapItem(pixmap, None, self)
		self.pixmap.setPixmap(pixmap)
		self.pixmap.setPos(-50,-20)
		self.pixmap.show()
		self.update()
		
		
# wave is 
class DSO_wave(QGraphicsItemGroup):
		
	def __init__(self, parent, color):
		QGraphicsItemGroup.__init__(self, None)
		
		self.color = QColor(color)
		self.pen = QPen()
		self.pen.setColor(self.color)
		
		self.lines = []
		
		self.offset_x = 10
		
		for i in range(self.offset_x,250+self.offset_x):
			line = QGraphicsLineItem(self)
			line.setLine(i*2,20+200,(i*2)+2,20+200)
			line.setPen(self.pen)
			self.lines.append(line)
			
			
	# hide all		
	def hide(self):
		for line in self.lines:
			line.hide()
				
	def repaint(self, samples):
		logging.debug("Repaint image:")
		index = 0
		x = 20
		y = 20
		for sample in samples:
			line = self.lines[index]
			index += 1 
			
			# get rid of out of display values
			#if sample > 254:
			#	continue
			#print(sample)
			
			# first point
			if x == 20:
				line.setLine(x,(2*(255 - sample) - 34),x,(2*(255 - sample) - 34))
			else:
				line.setLine(x-2,y,x,(2*(255 - sample) - 34))				
			x = x + 2
			y = (2*(255 - sample) - 34)
			#line.setPen(self.pen)
			line.show()


# 
class DSO_cursor(QGraphicsPolygonItem):
		
	def __init__(self, parent, name="", color=Qt.white, typ="X"):
		QGraphicsPolygonItem.__init__(self, None)
		
		polygon = QPolygonF()
		
		if typ == "Y":
			polygon.append(QPointF(0,0))
			polygon.append(QPointF(0,16))
			polygon.append(QPointF(12,16))
			polygon.append(QPointF(20,8))
			polygon.append(QPointF(12,0))
		
		if typ == "X":
			polygon.append(QPointF(0,0))
			polygon.append(QPointF(6,6))
			polygon.append(QPointF(12,0))
			
		
		self.setPolygon(polygon)
			
		# we want black background
		bg = QBrush()
		col = QColor(color)
		col.setAlpha(200)
		bg.setColor(col)
		bg.setStyle(Qt.SolidPattern)
		self.setBrush(bg)
		
		if typ == "Y":
			text = QGraphicsTextItem(self)
			text.setPlainText(name)
			text.setY(text.y()-4)
		
		self.typ = typ
		self.show()

	def setP(self, pos):
		if self.typ == "Y":
			self.setPos(0,pos)
		if self.typ == "X":
			self.setPos(pos,10)
	
# paint basic grid	
	 
class DSO_grid(QGraphicsItemGroup):
	
	def __init__(self, parent):
		QGraphicsItemGroup.__init__(self, None)
		self.showGrid()
		#self.hide()

	def showGrid(self):
		self.color = QColor()
		pen = QPen()
		self.color.setNamedColor("white")
		pen.setColor(self.color)
		
		# we will generate DSO screen grid
		for x in range(20,521,10):
			for y in range(20,421,50):
				
				self.point = QGraphicsLineItem(self)
				
				if y == 20:
					self.point.setLine(x,y,x,y+3)
				elif y == 220:
					self.point.setLine(x,y-2,x,y+2)
				elif y == 420:
					self.point.setLine(x,y,x,y-3)
				else:
					self.point.setLine(x,y,x,y)
				
				self.point.setPen(pen)
				self.point.show()

		for x in range(20,521,50):
			for y in range(20,421,10):
				
				self.point = QGraphicsLineItem(self)
				
				if x == 20:
					self.point.setLine(x,y,x+3,y)
				elif x == 270:
					self.point.setLine(x-2,y,x+2,y)
				elif x == 520:
					self.point.setLine(x,y,x-3,y)
				else:
					self.point.setLine(x,y,x,y)
				
				self.point.setPen(pen)
				self.point.show()

class DSO_range(QGraphicsPolygonItem):
		
	def __init__(self, parent, text="", color=Qt.white, text_col=Qt.black):
		QGraphicsPolygonItem.__init__(self, None)
		
		polygon = QPolygonF()
		
		self.width = 175
		self.height = 24
		
		polygon.append(QPointF(0,0))
		polygon.append(QPointF(0,self.height))
		polygon.append(QPointF(self.width,self.height))
		polygon.append(QPointF(self.width,0))
			
		
		self.setPolygon(polygon)
			
		# we want black background
		bg = QBrush()
		col = QColor(color)
		col.setAlpha(200)
		bg.setColor(col)
		bg.setStyle(Qt.SolidPattern)
		self.setBrush(bg)
		
		self.text = QGraphicsTextItem(self)
		self.text.setDefaultTextColor(QColor(text_col))
		self.text.setPlainText(text)
		
		self.show()
			
	def setText(self, text):
		self.text.setPlainText(text)

def main(args):
	app=QApplication(args)
	#app.connect(app, QtCore.SIGNAL("lastWindowClosed()"), app.quit)
	app.setStyle("plastique")
	dso = DSO_Scene()
	mainWindow = QMainWindow()
	mainWindow.setMinimumSize(QSize(640, 480))
	#view = DSO_View(dso, parent=mainWindow)
	view = QGraphicsView(dso)
	view.setMinimumSize(QSize(640, 480))
	mainWindow.show()
	sys.exit(app.exec_())

if __name__ == "__main__":
	import sys
	main(sys.argv)