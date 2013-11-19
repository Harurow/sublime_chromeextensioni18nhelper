# -*- coding: utf-8 -*-
import sublime
import sublime_plugin
import codecs
import json
import os
import re
import urllib
import webbrowser
from datetime import *


_FORM_URL = "http://www.google.com/translate_t?langpair={0}|{1}&text={2}"
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
_SCRIPT_EXT = ".js"
_MSG = "message"
_DSC = "description"
_R_KEY = "chromeextensioni18nhelper"
_R_KEY2 = "chromeextensioni18nhelper2"
_R_SCOPE = "highlight"
_R_ICON = ""
_R_FLGS = 0
_MSG_NAME_REG = '^[_A-Za-z][_A-Za-z1-9]+$'
_JSON_PREFIX = r"__MSG_"
_JSON_SUFFIX = r"__"
_JSON_FORMAT = '"__MSG_{0}__"'
_JS_PREFIX = r"[^_A-Za-z1-9]chrome\s*[.]\s*i18n\s*[.]\s*getMessage\s*\(\s*$"
_JS_SUFFIX = r"^\s*\)"
_JS_FORMAT = 'chrome.i18n.getMessage("{0}")'
_MSG_PREFIX = "{\s*['\"]message['\"]\s*:\s*"


_MODE_NONE = "none"
_MODE_MANIFEST = "manifest.json"
_MODE_JAVASCRIPT = "*.js"
_MODE_DEF_MESSAGE = "default messages.json"
_MODE_OTH_MESSAGE = "other messages.json"

_mode = _MODE_NONE


class ChromeExtensionI18nHelperEventListener(sublime_plugin.EventListener):
	def set_mode(self, val):
		global _mode
		_mode = val

	def on_activated(self, view):
		file_name = view.file_name()
		if file_name == None:
			self.set_mode(_MODE_NONE)
			return

		base_name = os.path.basename(file_name)
		if base_name == _MANIFEST_JSON_FILE:
			self.set_mode(_MODE_MANIFEST)
			return

		if base_name.endswith(_SCRIPT_EXT):
			self.set_mode(_MODE_JAVASCRIPT)
			return

		if base_name != _MESSAGES_JSON_FILE:
			self.set_mode(_MODE_NONE)
			return

		path = os.path.dirname(file_name)
		locale = os.path.basename(path)

		if locale not in _LOCALES:
			self.set_mode(_MODE_NONE)
			return

		path = os.path.dirname(path)
		locales = os.path.basename(path)
		if locales != _LOCALES_DIR:
			self.set_mode(_MODE_NONE)
			return

		settings = sublime.load_settings(_SETTINGS_NAME)
		def_locale = settings.get("default_locale")

		if def_locale == locale:
			self.set_mode(_MODE_DEF_MESSAGE)
		else:
			self.set_mode(_MODE_OTH_MESSAGE)

# menu control

