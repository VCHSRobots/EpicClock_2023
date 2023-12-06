import socket
import struct
import network
import machine
import sys
import time
import pw

wlan = None

wifi_table = [
    (b"BBHWifiLink", pw.Brandon),
    (b"BrandonWiFi_Attic", pw.Brandon),
    (b"BrandonWiFi_Attic_24", pw.Brandon),
    (b"BrandonGarage", pw.Brandon),
    (b"RobotsB17", pw.Epic),
    (b"RobotsB18", pw.Epic) ]

google_ntp = ('216.239.35.0', 123)

def init():
    ''' Initialize the network object. '''
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

def network_off():
    ''' Turn off network.  Must re-initalize after this.'''
    wlan.active(False)

def scan():
    ''' Scan the wifi environment, and return the strongest network that we recognize.
    Returned data is a 7-tuple: (ssid, bssid, chan, signal, ?, ?, pw)'''
    aps = wlan.scan()
    found = []
    for ap in aps:
        ssid, bssid, chan, signal, _, _ = ap
        for places in wifi_table:
            n, pw = places
            if n == ssid: found.append(ap + (pw,))
    n = len(found)
    if n <= 0: return None
    if n == 1: return found[0]
    best = found[0]
    for f in found:
        ssid, bssid, chan, signal, _, _, pw = f
        if signal > best[3]: best = f
    return best        
            
def is_connected():
    ''' Returns True if we have a wifi connection '''
    if wlan is None: return False
    return wlan.isconnected()

def start_connect(ssid, pw):
    ''' Starts the network trying to connect to the given access point. '''
    wlan.active(True)
    wlan.connect(ssid, pw)
    
def print_network_info():
    if not is_connected():
        print("Not connected to network.")
        return
    print("Connected. Network Info: ", wlan.ifconfig()) 
    
def connect(ssid, pw):
    ''' Trys to connect to an access point with information given. Blocks till connected.'''
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, pw)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        time.sleep(1)
    print(wlan.ifconfig())

def ntp(addr=google_ntp):
    REF_TIME_1970 = 2208988800  # Reference time
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(2.0)
    data = b'\x1b' + 47 * b'\0'
    try:
        client.sendto(data, addr)
        data, address = client.recvfrom(1024)
    except:
        client.close()
        return None        
    client.close()
    if data:
        t = struct.unpack('!12I', data)[10]
        t -= REF_TIME_1970
        return t
    return None

def off():
    t0 = ntp()
    delt = time.time() - t0
    return delt/3600.0

def get_time():
    t = ntp()
    x = time.localtime(t)
    return x

def setrtc():
    ''' Sets the RTC to UTC time '''
    t = ntp() 
    x = time.localtime(t)
    y = (x[0], x[1], x[2], x[6], x[3], x[4], x[5], x[7])
    rtc = machine.RTC()
    rtc.datetime(y)
    



