#############################################
# Profit-Taker Analyzer by ReVoltage#3425   #
# Rewritten by Iterniam#5829                #
# https://github.com/revoltage34/ptanalyzer #
# Requires Python 3.9                       #
#############################################
import sys
import traceback

import requests  # For checking the version
import packaging.version

from sty import fg
import colorama

from src.analyzer import Analyzer
from src.utils import color

VERSION = "v2.3.1"


def check_version():
    print(f'{fg.li_grey}Scanning for updates...', end='\r')
    try:
        response = requests.get("https://api.github.com/repos/revoltage34/ptanalyzer/releases/latest", timeout=2)
        json = response.json()
        latest_version = json['tag_name']  # KeyError -> got a non-200 OK message
        if packaging.version.parse(VERSION) < packaging.version.parse(latest_version):
            print(f'{fg.li_green}New version detected!       \n'
                  f'{fg.white}You are currently on version {VERSION}, whereas the latest is {latest_version}.\n'
                  f'To download the new update, visit https://github.com/revoltage34/ptanalyzer/releases/latest.')
        else:
            print(f'{fg.li_grey}Version is up-to-date.      ')
    except (requests.exceptions.RequestException, KeyError, ValueError):
        # Possible errors are: Internet down, slow or unexpected Github response, or a failed DNS lookup.
        print(f'{fg.red}Unable to connect to Github to check for new versions. Continuing...')
        return


def error_msg():
    traceback.print_exc()
    print(
        color("\nAn error might have occurred, please screenshot this and report this along with your EE.log attached.",
              fg.li_red))
    input('Press ENTER to exit..')
    sys.exit()


def main():
    colorama.init()  # To make ansi colors work.
    print(f'{fg.cyan}Profit-Taker Analyzer {VERSION} by {fg.li_cyan}ReVoltage#3425{fg.cyan}, rewritten by '
          f'{fg.li_cyan}Iterniam#5829.')
    print(color("https://github.com/revoltage34/ptanalyzer \n", fg.li_grey))

    check_version()
    Analyzer().run()


if __name__ == "__main__":
    # noinspection PyBroadException
    try:
        main()
    except KeyboardInterrupt as e:  # To gracefully exit on ctrl + c
        pass
    except Exception:
        error_msg()