class ChromeExtensionI18nHelperContextCommand(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		method = args["method"]
		if method == "trans":
			self.view.run_command("chrome_extension_i18n_google_trans")
		else:
			self.view.run_command("chrome_extension_i18n_helper", args)

	def is_visible(self, **args):
		method = args["method"]
		return ( method == "copy_to" and _mode == _MODE_DEF_MESSAGE
				or method == "copy_from" and _mode == _MODE_OTH_MESSAGE
				or (method == "add_message" or method == "paste_message") and (
						_mode == _MODE_MANIFEST or _mode == _MODE_JAVASCRIPT)
				or method == "trans" and _mode == _MODE_OTH_MESSAGE)

	def is_enabled(self, **args):
		method = args["method"]

		if _mode == _MODE_MANIFEST or _mode == _MODE_JAVASCRIPT:
			if method == "paste_message":
				return True

			for s in self.view.sel():
				r = self.view.extract_scope(s.a)
				str = self.view.substr(r)
				if (str.startswith('"') and str.endswith('"') or
					str.startswith("'") and str.endswith("'")):
					return True
			return False

		if method == "trans" and _mode == _MODE_OTH_MESSAGE:
			s = self.view.sel()[0]
			r = self.view.extract_scope(s.a)
			str = self.view.substr(r)
			if (str.startswith('"') and str.endswith('"') or
				str.startswith("'") and str.endswith("'")):
				return True
			return False

		return True


class ChromeExtensionI18nHelperSidebarCommand(sublime_plugin.WindowCommand):
	def run(self, paths, **args):
		v = self.window.active_view()
		if v:
			v.run_command("message_json_helper")

	def is_visible(self, paths, **args):
		if len(paths) == 0 or self.window.active_view() == None:
			return False
		if (paths[0] != self.window.active_view().file_name()):
			return False

		return ( args["method"] == "copy_to" and _mode == _MODE_DEF_MESSAGE or
				 args["method"] == "copy_from" and _mode == _MODE_OTH_MESSAGE )

# json functions

def open_view(path):
	for w in sublime.windows():
		v = w.find_open_file(path)
		if v != None:
			return v
	return None


def read_json(path):
	v = open_view(path)
	if v != None:
		all_rgn = sublime.Region(0, v.size())
		all_str = v.substr(all_rgn)
		return json.loads(all_str)
	else:
		with codecs.open(path, 'r', 'utf-8') as fp:
			return json.load(fp)


def write_json(path, obj, sort_keys, indent):
	dir_name = os.path.dirname(path)
	if not os.path.isdir(dir_name):
		os.makedirs(dir_name)

	with codecs.open(path, 'w', 'utf-8') as fp:
		json.dump(obj, fp, ensure_ascii = False,
			sort_keys = sort_keys, indent = indent)

# translate

class ChromeExtensionI18nGoogleTransCommand(sublime_plugin.TextCommand):
	def translate(self, from_lang, to_lang, text, newTab):
		if hasattr(urllib, "parse"):
			text = urllib.parse.quote_plus(text.strip())
		else:
			text = urllib.quote_plus(text.strip())
		url = str.format(_FORM_URL, from_lang, to_lang, text)
		if newTab:
			webbrowser.open_new_tab(url)
		else:
			webbrowser.open(url)

	def run(self, edit, **args):
		file_name = self.view.file_name()
		current_path = os.path.dirname(file_name)
		locale = os.path.basename(current_path)

		settings = sublime.load_settings(_SETTINGS_NAME)
		def_loc = settings.get("default_locale")
		new_tab = settings.get("translate_new_tab")

		s = self.view.sel()[0]
		r = self.view.extract_scope(s.a)
		str = self.view.substr(r)[1:-1]

		self.translate(def_loc, locale, str, new_tab)

# command

class ReplaceCommand(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		if "a" in args and "b" in args and "text" in args:
			r = sublime.Region(args["a"], args["b"])
			self.view.replace(edit, r, args["text"])


class MessageJsonHelperCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		file_name = self.view.file_name()
		current_path = os.path.dirname(file_name)
		locale_name = os.path.basename(current_path)
		locales_path = os.path.dirname(current_path)
		locales_name = os.path.basename(locales_path)

		if locales_name == _LOCALES_DIR and locale_name in _LOCALES:
			settings = sublime.load_settings(_SETTINGS_NAME)
			self.locales_dir = locales_path
			self.def_loc = settings.get("default_locale")
			self.support_locales = settings.get("support_locales")
			self.gen_dsc = settings.get("generate_description")
			self.indent = settings.get("indent")
			self.sort_keys = settings.get("sort_keys")
			self.translate_new_tab = settings.get("translate_new_tab")

			self.locales_path = locales_path

			if locale_name == self.def_loc:
				self.run_default_locale()
			else:
				self.run_other_locale()
		else:
			sublime.status_message("invalid locale")

	def make_template_json(self, path):
		tmpl_loc = read_json(path)
		for k in tmpl_loc.keys():
			tmpl_loc[k][_DSC] = "from '" + self.def_loc \
								+ "' : " + tmpl_loc[k][_MSG]
		return tmpl_loc

	def run_default_locale(self):
		items = []
		items_loc = []

		items.append("copy/merge to supported all files")
		items_loc.append(self.support_locales)

		for s in self.support_locales:
			if os.path.isfile(os.path.join(self.locales_path
					, s, _MESSAGES_JSON_FILE)):
				method = "merge "
			else:
				method = "copy "

			items.append(method + "to '" + s + "'")
			items_loc.append([s])

		def on_done(index):
			if index < 0:
				return
			locs = items_loc[index]

			tmpl_loc = self.make_template_json(self.view.file_name())

			for loc in locs:
				path = os.path.join(self.locales_path, loc, _MESSAGES_JSON_FILE)
				if (os.path.isfile(path)):
					print("merge to " + loc)
					o_loc = read_json(path)
					for k in tmpl_loc.keys():
						if k not in o_loc:
							o_loc[k] = tmpl_loc[k]
					write_json(path, o_loc, self.sort_keys, self.indent)
				else:
					print("copy to " + loc)
					write_json(path, tmpl_loc, self.sort_keys, self.indent)
				self.view.window().open_file(path)

		self.view.window().show_quick_panel(items, on_done)

	def run_other_locale(self):
		oth_path = self.view.file_name()
		def_path = os.path.join(os.path.dirname(os.path.dirname(oth_path)),
								self.def_loc, _MESSAGES_JSON_FILE)
		if not os.path.isfile(def_path):
			sublime.error_message(str.format(
				"not exists default({0}) messages.json file.", self.def_loc))
			return

		tmpl_loc = self.make_template_json(def_path)

		print("merge from " + self.def_loc)
		o_loc = read_json(oth_path)
		for k in tmpl_loc.keys():
			if k not in o_loc:
				o_loc[k] = tmpl_loc[k]
		write_json(oth_path, o_loc, self.sort_keys, self.indent)


class ChromeExtensionI18nHelperCommand(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		file_name = self.view.file_name();
		if not file_name:
			return

		base_name = os.path.basename(file_name).lower()
		ext_name = os.path.splitext(file_name)[1].lower()

		if args["method"] == "paste_message":
			mh = MessageHelper(self.view)
			msgs = mh.read_default_message_json();

			messages = [];
			ids = [];
			for m in msgs:
				ids.append(m);
				messages.append(msgs[m]["message"]);

			def on_done(index):
				if index < 0:
					return;

				for s in self.view.sel():
					self.view.run_command("replace",
						{
							"a": s.a,
							"b": s.b,
							"text": '"' + ids[index] + '"'
						})

			self.view.window().show_quick_panel(messages, on_done);
		else:
			cmd_helper = None
			if base_name == _MANIFEST_JSON_FILE:
				cmd_helper = ManifestHelper(self.view)
			elif ext_name == _SCRIPT_EXT:
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
				sublime.message_dialog("NOT SUPPORT FILE TYPE.\n\n" \
					+ "    Support files\n" \
					+ "        - javascripts(*.js)\n"
					+ "        - manifest.json\n"
					+ "        - messages.json")


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
				sublime.error_message(
					'invalid settings : "support_locales": [..."'
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

		return read_json(def_loc_path)

	def write_default_message_json(self):
		def_loc_path = self.get_default_message_json_path()
		write_json(def_loc_path, self.def_msg, self.sort_keys, self.indent)

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
				sels.append(sublime.Region(r.a, r.b))

		self.reset_regions(sels)

	def reset_regions(self, sel):
		self.erase_regions()
		sels = [s for s in sel if not s.empty()]
		if len(sels) > 0:
			self.view.add_regions(_R_KEY, sels, _R_SCOPE, _R_ICON, _R_FLGS | sublime.DRAW_NO_FILL)

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
		self.view.erase_regions(_R_KEY2)

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


class MessageHelper(I18nHelper):
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

	def run(self):
		sel = self.peek_region()
		if sel == None:
			return

		self.view.add_regions(_R_KEY2, [sel], _R_SCOPE, _R_ICON, _R_FLGS)

		str = self.view.substr(sel)
		if self.is_update(sel):
			self.run_update(sel, str)
		else:
			self.run_new(sel, str)

	def run_new(self, sel, selstr):
		self.cur_msg_name = self.get_default_msg_name()
		self.cur_msg_str = selstr[1:-1]
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

	def run_update(self, sel, str):
		self.cur_msg_name = self.get_message_name(str)
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

	def register_msg(self, name, msg, dsc, isNew):
		self.add_msg(name, msg, dsc)

		text = str.format(self.format, name)
		r = self.pop_region()
		if isNew:
			self.view.run_command("replace", {"a": r.a, "b": r.b, "text": text})
		self.run()

	def is_update(self, sel):
		pass

	def get_message_name(self, str):
		pass


class ManifestHelper(MessageHelper):
	def __init__(self, view):
		MessageHelper.__init__(self, view)
		self.format = _JSON_FORMAT

	def is_update(self, sel):
		str = self.view.substr(sel)[1:-1]
		return self.is_match(str, _JSON_PREFIX, _JSON_SUFFIX)

	def get_message_name(self, str):
		return str[len(_JSON_PREFIX) + 1 :-(len(_JSON_SUFFIX) + 1)]


class JavaScriptHelper(MessageHelper):
	def __init__(self, view):
		MessageHelper.__init__(self, view)
		self.format = _JS_FORMAT

	def is_update(self, sel):
		left = (sel.a - 32) if (sel.a - 32) > 0 else 0
		
		pre = self.view.substr(sublime.Region(left, sel.a))
		suf = self.view.substr(sublime.Region(sel.b, sel.b + 16))

		if re.search(_JS_PREFIX, pre) != None \
				and re.search(_JS_SUFFIX, suf) != None:
			return True
		return False

	def get_message_name(self, str):
		return str[1:-1]