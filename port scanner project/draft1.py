from flask import Flask, request, Response,render_template
import socket #lets you work with IPs and ports
import concurrent.futures #used to scan many ports at the same time

app = Flask(__name__)#intiaziting the web app 

# Streamed scanner function
def generate_output(domain):
    try:
        ip = socket.gethostbyname(domain)
        yield f"<p>Scanning {domain} ({ip})...</p>"

        ports = range(1, 1025)  # Use smaller range for demo; change to 65536 for full scan

        def scan(port):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                result = s.connect_ex((ip, port))
                s.close()

                try:
                    service = socket.getservbyport(port, 'tcp')
                except:
                    service = 'unknown'

                status = "open" if result == 0 else "closed"
                return f"<p class='{status}'>Port {port} [{service}] is {status}</p>"
            except Exception as e:
                return f"<p>Error on port {port}: {str(e)}</p>"


        #this is a module that helps to perform the network scanning using the cocurrent.futures module that he
        #perfom the network scanning simultaneously
        with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor: # i created an instance of ThreadPoolExecutor
            #A ThreadPoolExecutor is a high-level interface for asynchronously executing callables (like functions) using a pool of threads.
           #the max_workers attribute is used to specify how many parts is going to be scanned at once e.g 200 ports a once
           #the with word is used to start the operation without it the "shutdown(wait=true)" function is activated which means thatit would wait until all the tasks are completed then clean the thread
            futures = [executor.submit(scan, port) for port in ports]# this is a dictionary comprehension The goal here is to create a dictionary named futures that will store information about the tasks being submitted to the thread pool.
            # executor.submit is the method used to schedule a callable to be executed by one of the threads in the pool., the argument scan scans for ne port at a time
            #for ports in ports acts an iterator 
            for future in concurrent.futures.as_completed(futures):
                yield future.result()

        yield "<p>Scan complete ✅</p>"

    except socket.gaierror:#error raised when the domain is not found or there is a network issue
        yield f"<p style='color:red'>Error: Domain not found or network issue ({domain}). Please check the name and try again.</p>"
    
    except Exception as e:
        yield f"<p style='color:red'>Error: {str(e)}</p>"

# Route for web form + output
@app.route('/', methods=['GET', 'POST'])
def index():
     # This part handles when the form is submitted
    if request.method == 'POST':
          # 1. Get the URL from the submitted form data.
          #'url' here must match the 'name' attribute of the input field in your HTML form.
        full_url = request.form.get('url') # i am using .get() for safer access and to avoid KeyError
        if not full_url:
            return render_template('index.html', error="Please enter a website URL.")
          # 2. Extract the domain name from the full URL.
        #    - It removes 'https://' or 'http://' prefixes.
        #    - .split('/')[0] takes the part before the first slash (e.g., "www.example.com" from "www.example.com/some/path"
        domain = full_url.replace('https://', '').replace('http://', '').split('/')[0].strip() # i m using strip() to remove any leading or trailing whitespace
        
        if not domain:
            return render_template('index.html', error="Invalid URL or could not extract domain.")
         # It's good practice to wrap the streaming response in a basic HTML structure
        # if the generate_output doesn't produce full HTML boilerplate.
        def stream_with_layout(domain_to_scan):
            yield '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Scan Results</title>'
             #i can also link the same css from the  index.html file or i can embed the css in the html file
            yield '<link rel="stylesheet" href="../static/styles.css">' # Assuming you move styles to a static file
            yield '</head><body><div class="output-container"><h1>Scan results</h1>'
            for chunk in generate_output(domain_to_scan):
                yield chunk
            yield '</div></body></html>'

        return Response(stream_with_layout(domain), mimetype='text/html')
        
    # This part handles when the form is accessed via GET request
    # 1. If the request method is GET, it means the user is accessing the page to fill out the form.
    # 2. Render the form from templates/index.html.
    #    - This will display the HTML form for the user to input a URL.
    #    - The form should have an input field with the name 'url' to match the code above.
    # For GET requests, render the form from templates/index.html
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)



    #  # 3. Return a streaming response that generates the output of the port scan.
    #     #    - The generate_output function is called with the extracted domain.
    #     #    - The mimetype is set to 'text/html' to indicate that the response will be HTML content.
    #     #    - This allows the browser to render the output as a web page.
    #     return Response(generate_output(domain), mimetype='text/html')

    # return """
    # <!doctype html>
    # <title>Web Port Scanner</title>
    # <h2>Scan a Website's Ports</h2>
    # <form method="post">
    #   <input name="url" placeholder="Enter website (e.g. google.com)" size="40">
    #   <input type="submit" value="Scan">
    # </form>
    # """