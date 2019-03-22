import BaseHTTPServer

#-------------------------------------------------------------------------------

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    '''Respond to HTTP requests with info about the request.'''

    # Template for page to send back.
    # Page is a class property which can be changed by class or instance, used in class's method with self.
    Page = '''\
<html>
<body>
<table>
<tr>  <td>Header</td>         <td>Value</td>          </tr>
<tr>  <td>Date and time</td>  <td>{date_time}</td>    </tr>
<tr>  <td>Client host</td>    <td>{client_host}</td>  </tr>
<tr>  <td>Client port</td>    <td>{client_port}s</td> </tr>
<tr>  <td>Command</td>        <td>{command}</td>      </tr>
<tr>  <td>Path</td>           <td>{path}</td>         </tr>
</table>
</body>
</html>
'''

    # Handle a request by constructing an HTML page that echoes the
    # request back to the caller.
    def do_GET(self):
        page = self.create_page()
        self.send_page(page)

    # Create an information page to send.
    def create_page(self):
        values = {
            'date_time'   : self.date_time_string(),
            'client_host' : self.client_address[0],
            'client_port' : self.client_address[1],
            'command'     : self.command,
            'path'        : self.path
        }  # path is the /something.html following IP from request. We can return a 404 if it is a invalid url.
        # path is the /something.html following IP from request.
        # We can return a 404 if it is a invalid url. Or we can return whatever we want.

        page = self.Page.format(**values)  # string.format(**dict) to map values into Page
        return page

    # Send the created page.
    def send_page(self, page):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    serverAddress = ('', 8080)
    server = BaseHTTPServer.HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()
