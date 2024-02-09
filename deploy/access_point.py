import network
import usocket as socket
import select
import time
import machine
import neo
import history
import clock_server

html_head = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 20px; }
        h2 { color: #333; text-align: center; }
        form { max-width: 400px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
        label { display: block; margin-bottom: 8px; font-weight: bold; color: #555; }
        select, input[type="text"], input[type="password"] { width: 100%; padding: 8px; margin-bottom: 16px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; display: inline-block; vertical-align: middle; }
        #password-container { display: flex; align-items: center; }
        .password-input { width: calc(100% - 130px); margin-right: 8px; }
        .show-password-btn { margin-top:-15px; padding: 10px; border: none; border-radius: 4px; cursor: pointer; box-sizing: border-box; background-color: #008CBA; color: #fff; display: inline-block; vertical-align: middle; }
        input[type="submit"] { width: 100%; padding: 10px; border: none; border-radius: 4px; cursor: pointer; display: inline-block; box-sizing: border-box; background-color: #4caf50; color: #fff; margin-top: 10px; }
        input[type="submit"]:hover { background-color: #45a049; }
        .toast { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background-color: #4caf50; color: white; padding: 16px; border-radius: 5px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); }
        .toast.success { background-color: #4caf50; }
        .toast.error { background-color: #f44336; }
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(25, 25, 25, 0.5); display: flex; justify-content: center; align-items: center; }
        .overlay::before { content: ""; border: 4px solid rgba(0, 0, 0, 0.1); border-top: 4px solid #3498db; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .success-box { max-width: 400px; display: none; text-align: center; margin: 20px auto; padding: 20px; background-color: #fff; color:#333; border-radius: 5px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); }
        .success-box h3 { font-size: 1.5em; margin-bottom: 10px; }
        .success-box button { background-color: #e74c3c; color: white; padding: 10px; border: none; border-radius: 4px; cursor: pointer; }
        .success-box button:hover { background-color: #c0392b; }
    </style>
    <script>
        function togglePassword() {
            var passwordField = document.getElementById("password");
            passwordField.type = (passwordField.type === "password") ? "text" : "password";
        }
        function showSuccessBox() {
            var successBox = document.getElementById("success-box");
            successBox.style.display = "block";
        }
        function reboot() {
            showLoading(true);
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/reboot", true);

            xhr.onreadystatechange = function () {
                if (xhr.readyState == 4 && xhr.status == 200) {
                    createToast("Rebooting...", false, false);
                }
            };

            xhr.send();
        }
        function showLoading(onOff) {
            var body = document.body;

            if (onOff) {
                overlay = document.createElement("div");
                overlay.className = "overlay";
                body.appendChild(overlay);
            } else {
                body.removeChild(overlay);
            }
        }
        function submitForm() {
            showLoading(true);

            var ssidSelect = document.getElementById("ssidSelect");
            var ssid = ssidSelect.value;

            if (ssid === "manual") {
                // If manual entry, get the value from the manualSSID input
                ssid = document.getElementById("manualSSID").value;
            }

            var password = document.getElementById("password").value;

            var xhr = new XMLHttpRequest();
            var queryParams = "ssid=" + ssid + "&password=" + password;

            xhr.open("POST", "/submit?" + queryParams, true);
            xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

            xhr.onreadystatechange = function () {
                if (xhr.readyState == 4) {
                    if (xhr.status == 200) {
                        createToast("Success!", true);
                        showSuccessBox();
                    } else {
                        createToast("Problem!", false);
                    }
                }
            };

            xhr.send();

            return false;
        }

        function createToast(message, success = true, turnOff = true) {
            const toast = document.createElement('div');
            toast.classList.add('toast');
            toast.textContent = message;

            document.body.appendChild(toast);

            // Add additional class based on success or failure
            if (success) {
                toast.classList.add('success');
            } else {
                toast.classList.add('error');
            }
            if(turnOff){
                setTimeout(() => {
                    toast.remove();
                    showLoading(false);
                }, 1500);
            }
        }
        function toggleManualSSID() {
            var ssidSelect = document.getElementById("ssidSelect");
            var manualSSIDContainer = document.getElementById("manualSSIDContainer");
            var manualSSIDInput = document.getElementById("manualSSID");

            if (ssidSelect.value === "manual") {
                manualSSIDContainer.style.display = "block";
                manualSSIDInput.required = true;
            } else {
                manualSSIDContainer.style.display = "none";
                manualSSIDInput.required = false;
            }
        }
    </script>
</head>
"""

html_body = """
    <body>
        <h2>Clock WiFi Configuration</h2>
        <form onsubmit="return submitForm()">
            <label for="ssidSelect">Select or Enter SSID:</label>
            <select name="ssid" id="ssidSelect" onchange="toggleManualSSID()">
                {{options}}
                <option value="manual">Manual Entry</option>
            </select><br>
            <div id="manualSSIDContainer" style="display: none;">
                <label for="manualSSID">Manual SSID:</label>
                <input type="text" name="manual_ssid" id="manualSSID">
            </div>
            <label for="password">Password:</label>
            <div id="password-container">
                <input class="password-input" type="password" name="password" id="password" required>
                <button type="button" class="show-password-btn" onclick="togglePassword()">Show Password</button>
            </div><br>
            <input type="submit" value="Submit">
        </form>
        <div id="success-box" class="success-box">
            <h3>WiFi credentials saved. Click here to reboot your clock and have it attempt to connect.</h3>
            <button onclick="reboot()">Reboot and Connect</button>
        </div>
    </body>
</html>
"""
scroll_text = ""
def run(on_loop):
    global scroll_text
    # Set up the access point
    ap_ssid = "Clock"
    ap_password = "12345678"
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ap_ssid, password=ap_password)

    ap.active(True)
    
    while ap.active() == False:
        pass
    
    print("Access point active")
    print(ap.ifconfig())
    print("Current AP SSID:", ap.config('essid'))
    
    scroll_text = "WIFI: "+ ap_ssid + " Password: " + ap_password + " Go to: " + ap.ifconfig()[0]       
    neo.init_infinite_scroll(scroll_text, (35,0,2))
    

    # Create a socket and bind to a port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.SO_REUSEADDR)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reusing the address
   
    
    s.bind(('', 80))
    s.listen(3)
    s.setblocking(False)
    
    while True:
        on_loop()
        time.sleep(.01)
        readable, _, _ = select.select([s], [], [], .01)

        if readable:
            conn, addr = s.accept()
            print('Got a connection from', addr)
            conn.settimeout(2)
            conn.setblocking(True)
            try:
                request = conn.recv(1024)

                # Check if the received data is empty
                if not request:
                    print("No data received.")
                    conn.close()
                    continue

                #print("Received data from connection.")
                #print("request: ", request)

                
            except OSError as e:
                print(f"Error: {e}")
                conn.setblocking(False)
                conn.close()
                continue
            finally:
                conn.setblocking(False)
        

            # Print the received data for debugging
            print(f"\r\nFull request:", request)
            
            if "GET /favicon.ico" in request:
                response = b'HTTP/1.1 200 OK\n\n'
                conn.write(response)
                conn.close()
                continue  # Skip the rest of the loop for favicon requests
            
            if b"POST /submit" in request:
                # Extract SSID and password from the received data
                ssid_start = request.find(b'ssid=') + len(b'ssid=')
                ssid_end = request.find(b'&', ssid_start)
                ssid = request[ssid_start:ssid_end]

                password_start = request.find(b'&password=') + len(b'&password=')
                password_end = request.find(b'HTTP/1.1', password_start)
                password = request[password_start:password_end-1]

                # Print the extracted data for debugging
                print("\r\n\r\nExtracted SSID: ", ssid)
                print(f"Extracted Password:", password)
                print ("\r\n\r\n")
                history.write_wifi(ssid, password)
                connected = clock_server.connect_wifi(str(ssid), str(password))
                
                response = b'HTTP/1.1 200 OK\n\n' + bytes("connected: " + str(connected), 'utf-8')
                conn.sendall(response)
                conn.close()
                continue
            if b"POST /reboot" in request:
                response = b'HTTP/1.1 200 OK\n\n'
                conn.sendall(response)
                conn.close()
                time.sleep(4)
                machine.reset()
                continue
                

            
            # Scan for available WiFi networks
            wifi_scan_results = ap.scan()
            wifi_options = ''.join(['<option value="{}">{}</option>'.format(result[0].decode('utf-8'), result[0].decode('utf-8')) for result in wifi_scan_results])

            # Replace {{options}} with the generated options in the HTML body
            html_body_with_options = html_body.replace("{{options}}", wifi_options)
            response = b'HTTP/1.1 200 OK\n\n' + html_head + html_body_with_options
            response_length = len(response)
            
            while response:
                try:
                    # Write as much as possible to the socket
                    written = conn.write(response)
                    response = response[written:]
                    #print("updated response:" + str(response))

                    # Check if the entire response is sent
                    if not response:
                        print(f"Entire response sent. Length: {response_length}")
                        break
                except OSError as e:
                    print(f"Error: {e}")
                    break
            conn.close()
            print("Connection closed")
    
def scroll_text():
    neo.infinite_scroll_on_loop()