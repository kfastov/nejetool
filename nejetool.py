#!/usr/bin/env python
import argparse
import serial
import math
import time
import sys

class NEJECarver:
	#Known commands supported by DK5-Pro
	OP_START_CARVE = 0xF1
	OP_PAUSE_CARVE = 0xF2
	OP_MOVE_ORIGIN = 0xF3
	OP_CARVING_PREVIEW = 0xF4
	OP_MOVE_BEAM = 0xF5 #
	OP_INIT = 0xF6
	OP_REVERSE_AXIS = 0xF7 #
	OP_RESTART = 0xF9
	OP_SET_MOTOR_STEP_PAUSE = 0xFA
	OP_PREVIEW_CENTER = 0xFB
	OP_CARVE_RATE_CONTROL = 0xFC #
	OP_ERASE_PICTURE = 0xFE

	#constants
	DIRECTION_UP = 0x01
	DIRECTION_DOWN = 0x02
	DIRECTION_LEFT = 0x03
	DIRECTION_RIGHT = 0x04

	AXIS_X = 0x01
	AXIS_Y = 0x02

	CARVE_BACK = 0x55
	CARVE_RECARVE = 0x77
	CARVE_FORWARD = 0xAA

	def __init__(self):
		self._port = serial.Serial('/dev/ttyUSB0')
		self._port.baudrate = 57600
		self._port.setRTS(True)
		self._port.setDTR(True)

	def command(self, command, data = b''):
		#support hex constants as data
		if type(data) is int:
			data = chr(data)
		print('Sending command {}, data {}'.format(hex(command), data.encode('hex')))
		self._port.write(chr(command) + data)

	#just a proxy. maybe unneeded.
	def get_response(self, len):
		return self._port.read(len)

	def connect(self):
		print('Connecting...')
		#send init command
		self.command(self.OP_INIT)
		#read response and print it
		if self.get_response(2) == b'\x65\x6f':
			print('Connected!')
		#else:
		#	raise Exception("Connection error: Response don't match!")

	def move_beam(self, direction):
		self.command(OP_MOVE_BEAM, direction)

	def set_burning_time(self, ms):
		self._port.write(chr(min(ms,240)))

	def upload_picture(self, picture):
		#Here the magic begins
		#First of all, we send 0xFE 8 times
		#It's called 'Erasing old image' in official software
		print('Erasing old image?')
		for i in range(8):
			self.command(carver.OP_ERASE_PICTURE)
			self._port.flush()
		time.sleep(3)

		#Then send image in BMP monochrome format
		print('Uploading image from file...')
		bytesSend = self._port.write(picture.read())
		print('Sent {} bytes.'.format(bytesSend))


	def reverse_axis(self, axis):
		self.command(OP_REVERSE_AXIS, axis)

	def set_step_pause(self, ms):
		self.command(OP_SET_MOTOR_STEP_PAUSE, chr(min(255,ms)))

	def control_carve(self, op):
		self.command(OP_CARVE_PLAYBACK_CONTROL, op)

#argparser types checkers

def type_auto_int(x):
    return int(x, 0)

def type_dict(values, name='value'):
	def check(key):
		if key not in values:
			raise argparse.ArgumentTypeError(
				"{} is not a valid {}".format(key, name))
		return values[key]
	return check

#subcommand entry points

def command(carver, args):
	carver.command(args.code)

def call_method(carver, args):
	getattr(carver, args.method)(args.arg)

#build parser and parse args
def parse_args():
	parser = argparse.ArgumentParser(description='NEJE Laser Engraver control utility')
	parser.set_defaults(func=command)

	subparsers = parser.add_subparsers(
		dest='task',
		title='Operations',
		help='Run %(prog)s {command} -h for additional help')

	#direct commands

	subparsers.add_parser('start', help='Start engraving operation')\
		.set_defaults(code = NEJECarver.OP_START_CARVE)
	subparsers.add_parser('pause', help='Pause engraving')\
		.set_defaults(code = NEJECarver.OP_PAUSE_CARVE)
	subparsers.add_parser('restart', help='Restart the device')\
		.set_defaults(code = NEJECarver.OP_RESTART)
	subparsers.add_parser('preview', help='Show picture bounds')\
		.set_defaults(code = NEJECarver.OP_CARVING_PREVIEW)
	subparsers.add_parser('origin', help='Move beam to picture origin')\
		.set_defaults(code = NEJECarver.OP_MOVE_ORIGIN)
	subparsers.add_parser('middle', help='Move beam to the middle of the picture')\
		.set_defaults(code = NEJECarver.OP_PREVIEW_CENTER)
	parser_rawcmd = subparsers.add_parser('raw', help='Send raw command')\
		.add_argument('code', type=type_auto_int, help='command code')
	#TODO: data in hex encoding	
	#methods

	parser_move = subparsers.add_parser('move', help='Move picture in specific direction')
	parser_move.set_defaults(func=call_method)
	parser_move.add_argument('arg', metavar='direction', type=type_dict(dict(
			up = NEJECarver.DIRECTION_UP,
			down = NEJECarver.DIRECTION_DOWN,
			left = NEJECarver.DIRECTION_LEFT,
			right = NEJECarver.DIRECTION_RIGHT), 'direction'))

	parser_reverse = subparsers.add_parser('reverse', help='Mirror image along specified axis')
	parser_reverse.set_defaults(func = call_method)
	parser_reverse.add_argument('arg', metavar='axis', type=type_dict(dict(
			x = NEJECarver.AXIS_X,
			y = NEJECarver.AXIS_Y), 'axis'))

	parser_set_burn_time = subparsers.add_parser('set_burn_time', help='Set burning time')
	parser_set_burn_time.set_defaults(func=call_method)
	parser_set_burn_time.add_argument('arg', metavar='interval', type=int, help='interval in milliseconds')

	parser_set_pause = subparsers.add_parser('set_pause', help='Set motor step pause')
	parser_set_pause.set_defaults(func=call_method)
	parser_set_pause.add_argument('arg', metavar='interval', type=int, help='interval in milliseconds')

	parser_seek = subparsers.add_parser('seek', help='Seek through the carving sequence')
	parser_seek.set_defaults(func=call_method)
	parser_seek.add_argument('arg', metavar='offset', help='Seek 15 rows backward (back), forward or recarve',
		type=type_dict(dict(
			back = NEJECarver.CARVE_BACK,
			forward = NEJECarver.CARVE_FORWARD,
			recarve = NEJECarver.CARVE_RECARVE)))

	parser_upload_pic = subparsers.add_parser('upload_pic', help='Upload image to engraver')
	parser_upload_pic.set_defaults(func=call_method)
	parser_upload_pic.add_argument('arg', metavar='image', help='Raw 512x512 image file', type=argparse.FileType('rb'))

	return parser.parse_args()

def main():
	args = parse_args()
	print args
	#sys.exit(0)
	carver = NEJECarver()
	carver.connect()
	args.func(carver, args)
	#while True:
	#	data = carver._port.read()
	#	print(data.encode('hex'))

if __name__ == '__main__':
	main()


"""
Optional parameters:
 -b baudrate
 -p port

Actions:
	burning_time <int>
	start
	pause
	preview
	move <dir>
	reverse <axis>
	restart
	set_pause <int>
	center 
	seek <seek_dir>
	upload_pic <filename>
"""

#TODO: add arguments group?

#TODO: constants / mutual exclusions | custom type