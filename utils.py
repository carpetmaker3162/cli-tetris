import os

def _unix_getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def _win_getch():
    return msvcrt.getch()

if os.name == "nt":
    import msvcrt
    getch = _win_getch
else:
    import sys, tty, termios
    getch = _unix_getch

class Fmt:
    end = '\033[0m'

    bold_text = '\033[1m'
    light_text = '\033[2m'
    italic_text = '\033[3m'
    underline_text = '\033[4m'
    blinking_text = '\033[5m'
    inverted_color_text = '\033[7m'
    invisible_text = '\033[8m'
    
    dark_red_text = '\033[31m'
    dark_green_text = '\033[32m'
    dark_yellow_text = '\033[33m'
    dark_blue_text = '\033[34m'
    dark_magenta_text = '\033[35m'
    aqua_text = '\033[36m'
    light_gray_text = '\033[37m'

    black_highlight_text = '\033[40m'
    dark_red_highlight_text = '\033[41m'
    dark_green_highlight_text = '\033[42m'
    dark_yellow_highlight_text = '\033[43m'
    dark_blue_highlight_text = '\033[44m'
    dark_magenta_highlight_text = '\033[45m'
    aqua_highlight_text = '\033[46m'
    gray_highlight_text = '\033[47m'

    gray_text = '\033[90m'
    red_text = '\033[91m'
    green_text = '\033[92m'
    yellow_text = '\033[93m'
    blue_text = '\033[94m'
    magenta_text = '\033[95m'
    cyan_text = '\033[96m'
    white_text = '\033[97m'

    gray_highlight_text = '\033[100m'
    red_highlight_text = '\033[101m'
    green_highlight_text = '\033[102m'
    yellow_highlight_text = '\033[103m'
    blue_highlight_text = '\033[104m'
    magenta_highlight_text = '\033[105m'
    cyan_highlight_text = '\033[106m'
    light_gray_highlight_text = '\033[107m'