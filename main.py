from http.server import SimpleHTTPRequestHandler, HTTPServer, HTTPStatus
import ctypes, html, io, os, subprocess, sys, urllib

class FMHandler(SimpleHTTPRequestHandler):
  def do_GET(self):
    if len(self.path) > 2 and self.path[-2] == '?':
      self.process(self.path[-1], self.path[1:-2])
      self.path = self.path[:1+self.path.rfind('/')]
    super().do_GET()

  def do_POST(self):
    size = int(self.headers['content-length'])
    boundary = self.headers['content-type'].split("=")[1].encode()
    line = self.rfile.readline()
    size -= len(line)
    line = self.rfile.readline()
    size -= len(line)
    s = line.decode('utf-8')
    l = s.find('filename=')
    fn = s[l+10:-3]
    line = self.rfile.readline()
    size -= len(line)
    line = self.rfile.readline()
    size -= len(line)
    last = self.rfile.readline()
    size -= len(last)
    if size > 0 and len(fn) > 0:
      with open(fn, 'wb') as w:
        while size > 0:
          line = self.rfile.readline()
          size -= len(line)
          if boundary in line:
            last = last[0:-1]
            if last.endswith(b'\r'):
                last = last[0:-1]
            w.write(last)
          else:
            w.write(last)
            last = line
    if len(self.path) > 2 and self.path[-2] == '?':
      self.path = self.path[:1+self.path.rfind('/')]
    super().do_GET()

  def process(self, cmd, f):
    path = self.translate_path(f)
    s = path.rfind('/')
    l = path[:s]
    r = path[s+1:]
    if cmd == 'd':
      subprocess.run(["rm", "-rf", path])
    elif cmd == 'x':
      subprocess.run(["bsdtar", "-C", l, "-xf", r])
    elif cmd == 't':
      subprocess.run(["bsdtar", "-C", l, "-acf", path+'.tar', r])
    elif cmd == 'z':
      subprocess.run(["bsdtar", "-C", l, "-acf", path+'.7z', r])

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
    r.append('<body>\n<h1>%s</h1>' % title)
    r.append('<form ENCTYPE="multipart/form-data" method="post">')
    r.append('<input name="file" type="file"/>')
    r.append('<input type="submit" value="upload"/></form>\n<table border=1>')
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
