# imports - compatibility imports
from __future__ import absolute_import

# imports - standard imports
import threading

# imports - third-party imports
import numpy as np
import cv2
from PIL import Image

# imports - module imports
from spockpy       import Config
from spockpy.io    import Capture
from spockpy.event import Event
from spockpy._util import _resize_image, _round_int, _mount_roi
from spockpy.event import keycode

import spockpy

def _get_roi(size, ratio = 0.42, position = 'tl'):
	width, height = _round_int(size[0] * ratio), _round_int(size[1] * ratio)

	if   position == 'tl':
		x, y = 0, 0
	elif position == 'tr':
		x, y = size[0] - width, 0
	elif position == 'bl':
		x, y = 0, size[1] - height
	elif position == 'br':
		x, y = size[0] - width, size[1] - height

	return (x, y, width, height)

def _crop_array(array, roi):
	x, y, w, h = roi
	crop       = array[ y : y + h , x : x + w ]

	return crop

class HoverPad(object):
	'''
	HoverPad object

	Parameters

	:param size: the size of the HoverPad instance containing the width and height in pixels, defaults to 320x240
	:type size: :obj:`tuple`

	:param deviceID: the device ID of your capture device, defaults to 0.
	:type deviceID: :obj:`int`

	:param position: the relative position of the :obj:`HoverPad` with respect to the current frame. This could be top-left (`tl`), top-right (`tr`), bottom-left (`bl`) and bottom-right (`br`)
	:type position: :obj:`str`, defaults to `tl`.

	:param verbose: if True, displays frames containing the threshold and contour information.
	:type verbose: :obj:`bool`

	Example

	>>> import spockpy
	>>> pad = spockpy.HoverPad(size = (480, 320))
	'''
	TITLE = 'HoverPad | spockpy'

	def __init__(self, size = Config.HOVERPAD_SIZE, deviceID = 0, position = 'tl', verbose = False):
		self.size     = size
		self.deviceID = deviceID
		self.capture  = Capture(deviceID = self.deviceID)
		self.position = position
		self.event    = Event(Event.NONE)
		self.image    = None

		self.verbose  = verbose

		self.roi      = _get_roi(size = self.size, position = position)

		self.thread   = threading.Thread(target = self._showloop)

	def show(self):
		'''
		Displays the HoverPad object instance onto the screen. To close the HoverPad, simply press the ESC key
		
		Example

		>>> import spockpy
		>>> pad = spockpy.HoverPad()
		>>> pad.show()
		'''
		self.thread.start()

	def _showloop(self):
		while cv2.waitKey(10) not in [keycode.ESCAPE, keycode.Q, keycode.q]:
			image = self.capture.read()
			image = image.transpose(Image.FLIP_LEFT_RIGHT)

			image = _resize_image(image, self.size)
			
			array = np.asarray(image)
			array = _mount_roi(array, self.roi, color = (74, 20, 140), thickness = 2)

			crop  = _crop_array(array, self.roi)

			# process image for any gestures
			if self.verbose:
				segments, event = spockpy.detect(crop, verbose = self.verbose)
			else:
				event           = spockpy.detect(crop, verbose = self.verbose)

			
			self.image = Image.fromarray(segments)
			self.event = event

			cv2.imshow(HoverPad.TITLE, array)

		cv2.destroyWindow(HoverPad.TITLE)

	def get_event(self):
		'''
		Returns a :py:class:`spockpy.Event` captured within the current frame.

		Example

		>>> import spockpy
		>>> pad   = spockpy.HoverPad()
		>>> event = pad.get_event()
		>>> event.type == Event.ROCK
		True
		'''
		return self.event

	def get_image(self):
		'''
		Returns a :obj:`PIL.Image` captured within the current frame.

		Example
		
		>>> import spockpy
		>>> pad   = spockpy.HoverPad()
		>>> image = pad.get_image()
		>>> image.show()
		'''
		return self.image
