import sublime
import sublime_plugin
import os
import subprocess
import json

ALLOWED_FILE_EXTENSIONS = [
  'js',
  'jsx'
]

PLUGIN_NODE_PATH = os.path.join(
  sublime.packages_path(), 
  os.path.dirname(os.path.realpath(__file__)),
  'import-cost.js'
)

cache = {};

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
    final_data = [];
    final_modules = []
    for module in modules:
      if module:
        if self.check_module(module):
          final_modules.append(module)
          final_data.append({"region": lines[cnt], "module": module})
      cnt = cnt + 1

    if len(final_modules) is 0:
      return;

    args = []
    try:
      args = json.dumps(final_modules)
    except OSError:
      print('Something went wrong!')

    print('test', args)
    data = self.node_bridge(PLUGIN_NODE_PATH, [
      self.get_view_base_path(), 
      args
    ]);

    print('data', data)

    cnt = 0
    for module in final_data:
      line = self.view.line(module["region"].a)
      phantoms.append(sublime.Phantom(
        sublime.Region(line.b),
        '''
          <style>html, body {margin: 0; padding:0;}</style>
          <span style="color: green; padding: 0 10px;">Yes</span>
        ''',
        sublime.LAYOUT_INLINE
      ))
      cnt = cnt + 1
    self.phantoms.update(phantoms)

  def check_module(self, module_name):
    if module_name.startswith("."):
      return False
    node_path = self.get_node_modules_path()
    if node_path is False:
      return False
    if os.path.isdir(node_path + module_name + '/') is False:
      return False
    return True

  def get_view_base_path(self):
    return self.view.window().folders()[0]

  def get_node_modules_path(self):
    node_path = self.get_view_base_path() + '/node_modules/'
    if os.path.isdir(node_path):
      return node_path
    return False

  def is_file_allowed(self):
    filename = self.view.file_name()
    if not filename:
      return False
    file_ext = os.path.splitext(filename)[1][1:]
    if file_ext in ALLOWED_FILE_EXTENSIONS:
      return True
    return False

  def node_bridge(self, bin, args=[]):
    print('args', args)
    env = os.environ.copy()
    env['PATH'] += ':/usr/local/bin'
    try:
      process = subprocess.Popen(
        ['node'] + [bin],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        startupinfo=None
      )
    except OSError:
      print('Error: Couldn\'t find "node" in "%s"' % env['PATH'])
    stdout, stderr = process.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    if stderr:
      print('Error: %s' % stderr)
    else:
      return stdout
