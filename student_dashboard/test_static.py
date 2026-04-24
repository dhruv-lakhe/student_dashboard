import urllib.request
import sys

urls = [
    'http://localhost:8000/',
    'http://localhost:8000/static/assets/css/dark.min.css',
    'http://localhost:8000/static/assets/js/hope-ui.js',
]

with open('test_results.txt', 'w') as f:
    for url in urls:
        try:
            r = urllib.request.urlopen(url, timeout=5)
            ct = r.headers.get('Content-Type', 'unknown')
            f.write(f'OK  {r.getcode()}  {ct:<30}  {url}\n')
        except Exception as e:
            f.write(f'ERR {type(e).__name__:15}  {url}\n')
            f.write(f'    {e}\n')
