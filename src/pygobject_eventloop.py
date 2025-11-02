# Copyright (c) 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 LEW21
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1.  Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.

# 2.  Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import asyncio
import selectors
from gi.repository import GLib

class GLibSelector(selectors.BaseSelector):
	def __init__(self):
		self.sources = {}

	def register(self, fileobj, events, data=None):
		fd = fileobj.fileno()
		source = GLib.IO.add_watch(fd, self.glib_events(events), self.glib_callback, data)
		self.sources[fd] = source
		return selectors.SelectorKey(fileobj, fd, events, data)

	def unregister(self, fileobj):
		fd = fileobj.fileno()
		source = self.sources.pop(fd)
		GLib.source_remove(source)
		return selectors.SelectorKey(fileobj, fd, 0, None)

	def select(self, timeout=None):
		raise NotImplementedError

	def glib_events(self, events):
		glib_events = GLib.IO_ERR | GLib.IO_HUP
		if events & selectors.EVENT_READ:
			glib_events |= GLib.IO_IN
		if events & selectors.EVENT_WRITE:
			glib_events |= GLib.IO_OUT
		return glib_events

	def glib_callback(self, fd, events, data):
		self.loop._selector_callback(fd, events, data)
		return True

	def close(self):
		for fd in list(self.sources):
			self.unregister(fd)

class GLibEventLoop(asyncio.SelectorEventLoop):
	def __init__(self):
		selector = GLibSelector()
		super().__init__(selector)
		selector.loop = self

	def _selector_callback(self, fd, events, data):
		if events & (GLib.IO_ERR | GLib.IO_HUP):
			self._process_events([(self._selector.get_key(fd), selectors.EVENT_READ | selectors.EVENT_WRITE)])
		elif events & GLib.IO_IN:
			self._process_events([(self._selector.get_key(fd), selectors.EVENT_READ)])
		elif events & GLib.IO_OUT:
			self._process_events([(self._selector.get_key(fd), selectors.EVENT_WRITE)])

class GLibEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
	def new_event_loop(self):
		return GLibEventLoop()
