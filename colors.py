#!/usr/bin/env python3


class Colors:

    def __init__(self):
        pass

    CYAN = '\033[96m'
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLACK = '\033[90m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    HTML_BG_DARK_RED = 'bgcolor="#F50000"'
    HTML_BG_ORANGE = 'bgcolor="#F55200"'
    HTML_BG_YELLOW = 'bgcolor="#F5F500"'
    HTML_BG_LIGHT_GREEN = 'bgcolor="#CCF500"'
    HTML_BG_GREEN_1 = 'bgcolor="#00E100"'
    HTML_BG_GREEN_2 = 'bgcolor="#00D700"'
    HTML_BG_DARK_GREEN = 'bgcolor="#00C300"'
    HTML_BG_PURPLE = 'bgcolor="#8811ff"'


def wrap_message_in_green(message): return Colors.GREEN + str(message) + Colors.END


def wrap_message_in_purple(message): return Colors.PURPLE + str(message) + Colors.END


def wrap_message_in_red(message): return Colors.RED + str(message) + Colors.END


def wrap_message_in_blue(message): return Colors.BLUE + str(message) + Colors.END


def wrap_message_in_yellow(message): return Colors.YELLOW + str(message) + Colors.END


def wrap_message_in_black(message): return Colors.BLACK + str(message) + Colors.END


def wrap_message_in_cyan(message): return Colors.CYAN + str(message) + Colors.END


def wrap_message_in_bold(message): return Colors.BOLD + str(message) + Colors.END


def wrap_message_in_bold_red(message): return Colors.BOLD + Colors.RED + str(message) + Colors.END


def wrap_message_in_bold_blue(message): return Colors.BOLD + Colors.BLUE + str(message) + Colors.END


def html_background_define(value):
    # Negative result #
    if float(value) < float(-9.99):
        return Colors.HTML_BG_DARK_RED

    elif float(-5.00) > float(value) > float(-9.99):
        return Colors.HTML_BG_ORANGE

    elif float(-5.00) < float(value) < 0:
        return Colors.HTML_BG_YELLOW

    # Positive result #
    elif 0 < float(value) <= 5:
        return Colors.HTML_BG_LIGHT_GREEN

    elif 5 < float(value) <= 10:
        return Colors.HTML_BG_GREEN_1

    elif 10 < float(value) <= 20:
        return Colors.HTML_BG_GREEN_2

    elif float(value) > 20:
        return Colors.HTML_BG_DARK_GREEN