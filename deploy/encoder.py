from machine import Pin
import utime
from micropython import const

class EncoderResult:
    NO_CHANGE = const(0)
    UP = const(1)
    DOWN = const(2)

global encoder_value
# Define GPIO pins
CLK_PIN = 10  # GPIO pin number
DT_PIN = 11   # GPIO pin number
SW_PIN = 12   # GPIO pin number

# Setup GPIO pins
clk = Pin(CLK_PIN, Pin.IN, Pin.PULL_UP)
dt = Pin(DT_PIN, Pin.IN, Pin.PULL_UP)
sw = Pin(SW_PIN, Pin.IN, Pin.PULL_UP)

# Initialize variables
clk_state_prev = clk.value()
dt_state_prev = dt.value()
encoder_value = 0

def read_encoder():
    global clk_state_prev, dt_state_prev, encoder_value
    clk_state = clk.value()
    dt_state = dt.value()
    changed = False

    clk_state_prev = clk.value()
    dt_state_prev = dt.value()
    encoder_value = 0

def read_encoder():
    global clk_state_prev, dt_state_prev, encoder_value
    clk_state = clk.value()
    dt_state = dt.value()
    value = EncoderResult.NO_CHANGE
    if clk_state != clk_state_prev:
        # Encoder state changed
        if clk_state == 0:
            changed = True
            if dt_state == 0:
                encoder_value -= 1
                print(" ↓")
                value = EncoderResult.DOWN
            else:
                encoder_value += 1
                print("↑")
                value = EncoderResult.UP

    clk_state_prev = clk_state
    dt_state_prev = dt_state
    return value

    
def did_button_press():
    global encoder_value
    # Check if the switch (SW) pin is pressed
    if sw.value() == 0:
        encoder_value = 0
        print("Button Pressed")
        utime.sleep(.5) #sleep to debounce
        return True
    else: return False
        
def test_run():
    while True:
        read_encoder()
        did_button_press()
        utime.sleep(0.01)  # Adjust sleep time as needed
        
