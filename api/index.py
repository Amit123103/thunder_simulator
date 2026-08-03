from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cinematic Lightning Terrain Simulator API</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b0f19; color: #f3f4f6; text-align: center; padding: 60px 20px; }
                h1 { color: #a855f7; font-size: 2.5rem; }
                p { color: #9ca3af; font-size: 1.2rem; }
                a { color: #38bdf8; text-decoration: none; font-weight: 600; }
                .code { background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 8px; font-family: monospace; display: inline-block; text-align: left; margin-top: 20px; color: #79c0ff; }
            </style>
        </head>
        <body>
            <h1>⚡ Cinematic Lightning Terrain Simulator</h1>
            <p>3D ModernGL & OpenGL Real-Time Engine</p>
            <div class="code">
                # Clone and Run Locally on Desktop:<br>
                git clone https://github.com/Amit123103/thunder_simulator.git<br>
                python main.py
            </div>
            <p style="margin-top: 30px;"><a href="https://github.com/Amit123103/thunder_simulator" target="_blank">View GitHub Repository →</a></p>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
        return
