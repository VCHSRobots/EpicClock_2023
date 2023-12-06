# EPIC Clock 

This project consists of building a rather large wall clock that reliably displays
the correct time in Southern California, be it PST or PDT.  The idea for this clock
is "install and forget".  The clock is intended to be installed in our Robot Labs,
so that we have an easy way to see the time, so that we don't forget to go home.  

The plan is to replace two old style battery clocks that never have the right time,
and constantly kill their batteries.  

The clock display is a grid of Neo Pixels (WS2812B Led) arranged in 32 columns and
8 rows.  The clock is driven by a Raspberry Pico W.  Time is kept by a DS3132 chip
with a CR2023 backup battery.  Therefore, if AC power is lost, time will continue
to be maintained, and the clock won't have to be reset.  The battery should last
many years if the clock mostly runs on AC.

The PICO W also has a wifi module.  If the PICO W can connect to the
interrnet, NTP time can be obtained, in which case the time should be accurate
to within one second.

The inital time (and updated time) can come from three sources:
the RTC backup, NTP, or manually via interaction with the code using Thorny.

The code for the PICO W is writen in micropython.

## Interesting Findings
Python time on the Pico W, under the micropython enviroment is kept
by using the machine.RTC module.  It is unclear if this module is
using the RP2040 chip's built-in RTC hardware.  However, it doesn't
really matter since this code doesn't depend on the RP2040's notion
of time.  But it is interesting to note that upon USB connection with
Thorny the machine.RTC module is synced to the time of the host (i.e., Windows)

## Time Algorithem
For display output, the DS3231 time value is used. If the year in the DS3231 is
less than 2010, then we assume that the DS3231 does not know the time -- and an
error condition is shown on the display.  Time updates (synchronizations) are
attemped at startup if the time is found to be invalid, and once every night at
about 2 am.  If a valid NTP time is obtained, then the DS3132 is updated to
match NTP time.  The time that the DS3231 is updated is recorded in EEPROM.

## Stale Time
If the clock runs for more than about a month without being updated and/or checked by
wifi/NTP, then the time is decleared to be stale.  A stale time is indicated by blue
colon between the hour and minute digits.  Normally the colon is red.

## Time Zone and Daylight Savings
This clock is programmed to show the pacific time zone.  It is also programmed
to automatically switch between daylight savings and standard time.  The algorithem
for switching depends on past and current government policy, so the code will need
to change if the rules regarding daylight savings changes.

## Wifi Access
This code is hardwired to check for a list of wifi access points to gain connection to
the internet.  Currently this list includes the Brandon's house, and the school's Robotic
rooms.

## Critical Times
One feature of this clock is that it can change the color of the clock digits at different
times of day, for different days of the week.  We call these critical times.  Currently the
critical times are from 8:50pm till 9:05pm on Monday through Thursday -- since these are the
times the robot team needs to cleanup and leave the lab.  There is also a crital time near
3am, since this is the time the buiding alarm automatically arms itself.

## History
A record is kept for each power up cycle, and each time the RTC is updated with NTP Time.
There are 64 records for each activity, on a rollover buffer in EEPROM.  This data can
be accessed manually by interacting with the code using Thorny.
