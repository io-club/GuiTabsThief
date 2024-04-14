import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import json
from sheet import *
import argparse

class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    def handlePost(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        options = json.loads(post_data)

        # Call the function from the sheet module

        if 'url' not in options:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'No URL provided'}).encode('utf-8'))
            return
        
        video_url = options["url"]
        
        skip = None
        if 'skip' in options:
            skip = options["skip"]
        
        video_name = video_url
        if video_name[-1] == '/':
            video_name = video_name[:-1]
        video_name = video_name.split('/')[-1]
        path = options["name"] if 'name' in options is not None else video_name

        os.makedirs(path, exist_ok=True)
            
        mode = 3
        if 'mode' in options:
            mode = options["mode"]
            
        meta = {
            'url': video_url,
            'name': path,
            'addTime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'mode': mode,
            'skip': skip if skip is not None else 0
        }
        with open(os.path.join(path, 'info.json'), 'w') as f:
            json.dump(meta, f)

        if mode == 1:
            universal(video_url, variance=False, skip=skip, path=path)
        elif mode == 2:
            universal(video_url, variance=True, skip=skip, path=path)
        elif mode == 3:
            color_variance(video_url, skip=skip, path=path)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid mode'}).encode('utf-8'))
            return

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'result': 'Ok'}).encode('utf-8'))
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.end_headers()

    def do_POST(self):
        try:
            self.handlePost()
        except json.decoder.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid request JSON'}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            print(e, type(e))

    def do_GET(self):
        if self.path == "/list":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()


            dir_list = []
            for dir_name in os.listdir('.'):
                if os.path.isdir(dir_name):
                    import urllib.parse
                    dir_list.append({
                        'name': dir_name,
                        'href': urllib.parse.quote(f"/{dir_name}"),
                        'pages': len(os.listdir(dir_name)),
                        'content': os.listdir(dir_name)
                    })
                    meta_file = os.path.join(dir_name, 'info.json')
                    if os.path.exists(meta_file) and os.path.isfile(meta_file):
                        with open(meta_file) as f:
                            meta = json.load(f)
                            dir_list[-1]['meta'] = meta

            self.wfile.write(json.dumps(dir_list).encode('utf-8'))
        else:
            super().do_GET()

    def translate_path(self, path):
        path = super().translate_path(path)
        if os.path.exists(path):
            return path
        else:
            return os.path.join('serve', path)

if __name__ == '__main__':
    if not os.path.exists('serve'):
        os.mkdir('serve')
    os.chdir('serve')
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, help='Port number')
    args = parser.parse_args()

    # Get the port number from command line arguments
    port = args.port

    # Check if port is provided
    if port is None:
        port = 8000

    # Start the server
    httpd = HTTPServer(('localhost', port), MyHTTPRequestHandler)
    print(f"Serving on port {port}...")
    httpd.serve_forever()