import time
import usocket as socket
import network
import select
import encoder
import history
import ujson
import machine
import ure
import gc
import log
import rtcmod as rtc

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])

def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def connect_wifi(ssid, password, max_attempts=10, retry_interval=.1):
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    for attempt in range(max_attempts):
        if wlan.isconnected():
            print("Already connected to WiFi")
            return True

        print(f"Attempting to connect to WiFi (Attempt {attempt + 1}/{max_attempts})...")
        wlan.connect(ssid, password)

        time.sleep(retry_interval)

        if wlan.isconnected():
            print("Connected to WiFi")
            return True

    print(f"Failed to connect to WiFi after {max_attempts} attempts")
    return False


def start_server_loop(get_clock_values, update_colors, play_rainbow, send_message, on_loop, seconds_style):
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reusing the address
    s.bind(addr)
    s.listen(5)
    print('Listening on', addr)
    time_string = "--:--"

    s.setblocking(False)
    
    while True:
        time.sleep(0.01)
        
        on_loop() #calls main's on_loop each time we loop to check for things like the rotary encoder
        
        readable, _, _ = select.select([s], [], [], .01)

        if not readable: continue ## no connection so loop again otherwise we deal with the connection
        
        conn, addr = s.accept()
        print('Got a connection from', addr)

        conn.setblocking(True)

        try:
            request = conn.recv(1024)
        except OSError as e:
            if e.args[0] == errno.EAGAIN or e.args[0] == errno.EWOULDBLOCK:
                print("No data to read.")
            else:
                print(f"Error: {e}")
        finally:
            conn.setblocking(False)
            
        digit_color, colon_color, seconds_color, ampm_color, brightness, time_string, time_object = get_clock_values()
        
        current_values = {
            "digit_color": digit_color,
            "colon_color": colon_color,
            "seconds_color": seconds_color,
            "ampm_color": ampm_color,
            "brightness": str(brightness),
        }
#         print("raw request: ", request)
        if b"GET / " in request:
            handle_index(conn)
        elif b"GET /favicon.ico" in request:
            handle_favicon(conn)
        elif b"GET /styles.css" in request:
            handle_css(conn)
        elif b"GET /scripts.js" in request:
            handle_script(conn)
        elif b"POST /submit" in request:
            handle_submit(request, current_values, update_colors, time_object, conn)
        elif b"POST /refresh_time" in request:
            handle_refresh_time(request, current_values, time_object, conn)
        elif b"POST /play_rainbow" in request:
            handle_play_rainbow(conn, play_rainbow)
        elif b"POST /seconds_style" in request:
            handle_seconds_style(conn, seconds_style)
        elif b"POST /get_time_check_records" in request:
            handle_get_time_check_records(conn)
        elif b"POST /get_power_records" in request:
            handle_get_power_records(conn)
        elif b"POST /get_error_log" in request:
            handle_get_error_log(conn)
        elif b"POST /send_message" in request:
            handle_send_message(request, send_message, conn)
        elif b"POST /get_device_info" in request:
            handle_get_device_info(conn, wlan)
        
def send_data(conn, data):
    while data:
        try:
            gc.collect()
            written = conn.write(data)
            gc.collect()
            data = data[written:]
            gc.collect()
            
            if not data:
                print("Entire data sent.")
                break
        except OSError as e:
            print(f"Error: {e}")
            break
        
def handle_index(conn):
    try:
        print("send html")
        with open("web/index.html", "rb") as f:  # Adjust the path to your CSS file
            html_data = f.read()
            
        send_data(conn, b'HTTP/1.1 200 OK\nContent-Type: Content-Type: text/html; charset=utf-8\n\n')
        send_data(conn, html_data)
        conn.close()
    except OSError as e:
        print(f"Error while serving CSS file: {e}")
        send_data(conn, b'HTTP/1.1 404 Not Found\n\n')  
    finally:
        conn.close()
        
def handle_favicon(conn):
    try:
        with open("web/favicon.png", "rb") as f:
            favicon_data = f.read()
            
        send_data(conn, b'HTTP/1.1 200 OK\nContent-Type: image/x-icon\n\n')
        send_data(conn, favicon_data)
        conn.close()
    except OSError as e:
        print(f"Error while serving favicon: {e}")
        send_data(conn, b'HTTP/1.1 404 Not Found\n\n')  
    finally:
        conn.close()
        
def handle_css(conn):
    try:
        with open("web/styles.css", "rb") as f:  # Adjust the path to your CSS file
            css_data = f.read()
            
        send_data(conn, b'HTTP/1.1 200 OK\nContent-Type: text/css\n\n')
        send_data(conn, css_data)
        conn.close()
    except OSError as e:
        print(f"Error while serving CSS file: {e}")
        send_data(conn, b'HTTP/1.1 404 Not Found\n\n')  
    finally:
        conn.close()
        
def handle_script(conn):
    try:
        with open("web/scripts.js", "rb") as f:  # Adjust the path to your JavaScript file
            script_data = f.read()
            
        send_data(conn, b'HTTP/1.1 200 OK\nContent-Type: text/javascript\n\n')
        send_data(conn, script_data)
        conn.close()
    except OSError as e:
        print(f"Error while serving JavaScript file: {e}")
        send_data(conn, b'HTTP/1.1 404 Not Found\n\n')  
    finally:
        conn.close()
    
