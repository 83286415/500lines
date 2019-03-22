# for Python2.7

import BaseHTTPServer

# -------------------------------------------------------------------------------

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    '''Handle HTTP requests by returning a fixed 'page'.'''

    # Page to send back.
    Page = '''\
<html>
<body>
<p>Hello, web!</p>
</body>
</html>
'''

    # Handle a GET request.
    def do_GET(self):  # do_ + GET/POST etc request cmd to make a method to handle the related request
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(self.Page)))
        self.end_headers()
        self.wfile.write(self.Page)

    # def do_POST(self):
    #     self.send_response(201)
    #     self.send_header("Content-type", "text/html")
    #     self.send_header("Content-Length", str(len(self.Page)))
    #     self.end_headers()
    #     self.wfile.write(self.Page)

# -------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    serverAddress = ('', 8080)  # ''input IP like 10.6.11.81
    server = BaseHTTPServer.HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()
