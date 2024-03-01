# timesync.py -- attempts to sync time with ntp
# dlb, Dec 2023

import time
import rtcmod as rtc
import ntptime as ntp
import history as hist
import log

SYNC_OFF     = 0
SYNC_SCAN    = 1
SYNC_CONNECT = 2
SYNC_NTP     = 3

sync_mode = 0
last_try = None   # Unix time of last sync try.
tmark = 0 

def sync_time(tnow, override=False):
    ''' Called about every 0.5 sec.  At around 1:00 am every day tries to obtain NTP time.'''
    global sync_mode, last_try, tmark
    year, month, day, hour, minute, second, dow, doy = time.localtime(tnow)
    if sync_mode == SYNC_OFF:
        if not override:
            if hour != 9: return   # Must be 1:00 or 2:00 am (depending on daylight savings)
        if last_try is None: doit = True
        elif tnow - last_try > 16 * 3600: doit = True
        else: doit = False
        if not doit: return
        last_try = tnow
        ntp.init()
        sync_mode = SYNC_SCAN
        print("Entering scan mode for getting NTP time.")
        return
    if sync_mode == SYNC_SCAN:
        access_point = ntp.scan()
        if access_point is None:
            print("Scan Fail.")
            if time.time() - last_try > 60:
                print("Aborting.")
                ntp.network_off()
                sync_mode = SYNC_OFF
            return
        ssid, bssid, chan, signal, _, _, pw = access_point
        print("Found wifi access point. Name=%s, Chan=%d, signal=%d, pw=%s" % (ssid, chan, signal, pw))
        sync_mode = SYNC_CONNECT
        ntp.start_connect(ssid, pw)
        tmark = time.time()
        return
    if sync_mode == SYNC_CONNECT:
        if ntp.is_connected():
            ntp.print_network_info()
            sync_mode = SYNC_NTP
            tmark = time.time()
        elif time.time() - tmark > 60.0:
            print("Connect fail. Aborting.")
            ntp.network_off()
            sync_mode = SYNC_OFF
        return
    if sync_mode == SYNC_NTP:
        t = ntp.ntp()
        if t is None:
            if time.time() - tmark > 60.0:
                print("NTP fail. Aborting.")
                ntp.network_off()
                sync_mode = SYNC_OFF
            return
        str_tme = str(time.localtime(t))
        print("Setting Clock to UTC Time: %s" % str_tme)
        rtc.set_time(time.localtime(t))
        hist.time_check(t)
        ntp.network_off()
        sync_mode = SYNC_OFF
        return
        
    
def test_sync():
    global sync_mode, last_try, tmark
    tnow = time.time()
    for i in range(100):
        sync_time(tnow, True)
        print("Sync Mode=", sync_mode)
        time.sleep(1)
        if sync_mode == SYNC_OFF: break
    return

def sync_new(tnow, override=False):
    global last_try
    year, month, day, hour, minute, second, dow, doy = time.localtime(tnow)
    
    if hour != 9: return   # Must be 1:00 or 2:00 am (depending on daylight savings)
    if last_try is None: doit = True	
    elif tnow - last_try > 16 * 3600: doit = True #if it's in the 9 oclock hour and it's been 16 hours sense trying then 
    else: doit = False
    if not doit: return  #returns if it's not time to sync
    
    
    if not ntp.is_connected(): #should still be connected.
        print("NTP not connected... cannot sync time")
        log.log("Time could not sync via NTP. NTP is not connected.") 
        return
    
    t = ntp.ntp()
    if t is None:
        log.log("Time could not sync via NTP. NTP was connected but time came back as None") 
        return
    rtc.set_time(time.localtime(t))
    hist.time_check(t)
    str_tme = "Synced Time via NTP. Time set: " + str(time.localtime(t))
    last_try = t
    print(str_tme)
    log.log(str_tme)
    
        
    
    
    
