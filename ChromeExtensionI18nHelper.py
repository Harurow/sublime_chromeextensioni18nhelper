# -*- coding: utf-8 -*-
import sublime
import sublime_plugin
import os
import re
import json
from datetime import *


_SETTINGS_NAME = "ChromeExtensionI18nHelper.sublime-settings"
_MANIFEST_JSON_FILE = "manifest.json"
_MESSAGES_JSON_FILE = "messages.json"
_LOCALES_DIR = "_locales"
_LOCALES = ["ar", "am", "bg", "bn", "ca", "cs", "da", "de", "el",
			"en", "en_GB", "en_US", "es", "es_419", "et", "fa",
			"fi", "fil", "fr", "gu", "he", "hi", "hr", "hu", "id",
			"it", "ja", "kn", "ko", "lt", "lv", "ml", "mr", "ms",
			"nl", "no", "pl", "pt_BR", "pt_PT", "ro", "ru", "sk",
			"sl", "sr", "sv", "sw", "ta", "te", "th", "tr", "uk",
			"vi", "zh_CN", "zh_TW"]
_SCRIPT_EXTS = [".js"]
_MSG = "message"
_DSC = "description"
_R_KEY = "msgjsonhelper"
_R_SCOPE = "highlight"
_R_ICON = ""
_R_FLGS = 0
_MSG_NAME_REG = '^[_A-Za-z][_A-Za-z1-9]+$'
_JSON_PREFIX = "__MSG_"
_JSON_SUFFIX = "__"
_JS_PREFIX = r"[^_A-Za-z1-9]chrome\s*[.]\s*i18n\s*[.]\s*getMessage\s*\(\s*$"
_JS_SUFFIX = r"^\s*\)"
_JS_FORMAT = "chrome.i18n.getMessage('{0}')"


