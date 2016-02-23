#!/usr/bin/env python
from PIL import Image
import argparse
import math

class MonoBitmap:
	#static BMP header for monochrome 512x512 bitmap
	_HEADER = b'\x42\x4D\x3E\x80\x00\x00\x00\x00\x00\x00\x3E\x00\x00\x00\x28\x00\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\x00' 
	def __init__(self, width, height):
		self.width = width
		self.height = height
		#allocate image buffer
		self.buffer = bytearray(int(math.ceil(width * height / 8)))

	def fromPixels(self, pixelData):
		for y in xrange(self.height):
			for x in xrange(self.width):
				r,g,b = pixelData[x,y]
				if r > 127 or g > 127 or b > 127:
					self.setPixel(x,y)

	def setPixel(self, x, y):
		index = (y * self.width + x)
		byteIndex = index // 8
		byteOffset = index % 8
		self.buffer[byteIndex] |= (128 >> byteOffset)

	def save(self, outfile):
		#Write header
		outfile.write(MonoBitmap._HEADER)
		#Write picture data
		outfile.write(self.buffer)

parser = argparse.ArgumentParser(description='Converts image to NEJE-compatible BMP format')
parser.add_argument('infile', type=argparse.FileType('rb'))
parser.add_argument('outfile', type=argparse.FileType('wb'))

args = parser.parse_args()

im = Image.open(args.infile)
im = im.resize((512,512))#, Image.LANCZOS)

bmp = MonoBitmap(*im.size)
bmp.fromPixels(im.load())
bmp.save(args.outfile)