import sublime
import sublime_plugin
import os
import subprocess
import json

Path = os.path

PLUGIN_NAME = __package__
PLUGIN_PATH = Path.dirname(Path.realpath(__file__))
SETTINGS_FILE = '{0}.sublime-settings'.format(PLUGIN_NAME)

PLUGIN_NODE_PATH = Path.join(
  Path.dirname(Path.realpath(__file__)),
  'import-cost.js'
)

cache = {}

class ImportCostCommand(sublime_plugin.ViewEventListener):
  def __init__(self, view):
    self.view = view
    self.base_path = None
    self.phantoms = sublime.PhantomSet(view)
    self.update_phantoms()

  def on_new_async(self):
    if self.get_setting('check_on_open', True):
      self.update_phantoms()

  def on_modified_async(self):
    if self.get_setting('check_on_save', True):
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
    final_data = []
    final_modules = []
    for module in modules:
      if module and self.find_root_path(module):
        final_modules.append(module)
        final_data.append({"region": lines[cnt], "module": module})
      cnt = cnt + 1

    if len(final_modules) is 0:
      return None

    args = []
    try:
      args = json.dumps(final_modules)
    except OSError:
      print('Error trying to stringify json!')
      return None

    data = self.node_bridge([self.base_path, args])
    json_data = json.loads(data)

    cnt = 0
    for module in final_data:
      size_data = json_data[cnt]
      if size_data['size']:
        line = self.view.line(module["region"].a)

        # TODO: change to settings
        kb = size_data['size'] / 1000
        color = '#666'
        if kb > self.get_setting('min_size_warning', 40.0):
          color = 'var(--yellowish)'
        if kb > self.get_setting('min_size_error', 80.0):
          color = 'var(--redish)'

        gziptxt = ''
        if (self.get_setting('show_gzip', False)):
          gzipkb = size_data['gzip'] / 1000
          gziptxt = '<span style="color: color(%s blend(var(--background) 50%%));">- %.2fkB gzip</span>' % (color, gzipkb)

        phantoms.append(sublime.Phantom(
          sublime.Region(line.b),
          '''
            <style>html, body {margin: 0; padding:0; background-color: transparent;}</style>
            <span style="background-color: transparent; color: %s; padding: 0 15px; font-size: .9rem; line-height: 1.3rem;"><b>%.2fkB</b> %s</span>
          ''' % (color, kb, gziptxt),
          sublime.LAYOUT_INLINE
        ))

      cnt = cnt + 1
    self.phantoms.update(phantoms)

  def is_file_allowed(self):
    filename = self.view.file_name()
    if not filename:
      return False
    file_ext = Path.splitext(filename)[1][1:]
    if file_ext in self.get_setting('extensions', ['js', 'jsx']):
      return True
    return False

  def node_bridge(self, args=[]):
    node_path = self.get_setting('node_path', '/usr/local/bin/node')

    if (Path.isfile(node_path) == False):
      print('Error: Couldn\'t find "node" in "%s"' % node_path)
      return None
    try:
      process = subprocess.Popen(
        [node_path, PLUGIN_NODE_PATH] + args,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
        startupinfo=None,
        shell=True
      )
    except OSError:
      print('Error: Couldn\'t find "node" in "%s"' % node_path)
    stdout, stderr = process.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    if stderr:
      print('Error: %s' % stderr)
      return None
    return stdout

  def get_setting(self, key, default_value=None):
    settings = self.view.settings().get(PLUGIN_NAME)
    if settings is None or settings.get(key) is None:
        settings = sublime.load_settings(SETTINGS_FILE)
    value = settings.get(key, default_value)
    return value

  def find_root_path(self, module_name = ''):
    if module_name.startswith('./') or module_name.startswith('../'):
      return False

    if self.base_path and \
        Path.isdir(Path.join(self.base_path, 'node_modules', module_name)):
      # If we already have the base path, use this
      return True

    # Otherwise try to determine base path
    i = 0
    check_dir = Path.dirname(self.view.file_name())
    node_dir = Path.join(check_dir, 'node_modules')
    module_dir = Path.join(node_dir, module_name)
    is_dir = Path.isdir(module_dir)
    while (i < 100 and (is_dir is False)):
      check_dir = Path.join(check_dir, '..')
      node_dir = Path.join(check_dir, 'node_modules')
      module_dir = Path.join(node_dir, module_name)
      is_dir = Path.isdir(module_dir)
      i = i + 1

    if is_dir:
      self.base_path = check_dir
      return True
    return False