class ReplaceCommand(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		if "a" in args and "b" in args and "text" in args:
			r = sublime.Region(args["a"], args["b"])
			self.view.replace(edit, r, args["text"])


class ChromeExtensionI18nHelperCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		file_name = self.view.file_name();
		if not file_name:
			return

		base_name = os.path.basename(file_name).lower()
		ext_name = os.path.splitext(file_name)[1].lower()

		cmd_helper = None
		if base_name == _MANIFEST_JSON_FILE:
			cmd_helper = ManifestHelper(self.view)
		elif ext_name in _SCRIPT_EXTS:
			cmd_helper = JavaScriptHelper(self.view)

		if cmd_helper:
			try:
				cmd_helper.setup_regions()
				cmd_helper.run()
			except:
				cmd_helper.cancel()
				raise
		elif base_name == _MESSAGES_JSON_FILE:
			self.view.run_command("message_json_helper")
		else:
			sublime.message_dialog("not support file.")


class I18nHelper:
	def __init__(self, view):
		settings = sublime.load_settings(_SETTINGS_NAME)
		self.def_loc = settings.get("default_locale")
		self.sup_locs = settings.get("support_locales")
		self.gen_dsc = settings.get("generate_description")
		self.indent = settings.get("indent")
		self.sort_keys = settings.get("sort_keys")
		self.msg_name_prefix = settings.get("msg_name_prefix")

		if self.def_loc not in _LOCALES:
			sublime.error_message('invalid settings : "default_locale": "'
									+ self.def_loc + '"')
			view.window().open_file("${packages}/User/" + _SETTINGS_NAME)
			raise Exception('invalid settings "default_locale"', self.def_loc)

		for loc in self.sup_locs:
			if loc not in _LOCALES:
				sublime.error_message('invalid settings : "support_locales": [..."'
									+ loc + '" ...]')
				view.window().open_file("${packages}/User/" + _SETTINGS_NAME)
				raise Exception('invalid settings : "support_locales"', loc)

		self.view = view
		self.def_msg = self.read_default_message_json()

	def __del__(self):
		self.cancel()

	def run(self):
		pass

	def get_default_message_json_path(self):
		pass

	def cancel(self):
		self.erase_regions()

	def read_default_message_json(self):
		def_loc_path = self.get_default_message_json_path()

		if def_loc_path == None:
			raise Exception('not found "' + _LOCALES_DIR + '" folder.')

		if not os.path.isfile(def_loc_path):
			dir_name = os.path.dirname(def_loc_path)
			if not os.path.isdir(dir_name):
				os.makedirs(dir_name)
			with open(def_loc_path, 'w') as fp:
				fp.writelines("{\n}");

		return self.read_json(def_loc_path)

	def write_default_message_json(self):
		def_loc_path = self.get_default_message_json_path()
		self.write_json(def_loc_path, self.def_msg)

	def read_json(self, path):
		with open(path, 'r') as fp:
			return json.load(fp)

	def write_json(self, path, obj):
		with open(path, 'w') as fp:
			json.dump(obj, fp, sort_keys = self.sort_keys, indent = self.indent)

	def add_msg(self, name, msg, dsc):
		msg_obj = {}
		msg_obj[_MSG] = msg
		if self.gen_dsc:
			msg_obj[_DSC] = dsc
		self.def_msg[name] = msg_obj
		print("name: '" + name + "', msg: '" + msg + "'")
		self.write_default_message_json()

	def setup_regions(self):
		sels = []
		for s in self.view.sel():
			r = self.view.extract_scope(s.a)
			str = self.view.substr(r)
			if self.is_match(str, '"', '"') or self.is_match(str, "'", "'"):
				sels.append(sublime.Region(r.a + 1, r.b - 1))

		self.reset_regions(sels)

	def reset_regions(self, sel):
		self.view.erase_regions(_R_KEY)
		sels = [s for s in sel if not s.empty()]
		if len(sels) > 0:
			self.view.add_regions(_R_KEY, sels, _R_SCOPE, _R_ICON, _R_FLGS)

	def peek_region(self):
		regions = self.view.get_regions(_R_KEY)
		if len(regions) > 0:
			return regions[0]
		return None

	def pop_region(self):
		regions = self.view.get_regions(_R_KEY)
		if len(regions) > 0:
			r = regions[0]
			self.reset_regions(regions[1:])
			return r
		return None

	def erase_regions(self):
		self.view.erase_regions(_R_KEY)

	def is_match(self, str, prefix, suffix):
		return str.startswith(prefix) and str.endswith(suffix)

	def is_valid_name(self, str):
		return re.match(str, _MSG_NAME_REG) == None

	def get_default_msg_name(self):
		for i in range(1, 9999):
			tmp = str.format("{0}{1:04d}", self.msg_name_prefix, i)
			if tmp not in self.def_msg:
				return tmp
		return ""


class ManifestHelper(I18nHelper): 
	def get_default_message_json_path(self):
		file_name = self.view.file_name()
		dir_name = os.path.dirname(file_name)
		return os.path.abspath(os.path.join(dir_name, _LOCALES_DIR,
									self.def_loc, _MESSAGES_JSON_FILE))

	def on_cancel(self):
		self.cancel()

	def register_msg(self, name, msg, dsc):
		self.add_msg(name, msg, dsc)

		text = _JSON_PREFIX + name + _JSON_SUFFIX
		r = self.pop_region()
		self.view.run_command("replace", {"a": r.a, "b": r.b, "text": text})
		self.run()

	def run(self):
		sel = self.peek_region()
		if sel == None:
			return

		selstr = self.view.substr(sel)
		if self.is_match(selstr, _JSON_PREFIX, _JSON_SUFFIX):
			self.run_update(sel, selstr)
		else:
			self.run_new(sel, selstr)

	def run_new(self, sel, selstr):
		self.cur_msg_name = self.get_default_msg_name()
		self.cur_msg_str = selstr
		self.cur_msg_dsc = ""

		self.view.show(self.peek_region())
		self.input_msg_name()

	def input_msg_name(self):
		self.view.window().show_input_panel("Input message name:",
			self.cur_msg_name, self.on_done_msg_name, None, self.on_cancel)

	def on_done_msg_name(self, text):
		if not self.is_valid_name(text):
			sublime.error_message("invalid message name")
			self.input_msg_name()
			return

		self.cur_msg_name = text
		if text in self.def_msg:
			cnfmsg = "Input message name with the same name already exists.\n"
			cnfmsg += "Do you overwrite it ?"
			if not sublime.ok_cancel_dialog(cnfmsg, "Yes, I do."):
				return

		self.register_msg(self.cur_msg_name, self.cur_msg_str, self.cur_msg_dsc)

	def run_update(self, sel, selstr):
		self.cur_msg_name = selstr[len(_JSON_PREFIX):
									-len(_JSON_SUFFIX)]
		self.cur_msg_str = ""
		self.cur_msg_dsc = ""

		if self.cur_msg_name in self.def_msg:
			msg_obj = self.def_msg[self.cur_msg_name]
			self.cur_msg_str = msg_obj[_MSG] if _MSG in msg_obj else ""
			self.cur_msg_dsc = msg_obj[_DSC] if _DSC in msg_obj else ""

		self.view.show(self.peek_region())
		self.input_msg_text()

	def input_msg_text(self):
		self.view.window().show_input_panel("update message:",
			self.cur_msg_str, self.on_done_msg_text, None, self.on_cancel)

	def on_done_msg_text(self, text):
		self.cur_msg_str = text
		self.register_msg(self.cur_msg_name, self.cur_msg_str, self.cur_msg_dsc)


class JavaScriptHelper(I18nHelper):
	def get_default_message_json_path(self):
		file_name = self.view.file_name()
		dir_name = os.path.dirname(file_name)
		
		test_path = os.path.abspath(os.path.join(dir_name, _LOCALES_DIR))
		if os.path.isdir(test_path):
			return os.path.join(test_path, self.def_loc, _MESSAGES_JSON_FILE)

		test_path = os.path.abspath(os.path.join(dir_name, "..", _LOCALES_DIR))
		if os.path.isdir(test_path):
			return os.path.join(test_path, self.def_loc, _MESSAGES_JSON_FILE)

		return None

	def on_cancel(self):
		self.cancel()

	def register_msg(self, name, msg, dsc, isNew):
		self.add_msg(name, msg, dsc)

		text = str.format(_JS_FORMAT, name)
		r = self.pop_region()
		if isNew:
			self.view.run_command("replace",
				{"a": r.a - 1, "b": r.b + 1, "text": text})
		self.run()

	def run(self):
		sel = self.peek_region()
		if sel == None:
			return

		selstr = self.view.substr(sel)

		left = (sel.a - 32) if (sel.a - 32) > 0 else 0
		
		pre = self.view.substr(sublime.Region(left, sel.a - 1))
		suf = self.view.substr(sublime.Region(sel.b + 1, sel.b + 16))

		if re.search(_JS_PREFIX, pre) != None and re.search(_JS_SUFFIX, suf) != None:
			self.run_update(sel, selstr)
		else:
			self.run_new(sel, selstr)

	def run_new(self, sel, selstr):
		self.cur_msg_name = self.get_default_msg_name()
		self.cur_msg_str = selstr
		self.cur_msg_dsc = ""

		self.view.show(self.peek_region())
		self.input_msg_name()

	def input_msg_name(self):
		self.view.window().show_input_panel("Input message name:",
			self.cur_msg_name, self.on_done_msg_name, None, self.on_cancel)

	def on_done_msg_name(self, text):
		if not self.is_valid_name(text):
			sublime.error_message("invalid message name")
			self.input_msg_name()
			return

		self.cur_msg_name = text
		if text in self.def_msg:
			cnfmsg = "Input message name with the same name already exists.\n\n"
			cnfmsg += "Do you overwrite it ?"
			if not sublime.ok_cancel_dialog(cnfmsg, "Yes, I do."):
				return

		self.register_msg(self.cur_msg_name, self.cur_msg_str,
							self.cur_msg_dsc, True)

	def run_update(self, sel, selstr):
		self.cur_msg_name = selstr
		self.cur_msg_str = ""
		self.cur_msg_dsc = ""

		if self.cur_msg_name in self.def_msg:
			msg_obj = self.def_msg[self.cur_msg_name]
			self.cur_msg_str = msg_obj[_MSG] if _MSG in msg_obj else ""
			self.cur_msg_dsc = msg_obj[_DSC] if _DSC in msg_obj else ""

		self.view.show(self.peek_region())
		self.input_msg_text()

	def input_msg_text(self):
		self.view.window().show_input_panel("update message:",
			self.cur_msg_str, self.on_done_msg_text, None, self.on_cancel)

	def on_done_msg_text(self, text):
		self.cur_msg_str = text
		self.register_msg(self.cur_msg_name, self.cur_msg_str,
							self.cur_msg_dsc, False)


class MessageJsonHelperCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		file_name = self.view.file_name()
		current_path = os.path.dirname(file_name)
		locale_name = os.path.basename(current_path)
		locales_path = os.path.dirname(file_name)
		locales_name = os.path.basename(locales_path)

		if locales_name == _LOCALES_DIR and locale_name in _LOCALES:
			settings = sublime.load_settings(_SETTINGS_NAME)
			self.locales_dir = locales_path
			self.def_loc = settings.get("default_locale")
			self.gen_dsc = settings.get("generate_description")
			self.indent = settings.get("indent")
			self.sort_keys = settings.get("sort_keys")
			self.msg_name_prefix = settings.get("msg_name_prefix")

			if locale_name == self.def_loc:
				self.run_default_locale()
			else:
				self.run_other_locale()
		else:
			print ("invalid locale")

	def run_default_locale(self):
		pass

	def run_other_locale(self):
		pass
