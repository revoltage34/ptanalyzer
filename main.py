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
from requests import RequestException

from sty import fg
import colorama

from src.analyzer import Analyzer
from src.utils import color

VERSION = "v2.3.1"


def check_version():
    print(f'{fg.li_grey}Scanning for updates...', end='\r')
    # noinspection PyBroadException
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
    except RequestException:  # Generic IO failure
        print(f'{fg.red}Unable to connect to Github to check for newer versions. Continuing...')
    except ValueError:  # DNS failure
        print(f'{fg.red}Unable to resolve the ip address of Github.com to check for newer versions. Continuing...')
    except KeyError:  # Unexpected Github response, including being rate limited.
        print(f'{fg.red}Github sent back an unexpected response while checking for newer versions. Continuing...')
    except Exception:  # Catch-all
        traceback.print_exc()
        print(f'{fg.red}An unknown error occurred while checking for newer versions. Please screenshot this and report'
              f'this along with your EE.log attached.')


def error_msg():
    traceback.print_exc()
    print(color('\nAn unknown error occurred. Please screenshot this and report this along with your EE.log attached.',
                fg.li_red))
    input('Press ENTER to exit..')


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
