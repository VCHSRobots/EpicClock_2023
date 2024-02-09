import socket
import struct
import network
import machine
import sys
import time

wlan = None

# no longer used
wifi_table = [ ]

google_ntp = ('216.239.35.0', 123)

break_scan = False
break_wifi = False
break_ntp  = False

def debug_off():
    global break_scan, break_wifi, break_ntp
    break_scan = False
    break_wifi = False
    break_ntp  = False

def init():
    ''' Initialize the network object. '''
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

def network_off():
    ''' Turn off network.  Must re-initalize after this.'''
    wlan.active(False)

# no longer used now that have find_ap
def scan():
    ''' Scan the wifi environment, and return the strongest network that we recognize.
    Returned data is a 7-tuple: (ssid, bssid, chan, signal, ?, ?, pw)'''
    if break_scan: return None
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

def find_ap(ssid_to_find):
    ''' Scan the wifi environment, and return the the matched wifi access point.
    Returned data is a 6-tuple: (ssid, bssid, chan, signal, ?, ?)'''
    ssid_to_find = bytes(ssid_to_find, 'utf-8')
    if break_scan: return None
    aps = wlan.scan()
    found = []
    for ap in aps:
        ssid, bssid, chan, signal, _, _ = ap
        if ssid_to_find == ssid: return ap
        #else: print("wrong wifi ", ssid)
    return None   
            
def is_connected():
    ''' Returns True if we have a wifi connection '''
    if wlan is None: return False
    return wlan.isconnected()

def start_connect(ssid, pw):
    ''' Starts the network trying to connect to the given access point. '''
    if break_wifi: return 
    wlan.active(True)
    wlan.connect(ssid, pw)
    
def print_network_info():
    if not is_connected():
        print("Not connected to network.")
        return
    print("Connected. Network Info: ", wlan.ifconfig())

def get_ip():
    if not is_connected():
        print("not connected to network")
        return "-1.-1.-1.-1"
    return wlan.ifconfig()[0]
    
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
    if break_ntp: return None
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
        unpacked = struct.unpack('!12I', data)
        t = unpacked[10] - REF_TIME_1970
        #frac_of_second = float(unpacked[11]) / 2**32
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
    
  

    



