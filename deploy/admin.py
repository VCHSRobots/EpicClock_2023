# admin.py -- administration stuff
# dlb, Dec 2023

import machine
from machine import RTC
from machine import Timer
import main
import history as hist
import neo
import ntptime as ntp
import rtcmod as rtc
import timehelp as th
import timesync as sync
import time

def run():
    ''' Starts the clock running.'''
    main.run()
    
def get_time():
    return rtc.get_time()

def set_time(year, month, date, hours, minutes, seconds):
    ''' Sets the UTC time of the clock, in 24 hour format.'''
    t = (year, month, date, hours, minutes, seconds, 0, 0)
    rtc.set_time()
    
def wipe_eeprom(clock_id='default'):
    ''' Wipes the eeprom, and sets it up with the given clock id.'''
    hist.wipe_eeprom(clock_id)
    print("EEPROM wiped.")

def get_id():
    ''' Returns the clock id.''' 
    return hist.read_clock_id()
    
def dump_eeprom(adr0=0, n=2048):
    ''' Dumps eeprom to the terminal starting at adr, for n bytes.'''
    rtc.dump_eeprom(adr0, n)
    
def set0():
    ''' Syncs the time to NTP time.'''
    main.wait_for_network_time(must_connect = True)
    
def last_boot():
    ''' Returns the UTC time of last boot.'''
    tt = hist.get_last_power_cycle()
    if tt is None: print("Nothing in eeprom.")
    else:
        t = time.localtime(tt)
        return t
    
def last_time_check():
    ''' Returns the UTC time of the last time check.'''
    tt = hist.get_last_time_check()
    if tt is None: print("Nothing in eeprom.")
    else:
        t = time.localtime(tt)
        return t

def break_wifi():
    ''' Sets the flag to break wifi access'''
    ntp.break_wifi = True 
    
def break_ntp():
    ''' Sets the flag to break ntp access.'''
    ntp.break_ntp = True
    
def break_scan():
    ''' Sets the flag to break wifi scanner.'''
    ntp.break_scan = True
    
def reset_debug():
    ntp.debug_off()
    
def list_power():
    hist.list_power()
    
def list_time_checks():
    hist.list_time_checks()
    
    
    
    
    
    
    