def handle_submit(request, current_values, update_colors, time_object, conn):
    path = request.split(b'\r\n')[0].split(b' ')[1].decode('utf-8')
    query_string = path[len("/submit?"):]
    params = query_string.split('&')
    
    data_dict = {}
    
    for param in params:
        key, value = param.split('=')
        if key != "brightness":
            value = hex_to_rgb(value)
        data_dict[key] = value

    current_values.update(data_dict)
    update_colors(current_values)

    response_data = {
        "digit_color": rgb_to_hex(current_values["digit_color"]),
        "colon_color": rgb_to_hex(current_values["colon_color"]),
        "seconds_color": rgb_to_hex(current_values["seconds_color"]),
        "ampm_color": rgb_to_hex(current_values["ampm_color"]),
        "brightness": current_values["brightness"],
        "h": time_object[0],
        "m": time_object[1],
        "s": time_object[2],
        "am": time_object[3]
    }

    json_response = ujson.dumps(response_data)
    send_data(conn, b'HTTP/1.1 200 OK\n')
    send_data(conn, b'Content-Type: application/json\n\n')
    send_data(conn, json_response.encode('utf-8'))
    conn.close()

def handle_refresh_time(request, current_values, time_object, conn):
    response_data = {
        "digit_color": rgb_to_hex(current_values["digit_color"]),
        "colon_color": rgb_to_hex(current_values["colon_color"]),
        "seconds_color": rgb_to_hex(current_values["seconds_color"]),
        "ampm_color": rgb_to_hex(current_values["ampm_color"]),
        "brightness": current_values["brightness"],
        "h": time_object[0],
        "m": time_object[1],
        "s": time_object[2],
        "am": time_object[3]
    }
    json_response = ujson.dumps(response_data)
    
    send_data(conn, b'HTTP/1.1 200 OK\n')
    send_data(conn, b'Content-Type: application/json\n\n')
    send_data(conn, json_response.encode('utf-8'))
    conn.close()

def handle_play_rainbow(conn, play_rainbow):
    play_rainbow()
    send_data(conn, b'HTTP/1.1 200 OK\n\n')
    conn.close()

def handle_seconds_style(conn, seconds_style):
    seconds_style()
    send_data(conn, b'HTTP/1.1 200 OK\n\n')
    conn.close()

def handle_get_error_log(conn):
    log_generator = log.read_log()
    send_data(conn, b'HTTP/1.1 200 OK\n\n')
    for chunk in log_generator:
        send_data(conn, chunk)
    conn.close()
    
def handle_get_time_check_records(conn):
    time_records = history.list_time_checks()
    print("time_records: ", time_records)
    send_data(conn, b'HTTP/1.1 200 OK\n\n')
    send_data(conn, time_records.encode('utf-8'))
    conn.close()

def handle_get_power_records(conn):
    power_records = history.list_power()
    print("power records: ", power_records)
    send_data(conn, b'HTTP/1.1 200 OK\n\n')
    send_data(conn, power_records.encode('utf-8'))
    conn.close()

def handle_send_message(request, send_message, conn):
    path = request.split(b'\r\n')[0].split(b' ')[1].decode('utf-8')
    query_string = path[len("/send_message?"):]
    decoded_query_string = ure.sub('%[0-9a-fA-F][0-9a-fA-F]', lambda m: chr(int(m.group(0)[1:], 16)), query_string)
    params = decoded_query_string.split('&')

    message = "   "
    color = (255, 0, 0)
    isLargeText = True
    for param in params:
        key, value = param.split('=')
        if key == "message":
            message += value
        elif key == "message_color":
            color = hex_to_rgb(value)
        elif key == "text_size":
            isLargeText = (value.lower() == "large")
    
    send_message(message, color, isLargeText)
    send_data(conn, b'HTTP/1.1 200 OK\n\n')
    conn.close()

def handle_get_device_info(conn, wlan):
    temperature = machine.ADC(4).read_u16() * (3.3 / 65535.0 * 100)
    led = machine.Pin(25, machine.Pin.OUT)

    wifi_info = {
        "SSID": wlan.config("essid"),
        "IP Address": wlan.ifconfig()[0],
        "Subnet Mask": wlan.ifconfig()[1],
        "Gateway": wlan.ifconfig()[2],
        "DNS Server": wlan.ifconfig()[3],
        "Signal Strength (RSSI)": wlan.status("rssi")
    }

    response_text = f"Temperature: {temperature:.2f} °C\r\n"
    response_text += f"LED Status: {'On' if led.value() else 'Off'}\r\n"

    response_text += "Wi-Fi Information:\r\n"
    for key, value in wifi_info.items():
        response_text += f"  {key}: {value}\r\n"

    signal_strength_category = classify_signal_strength(wifi_info["Signal Strength (RSSI)"])
    response_text += f"  Signal Strength Category: {signal_strength_category}\r\n"
    
    response_text += "\r\nMemory Dump:\r\n" + rtc.dump_eeprom(0, 2048)

    print("get device info: ", response_text)
    
    send_data(conn, b'HTTP/1.1 200 OK\n\n')
    send_data(conn, response_text.encode('utf-8'))
    conn.close()



def classify_signal_strength(rssi):
    if rssi >= -50:
        return "Excellent (High)"
    elif -50 > rssi >= -70:
        return "Good (Medium)"
    elif -70 > rssi >= -80:
        return "Fair (Low)"
    elif -80 > rssi:
        return "Poor (None)"
    else:
        return "Unknown"
