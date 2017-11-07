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

  def on_modified_async(self):
    print('presave')
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
    # TODO: cache modules!
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
      print('Error trying to stringify json!')
      return None

    data = self.node_bridge(PLUGIN_NODE_PATH, [
      self.get_view_base_path(), 
      args
    ]);
    json_data = json.loads(data)

    cnt = 0
    for module in final_data:
      size_data = json_data[cnt];
      if size_data['size']:
        line = self.view.line(module["region"].a)

        # TODO: change to settings
        kb = size_data['size'] / 1000
        color = '#666'
        if kb > 20:
          color = 'var(--yellowish)'
        if kb > 40:
          color = 'var(--redish)'

        phantoms.append(sublime.Phantom(
          sublime.Region(line.b),
          '''
            <style>html, body {margin: 0; padding:0; background-color: transparent;}</style>
            <span style="background-color: transparent; color: %s; padding: 0 15px; font-size: .9rem; line-height: 1.2rem">%.2fkB</span>
          ''' % (color, kb),
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
    if self.view.window():
      return self.view.window().folders()[0]
    return None

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
    env = os.environ.copy()
    env['PATH'] += ':/usr/local/bin'
    try:
      process = subprocess.Popen(
        ['node'] + [bin] + args,
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
      return None
    return stdout
