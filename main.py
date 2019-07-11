from http.server import SimpleHTTPRequestHandler, HTTPServer, HTTPStatus
import ctypes, html, io, os, subprocess, sys, urllib

class FMHandler(SimpleHTTPRequestHandler):
  def do_GET(self):
    if len(self.path) > 2 and self.path[-2] == '?':
      self.process(self.path[-1], self.path[1:-2])
      self.path = self.path[:1+self.path.rfind('/')]
    super().do_GET()

  def process(self, cmd, f):
    path = self.translate_path(f)
    if cmd == 'd':
      subprocess.run(["rm", "-rf", path])
    elif cmd == 'x':
      subprocess.run(["7z", "x", path])
    elif cmd == 't':
      subprocess.run(["7z", "a", path+'.tar', path])
    elif cmd == 'z':
      subprocess.run(["7z", "a", path+'.7z', path])
  
  def calc_size(self, num):
    for x in ['B', 'KB', 'MB', 'GB', 'TB']:
      if num < 1024.0:
        return "%3.2f %s" % (num, x)
      num /= 1024.0

  def get_free_space(self):
    if os.name == 'nt':
      free_bytes = ctypes.c_ulonglong(0)
      ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(), None, None, ctypes.pointer(free_bytes))
      return free_bytes.value
    else:
      st = os.statvfs('/')
      return st.f_bavail * st.f_frsize

  def list_directory(self, path):
    list = os.listdir(path)
    list.sort(key=lambda a: a.lower())
    r = []
    root = urllib.parse.unquote(self.path, errors='surrogatepass')
    root = html.escape(root, quote=False)
    title = 'Directory listing for %s' % root
    r.append('<html>\n<head>')
    r.append('<meta http-equiv="Content-Type" content="text/html">')
    r.append('<title>%s</title>\n</head>' % title)
    r.append('<body>\n<h1>%s</h1>\n<table border=1>' % title)
    for name in list:
      fullname = os.path.join(path, name)
      link = urllib.parse.quote(name, errors='surrogatepass')
      display = html.escape(name, quote=False)
      if os.path.isdir(fullname):
        size = ''
        bg = 'gainsboro'
        href = link + '/'
      else:
        size = self.calc_size(os.stat(fullname).st_size)
        bg = 'white'
        href = '/files' + self.path + link
      r.append('<tr bgcolor="%s"><td><a href="%s?d">D</td><td><a href="%s">%s</a></td><td>%s</td><td><a href="%s?x">X</td><td><a href="%s?t">T</td><td><a href="%s?z">Z</td></tr>' % (bg, link, href, display, size, link, link, link))
    r.append('</table>\n<br>Remaining Space: %s</body>\n</html>\n' % self.calc_size(self.get_free_space()))
    encoded = '\n'.join(r).encode('utf-8', 'surrogateescape')
    f = io.BytesIO()
    f.write(encoded)
    f.seek(0)
    self.send_response(HTTPStatus.OK)
    self.send_header("Content-type", "text/html; charset=UTF-8")
    self.send_header("Content-Length", str(len(encoded)))
    self.end_headers()
    return f

HTTPServer(('127.0.0.1', int(sys.argv[1])), FMHandler).serve_forever()
