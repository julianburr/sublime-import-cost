import sublime
import sublime_plugin
import os

ALLOWED_FILE_EXTENSIONS = [
  'js',
  'jsx'
]

class ImportCostCommand(sublime_plugin.ViewEventListener):
  def __init__(self, view):
    self.view = view;
    self.phantoms = sublime.PhantomSet(view)
    self.update_phantoms()

  def on_new_async(self):
    self.update_phantoms()

  def on_pre_save_async(self):
    self.update_phantoms()

  def update_phantoms(self):
    if self.is_file_allowed():
      imports = self.find_imports()
      self.calc_imports(imports)

  def find_imports(self):
    modules = []
    es6 = self.view.find_all("import (.+) from ['\"](.+)['\"]", 0, "$2", modules)
    es5 = self.view.find_all("require\\((.+)\\)", 0, "$2", modules)
    return [es6 + es5, modules]
    
  def calc_imports(self, imports):
    phantoms = []
    lines, modules = imports
    cnt = 0
    for i in lines:
      module_name = modules[cnt];
      print('check', module_name, self.check_module(module_name))
      if self.check_module(module_name):
        line = self.view.line(i.a)
        phantoms.append(sublime.Phantom(
          sublime.Region(line.b),
          '''
            <style>html, body {margin: 0; padding:0;}</style>
            <span style="color: green; padding: 0 10px;">Yes</span>
          ''',
          sublime.LAYOUT_INLINE
        ))
      else:
        line = self.view.line(i.a)
        phantoms.append(sublime.Phantom(
          sublime.Region(line.b),
          '''
            <style>html, body {margin: 0; padding:0;}</style>
            <span style="color: red; padding: 0 10px;">No</span>
          ''',
          sublime.LAYOUT_INLINE
        ))
      cnt = cnt + 1
    self.phantoms.update(phantoms)

  def check_module(self, module_name):
    if module_name.startswith("."):
      return False
    node_path = self.get_node_modules_path()
    if os.path.isdir(node_path + module_name + '/') is False:
      return False
    return True

  def get_node_modules_path(self):
    node_path = self.view.window().folders()[0] + '/node_modules/'
    if os.path.isdir(node_path):
      return node_path
    return False

  def is_file_allowed(self):
    filename = self.view.file_name()
    if not filename:
      return False
    file_ext = os.path.splitext(filename)[1][1:]
    print('file_ext', file_ext, filename)
    if file_ext in ALLOWED_FILE_EXTENSIONS:
      return True
    return False
