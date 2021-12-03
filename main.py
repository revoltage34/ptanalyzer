#############################################
# Profit-Taker Analyzer by ReVoltage#3425   #
# Rewritten by Iterniam#5829                #
# https://github.com/revoltage34/ptanalyzer #
# Requires Python 3.9                       #
#############################################
import socket
import traceback

import requests  # For checking the version
import packaging.version
from requests import RequestException

from sty import fg
import colorama

from src.analyzer import Analyzer
from src.utils import color

VERSION = 'v2.5.1'


def check_version():
    print(f'{fg.li_grey}Scanning for updates...', end='\r')

    proxy = False
    try:
        socket.getaddrinfo('api.github.com', 80)
    except socket.gaierror:  # Used to catch DNS failure, also catches internet is offline.
        proxy = True

    # noinspection PyBroadException
    try:
        if proxy:
            json = requests.get('https://utils.idalon.com/v1/pt/releases', timeout=2).json()
            latest_version = json['items'][0]['version']
            download_link = 'https://idalon.com/pt'
        else:
            json = requests.get('https://api.github.com/repos/revoltage34/ptanalyzer/releases/latest', timeout=2).json()
            latest_version = json['tag_name']  # KeyError -> got a non-200 OK message
            download_link = 'https://github.com/revoltage34/ptanalyzer/releases/latest'

        if packaging.version.parse(VERSION) < packaging.version.parse(latest_version):
            print(f'{fg.li_green}New version detected!       \n'
                  f'{fg.white}You are currently on version {VERSION}, whereas the latest is {latest_version}.\n'
                  f'To download the new update, visit {download_link}.')
        else:
            print(f'{fg.li_grey}Version is up-to-date.      ')  # Whitespace necessary to overwrite previous message.
    except RequestException:  # Generic IO failure
        print(f'{fg.red}Unable to check for newer versions. Continuing...')
    except KeyError:  # Unexpected Github response, including being rate limited.
        print(f'{fg.red}Received an unexpected response while checking for newer versions. Continuing...')
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
