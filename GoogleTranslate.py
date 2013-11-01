# -*- coding: utf-8 -*-

import webbrowser
import urllib

_FORM_URL = "http://translate.google.com/{0}/{1}/{2}"

class GoogleTranslate:
	def __init__(self, from_lang, to_lang):
		self.from_lang = from_lang
		self.to_lang = to_lang
		self.from_text = ""
		self.to_text = ""
		self.on_done = None

	def get_from_lang(self):
		return self.from_lang

	def set_from_lang(self, value):
		self.from_lang = value
		return self.from_lang

	def get_to_lang(self):
		return self.to_lang

	def set_to_lang(self, value):
		self.to_lang = value
		return self.to_lang

	def get_from_text(self):
		return self.from_text

	def get_to_text(self):
		return self.to_text

	def trans(self, text, newTab):
		text = text.strip()
		if text == "":
			self.from_text = ""
			self.to_text = ""
			return

		self.from_text = text
		self.to_text = ""
		url = str.format(_FORM_URL, self.from_lang, self.to_lang, urllib.quote(text))

		if newTab:
			webbrowser.open_new_tab(url)
		else:
			webbrowser.open(url)
