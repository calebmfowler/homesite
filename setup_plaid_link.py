from homesite.finance.utils import Plaid

from flask import Flask, request, render_template_string
from threading import Thread
import time
import webbrowser

plaid = Plaid("Production") # Select from "Production", "Sandbox"

link_type = ["transactions"] # Select from ["investments", "liabilities", "transactions"]

temp_link_token_response = plaid.get_link_token(link_type)

app = Flask(__name__)

html_template = f"""
<!DOCTYPE html>
<html>
  <head>
    <title>Plaid Link Auto</title>
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
  </head>
  <body>
    <pre id="output"></pre>
    <script>
      var handler = Plaid.create({{
        token: "{temp_link_token_response["link_token"]}",
        onSuccess: function(public_token, metadata) {{
          var public_token_response = {{public_token: public_token, metadata: metadata}};
          console.log("Full response dictionary:", public_token_response);
          fetch('/callback', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(public_token_response)
          }});
        }},
        onExit: function(err, metadata) {{
          console.log("Exited:", err, metadata);
        }}
      }});
      window.onload = function() {{
        handler.open();
      }};
    </script>
  </body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(html_template)

public_token_response = None
@app.route("/callback", methods=["POST"])
def callback():
    global public_token_response
    public_token_response = request.json
    return {"status": "ok"}

def run_app():
    app.run(port=5000)

thread = Thread(target=run_app)
thread.start()

webbrowser.open("http://localhost:5000")

while not public_token_response:
    time.sleep(1)

access_token_response = plaid.get_access_token(public_token_response["public_token"])

print(access_token_response)
