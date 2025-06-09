from flask import Flask, request, Response, render_template # Ensure render_template is imported
import socket
import concurrent.futures

app = Flask(__name__) # intiaziting the web app 

# ... (your generate_output function remains the same) ...
def generate_output(domain):
    try:
        ip = socket.gethostbyname(domain)
        yield f"<p>Scanning {domain} ({ip})...</p>" #

        ports = range(1, 1025)  # Use smaller range for demo; change to 65536 for full scan

        def scan(port): # Renamed from scan_port for clarity with the submit call
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                result = s.connect_ex((ip, port))
                s.close()

                try:
                    service = socket.getservbyport(port, 'tcp') #
                except:
                    service = 'unknown' #

                status = "open" if result == 0 else "closed" #
                # Add classes for styling based on status
                return f"<p class='{status}'>Port {port} [{service}] is {status}</p>" #
            except Exception as e:
                return f"<p>Error on port {port}: {str(e)}</p>" #


        with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor: #
            futures = [executor.submit(scan, port) for port in ports] #
            for future in concurrent.futures.as_completed(futures):
                yield future.result() #

        yield "<p>Scan complete ✅</p>" #

    except socket.gaierror: # More specific error for domain not found
        yield f"<p style='color:red'>Error: Domain not found or network issue ({domain}). Please check the name and try again.</p>"
    except Exception as e:
        yield f"<p style='color:red'>Error: {str(e)}</p>" #

# Route for web form + output
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        full_url = request.form.get('url') # Use .get() for safer access and to avoid KeyError

        if not full_url:
            return render_template('index.html', error="Please enter a website URL.")

        domain = full_url.replace('https://', '').replace('http://', '').split('/')[0].strip() #

        if not domain:
            return render_template('index.html', error="Invalid URL or could not extract domain.")
        
        # It's good practice to wrap the streaming response in a basic HTML structure
        # if the generate_output doesn't produce full HTML boilerplate.
        def stream_with_layout(domain_to_scan):
            yield '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Scan Results</title>'
            # You can link the same CSS from index.html or embed styles
            yield '<link rel="stylesheet" href="/static/styles.css">' # Assuming you move styles to a static file
            # Or embed some basic styles directly for the results page
            yield '''
                <style>
                    body { font-family: 'Segoe UI', sans-serif; background-color: #f2f2f2; margin: 20px; color: #333; }
                    .output-container { max-width: 700px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
                    .open { color: green; }
                    .closed { color: red; }
                </style>
            '''
            yield '</head><body><div class="output-container"><h1>Scan Results</h1>'
            for chunk in generate_output(domain_to_scan):
                yield chunk
            yield '</div></body></html>'

        return Response(stream_with_layout(domain), mimetype='text/html')

    # For GET requests, render the form from templates/index.html
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)














#how it works now
# #GET Request: When you run draft1.py and go to http://127.0.0.1:5000/ in your browser, Flask will execute the else part of the index() function. render_template('index.html') will load your index.html file from the templates folder and display it.
# User Input: The user enters a website (e.g., google.com) into the form on index.html and clicks "Scan."
# POST Request: The browser sends a POST request to the same / URL.
# The if request.method == 'POST': block in draft1.py is executed.
# full_url = request.form.get('url') gets the entered URL.
# The domain is extracted.
# Response(stream_with_layout(domain), mimetype='text/html') is called.
# Streaming Results:
# The stream_with_layout function (which calls your generate_output function) starts yielding HTML content.
# Because it's a Response object with mimetype='text/html', the browser will replace the current page content (the form) with the new HTML being streamed from the server.
# You'll see "Scanning domain (ip)..." and then each port status as it's discovered.