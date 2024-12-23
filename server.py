import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import sys
import json
import re
from sheet import *
import argparse
import pdf2image


class RequestHandler(SimpleHTTPRequestHandler):
    def parsePDF(self, pdf_path, path):
        meta_path = os.path.join(path, 'info.json')
        if not os.path.exists(meta_path):
            meta = {"name": os.path.basename(path)}
        else:
            meta = json.load(open(meta_path))

        pdf_hash = hash(open(pdf_path, 'rb').read())
        if 'pdfHash' in meta and meta['pdfHash'] == pdf_hash:
            return

        images = pdf2image.convert_from_path(pdf_path)
        for i, img in enumerate(images):
            img.save(os.path.join(path, f'{i}.png'))

        meta['pdfHash'] = pdf_hash
        with open(meta_path, 'w') as f:
            json.dump(meta, f)

    def handlePost(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        options = json.loads(post_data)

        # Call the function from the sheet module

        if 'url' not in options:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(
                {'error': 'No URL provided'}).encode('utf-8'))
            return

        video_url = options["url"]

        if len(video_url) < 1 or video_url[0] in [' ', '\n', '\t', '.', '/']:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(
                {'error': 'Invalid URL'}).encode('utf-8'))
            return

        skip = None
        if 'skip' in options:
            skip = options["skip"]

        invert = False
        if 'invert' in options:
            invert = options["invert"]

        similarity = 0.85
        if 'similarity' in options:
            similarity = options["similarity"]

        video_name = video_url
        if video_name[-1] == '/':
            video_name = video_name[:-1]
        video_name = video_name.split('/')[-1]
        path = options["name"] if 'name' in options is not None else video_name

        if os.path.exists(path):
            # delete existing files
            for file in os.listdir(path):
                os.remove(os.path.join(path, file))
        os.makedirs(path, exist_ok=True)

        mode = 3
        if 'mode' in options:
            mode = options["mode"]

        meta = {
            'url': video_url,
            'name': path,
            'addTime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'mode': mode,
            'skip': skip if skip is not None else 0,
            'similarity': similarity,
            'invert': invert,
        }
        with open(os.path.join(path, 'info.json'), 'w') as f:
            json.dump(meta, f)

        if mode == 1:
            universal(video_url, variance=False, skip=skip,
                      path=path, similarity_threshold=similarity)
        elif mode == 2:
            universal(video_url, variance=True, skip=skip,
                      path=path, similarity_threshold=similarity)
        elif mode == 3:
            color_variance(video_url, skip=skip, path=path,
                           similarity_threshold=similarity)
        elif mode == 4:
            full(video_url, skip=skip, path=path,
                 similarity_threshold=similarity)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(
                {'error': 'Invalid mode'}).encode('utf-8'))
            return

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'result': 'Ok'}).encode('utf-8'))

    def end_headers(self):
        origin = self.headers.get("Origin")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        else:
            self.send_header("Access-Control-Allow-Origin", "*")

        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS, POST")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.end_headers()

    def do_POST(self):
        if self.path == "/":
            try:
                self.handlePost()
            except json.decoder.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(
                    {'error': 'Invalid request JSON'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                print(e, type(e))
        else:
            super().do_POST()

    def do_GET(self):
        if self.path == "/list":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            def dir_filter(path):
                return not path.startswith('.') and os.path.isdir(path)
            dir_list = list(filter(dir_filter, os.listdir('.')))
            tag_pattern = re.compile(r"\[(.*?)\]")

            self.wfile.write(json.dumps(dir_list).encode('utf-8'))

        elif self.path.startswith('/sheet'):
            import urllib.parse

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            dir_name = os.path.join('.', *(urllib.parse.unquote(f"{self.path}").rsplit('/')[2:]))

            print(dir_name)

            if os.path.exists(dir_name):
                file_content = os.listdir(dir_name)
                meta_file = os.path.join(dir_name, 'info.json')

                entry = {}

                # handle pdf file
                pdf_files = [f for f in file_content if f.endswith('.pdf')]
                if len(pdf_files) > 0:
                    self.parsePDF(os.path.join(
                        dir_name, pdf_files[0]), dir_name)

                    file_content = os.listdir(dir_name)
                    for pdf_file in pdf_files:
                        file_content.remove(pdf_file)

                # handle meta file
                if os.path.exists(meta_file) and os.path.isfile(meta_file):
                    file_content.remove('info.json')
                    with open(meta_file) as f:
                        meta = json.load(f)
                        entry['meta'] = meta
                        if 'name' in meta:
                            entry['name'] = meta['name']

                # leave out directories
                file_content = [f for f in file_content if os.path.isfile(os.path.join(dir_name, f))]

                def extract_number(filename):
                    try:
                        return int(filename.split('.')[0])
                    except ValueError:
                        print(f"Skipping invalid filename: {filename}")
                        return float('inf')

                try:
                    file_content.sort(key=extract_number)
                except Exception as e:
                    print(f"Sorting error: {e}")
                    file_content.sort()

                entry['content'] = file_content
                entry['pages'] = len(file_content)

                self.wfile.write(json.dumps(entry).encode('utf-8'))

        else:
            super().do_GET()

    def translate_path(self, path):
        path = super().translate_path(path)
        if os.path.exists(path):
            return path
        else:
            return os.path.join('serve', path)

    def log_message(self, format, *args):
        forwarded_for = self.headers.get('X-Forwarded-For')
        client_ip = forwarded_for.split(',')[0] if forwarded_for else self.address_string()
        sys.stderr.write("%s - - [%s] %s\n" % (client_ip, self.log_date_time_string(), format % args))

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
    httpd = HTTPServer(('0.0.0.0', port), RequestHandler)
    print(f"Serving on port {port}...")
    httpd.serve_forever()
