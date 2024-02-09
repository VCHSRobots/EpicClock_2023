# next_color.py -- used to smothly transitions colors in
# a gradiant across a rainbow.

# It transitions colors from Red, to Yellow, to Green,
# to Teal, To Blue, To Purple and then back to red.

# The main method next color takes a color, a transition
# state, transition speed, and a direction to find
# the next color in the gradiant 


class ColorStates:
    """Enum of transitional States to Move Colors through the Rainbow"""
    TO_RED = 0
    TO_YELLOW = 1
    TO_GREEN = 2
    TO_TEAL = 3
    TO_BLUE = 4
    TO_PURPLE = 5
    BACK_TO_RED = 6
    
class ColorDirection:
    UP = 1
    DOWN = -1

RGB_MIN = 0
RGB_MAX = 255

def next_color(r, g, b, state, speed, color_direction=ColorDirection.UP):
    """given an r, g, b, color, the state and speed it returns the next color and state"""
    speed *= color_direction
    if state == ColorStates.TO_RED:
        g = 0
        if r >= RGB_MAX:
            state = ColorStates.TO_YELLOW
        else:
            r += speed
            
        if r < RGB_MIN:
            state = ColorStates.TO_PURPLE

    if state == ColorStates.TO_YELLOW:
        r = RGB_MAX
        b = RGB_MIN
        if g >= RGB_MAX:
            state = ColorStates.TO_GREEN
        else:
            g += speed
            
        if g < RGB_MIN:
            state = ColorStates.BACK_TO_RED
            b = RGB_MIN+1

    if state == ColorStates.TO_GREEN:
        g = RGB_MAX
        b = RGB_MIN
        if r <= RGB_MIN:
            state = ColorStates.TO_TEAL
        else:
            r -= speed
        
        if r > RGB_MAX:
            state = ColorStates.TO_YELLOW
            g = RGB_MAX -1

    if state == ColorStates.TO_TEAL:
        g = RGB_MAX
        if b >= RGB_MAX:
            state = ColorStates.TO_BLUE
        else:
            b += speed
        if b<RGB_MIN:
            state = ColorStates.TO_GREEN
            r = RGB_MIN+1

    if state == ColorStates.TO_BLUE:
        b = RGB_MAX
        r = RGB_MIN
        if g <= RGB_MIN:
            state = ColorStates.TO_PURPLE
        else:
            g -= speed
        if g>RGB_MAX:
            state = ColorStates.TO_TEAL
            b = RGB_MAX -1

    if state == ColorStates.TO_PURPLE:
        b = RGB_MAX
        g = RGB_MIN
        if r >= RGB_MAX:
            state = ColorStates.BACK_TO_RED
        else:
            r += speed
        if r< RGB_MIN:
            state = ColorStates.TO_BLUE
            g = RGB_MIN+1

    if state == ColorStates.BACK_TO_RED:
        r = RGB_MAX
        g = RGB_MIN
        if b <= RGB_MIN:
            state = ColorStates.TO_YELLOW
        else:
            b -= speed
        if b > RGB_MAX:
            state = ColorStates.TO_PURPLE
            r = RGB_MAX-1

    r, g, b = ensure_rgb_range(r, g, b)

    return r, g, b, state


def ensure_rgb_range(r, g, b):
    r = max(RGB_MIN, min(r, RGB_MAX))
    g = max(RGB_MIN, min(g, RGB_MAX))
    b = max(RGB_MIN, min(b, RGB_MAX))
    return r, g, b
