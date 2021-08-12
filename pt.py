#############################################
# Profit-Taker Analyzer by ReVoltage#3425   #
# Rewritten by Iterniam#5829                #
# https://github.com/revoltage34/ptanalyzer #
# Requires Python 3.9                       #
#############################################

import requests  # For checking the version
import packaging.version
import traceback
import sys
import os
from collections import defaultdict
from math import nan, isnan
from time import sleep
from typing import Iterator, Callable, Literal, Iterable

from sty import fg, rs
import colorama


VERSION = "v2.3.1"
follow_mode = False  # False -> analyze mode

dt_dict = {
    'DT_IMPACT': "Impact",
    'DT_PUNCTURE': "Puncture",
    'DT_SLASH': "Slash",

    'DT_FREEZE': "Cold",
    'DT_FIRE': "Heat",
    'DT_POISON': "Toxin",
    'DT_ELECTRICITY': "Electricity",

    'DT_GAS': "Gas",
    'DT_VIRAL': "Viral",
    'DT_MAGNETIC': "Magnetic",
    'DT_RADIATION': "Radiation",
    'DT_CORROSIVE': "Corrosive",
    'DT_EXPLOSION': "Blast"}


class RunAbort(Exception):
    def __init__(self, require_heist_start: bool):
        self.require_heist_start = require_heist_start


class LogEnd(Exception):
    pass


class Constants:
    NICKNAME = 'Net [Info]: name: '
    SQUAD_MEMBER = 'loadout loader finished.'
    HEIST_START = 'jobId=/Lotus/Types/Gameplay/Venus/Jobs/Heists/HeistProfitTakerBountyFour'
    HOST_MIGRATION = '"jobId" : "/Lotus/Types/Gameplay/Venus/Jobs/Heists/HeistProfitTakerBountyFour'
    HEIST_ABORT = 'SetReturnToLobbyLevelArgs: '
    ELEVATOR_EXIT = 'EidolonMP.lua: EIDOLONMP: Avatar left the zone'
    SHIELD_SWITCH = 'SwitchShieldVulnerability'
    LEG_KILL = 'Leg freshly destroyed at part'
    BODY_VULNERABLE = 'Camper->StartVulnerable() - The Camper can now be damaged!'
    STATE_CHANGE = 'CamperHeistOrbFight.lua: Landscape - New State: '
    PYLONS_LAUNCHED = 'Pylon launch complete'
    PHASE_1_START = 'Orb Fight - Starting first attack Orb phase'
    PHASE_ENDS = {1: 'Orb Fight - Starting second attack Orb phase',
                  2: 'Orb Fight - Starting third attack Orb phase',
                  3: 'Orb Fight - Starting final attack Orb phase',
                  4: ''}
    FINAL_PHASE = 4


def color(text: str, col: str) -> str:
    return col + text + rs.fg


def oxfordcomma(collection: Iterable[str]):
    collection = list(collection)
    if len(collection) == 0:
        return ''
    if len(collection) == 1:
        return collection[0]
    if len(collection) == 2:
        return collection[0] + ' and ' + collection[1]
    return ', '.join(collection[:-1]) + ', and ' + collection[-1]


def time_str(seconds: float, format_: Literal['brackets', 'units']) -> str:
    if format_ == 'brackets':
        return f'[{int(seconds / 60)}:{int(seconds % 60):02d}]'
    elif format_ == 'units':
        if seconds < 60:
            return f'{int(seconds % 60)}s {int(seconds % 1 * 1000)}ms'
        else:
            return f'{int(seconds / 60)}m {int(seconds % 60):02d}s {int(seconds % 1 * 1000):03d}ms'
    raise ValueError(f"Expected format_ to be 'brackets' or 'units' but was {format_}.")


class RelRun:

    def __init__(self,
                 run_nr: int,
                 nickname: str,
                 squad_members: set[str],
                 pt_found: float,
                 phase_durations: dict[int, float],
                 shields: dict[float, list[tuple[str, float]]],
                 legs: dict[int, list[float]],
                 body_dur: dict[int, float],
                 pylon_dur: dict[int, float]):
        self.run_nr = run_nr
        self.nickname = nickname
        self.squad_members = squad_members
        self.pt_found = pt_found
        self.phase_durations = phase_durations
        self.shields = shields
        self.legs = legs
        self.body_dur = body_dur
        self.pylon_dur = pylon_dur
        self.best_run = False
        self.best_run_yet = False

    def __str__(self):
        return '\n'.join((f'{key}: {val}' for key, val in vars(self).items()))

    def length(self):
        return self.phase_durations[4]

    def pretty_print(self):
        print(color('-' * 72, fg.white))  # header

        self.pretty_print_run_summary()

        print(f'{fg.li_red}From elevator to Profit-Taker took {self.pt_found:.3f}s. '
              f'Fight duration: {time_str(self.length() - self.pt_found, "units")}.\n')

        for i in [1, 2, 3, 4]:
            self.pretty_print_phase(i)

        self.pretty_print_sum_of_parts()

        print(f'{fg.white}{"-" * 72}\n\n')  # footer

    def pretty_print_run_summary(self):
        players = oxfordcomma([self.nickname] + list(self.squad_members - {self.nickname}))
        run_info = f'{fg.cyan}Profit-Taker Run #{self.run_nr} by {fg.li_cyan}{players}{fg.cyan} cleared in ' \
                   f'{fg.li_cyan}{time_str(self.length(), "units")}'
        if self.best_run:
            run_info += f'{fg.white} - {fg.li_magenta}Best run!'
        elif self.best_run_yet:
            run_info += f'{fg.white} - {fg.li_magenta}Best run yet!'
        print(f'{run_info}\n')

    def pretty_print_phase(self, phase: int):
        white_dash = f'{fg.white} - '
        print(f'{fg.li_green}> Phase {phase} {fg.li_cyan}{time_str(self.phase_durations[phase], "brackets")}')

        if phase in self.shields:
            shield_sum = sum(time for _, time in self.shields[phase] if not isnan(time))
            shield_str = f'{fg.white} | '.join((f'{fg.li_yellow}{s_type} {"?" if isnan(s_time) else f"{s_time:.3f}"}s'
                                                for s_type, s_time in self.shields[phase]))
            print(f'{fg.white} Shield change:\t{fg.li_green}{shield_sum:7.3f}s{white_dash}{fg.li_yellow}{shield_str}')

        normal_legs = [f'{fg.li_yellow}{time:.3f}s' for time in self.legs[phase][:4]]
        leg_regen = [f'{fg.red}{time:.3f}s' for time in self.legs[phase][4:]]
        leg_str = f"{fg.white} | ".join(normal_legs + leg_regen)
        print(f'{fg.white} Leg break:\t{fg.li_green}{sum(self.legs[phase]):7.3f}s{white_dash}{leg_str}')
        print(f'{fg.white} Body killed:\t{fg.li_green}{self.body_dur[phase]:7.3f}s')

        if phase in self.pylon_dur:
            print(f'{fg.white} Pylons:\t{fg.li_green}{self.pylon_dur[phase]:7.3f}s')

        if phase == 3 and self.shields[3.5]:  # Print phase 3.5
            print(f'{fg.white} Extra shields:\t\t   {fg.li_yellow}'
                  f'{" | ".join((shield for shield, _ in self.shields[3.5]))}')
        print('')  # to print an enter

    def pretty_print_sum_of_parts(self):
        shield_sum = sum(time for times in self.shields.values() for _, time in times if not isnan(time))
        leg_sum = sum(time for times in self.legs.values() for time in times)
        body_sum = sum(self.body_dur.values())
        pylon_sum = sum(self.pylon_dur.values())
        total_sum = shield_sum + leg_sum + body_sum + pylon_sum

        print(f'{fg.li_green}> Sum of parts {fg.li_cyan}{time_str(total_sum, "brackets")}')
        print(f'{fg.white} Shield change:\t{fg.li_green}{shield_sum:7.3f}s')
        print(f'{fg.white} Leg Break:\t{fg.li_green}{leg_sum:7.3f}s')
        print(f'{fg.white} Body Killed:\t{fg.li_green}{body_sum:7.3f}s')
        print(f'{fg.white} Pylons:\t{fg.li_green}{pylon_sum:7.3f}s')

    def sum_all_times(self) -> int:
        sum_ = 0
        for phase in [1, 2, 3, 4]:
            sum_ += sum(time for _, time in self.shields[phase] if not isnan(time))
            sum_ += sum(self.legs[phase])
        sum_ += sum(self.body_dur.values())
        sum_ += sum(self.pylon_dur.values())
        return sum_


class AbsRun:

    def __init__(self, run_nr: int):
        self.run_nr = run_nr
        self.nickname = ''
        self.squad_members: set[str] = set()
        self.heist_start = 0.0
        self.pt_found = 0.0
        self.shields: dict[float, list[tuple[str, float]]] = defaultdict(list)  # phase -> list((type, absolute time))
        self.legs: dict[int, list[float]] = defaultdict(list)  # phase -> list(absolute time)
        self.body_vuln: dict[int, float] = {}  # phase -> vuln-time
        self.body_kill: dict[int, float] = {}  # phase -> kill-time
        self.pylon_start: dict[int, float] = {}  # phase -> start-time
        self.pylon_end: dict[int, float] = {}  # phase -> end-time

    def __str__(self):
        return '\n'.join((f'{key}: {val}' for key, val in vars(self).items()))

    def post_process(self):
        # Take the final shield from shield phase 3.5 and prepend it to phase 4.
        if len(self.shields[3.5]) > 0:  # If the player is too fast, there won't be phase 3.5 shields.
            self.shields[4] = [self.shields[3.5].pop()] + self.shields[4]
        # Remove the extra shield from phase 4.
        self.shields[4].pop()

    def to_rel(self) -> RelRun:
        pt_found = self.pt_found - self.heist_start
        phase_durations = {}
        shields = defaultdict(list)
        legs = defaultdict(list)
        body_dur = {}
        pylon_dur = {}

        previous_value = self.pt_found
        for phase in [1, 2, 3, 4]:
            if phase in [1, 3, 4]:  # Phases with shield phases
                for i in range(len(self.shields[phase]) - 1):
                    shield_type, _ = self.shields[phase][i]
                    _, shield_end = self.shields[phase][i + 1]
                    shields[phase].append((shield_type, shield_end - previous_value))
                    previous_value = shield_end
                shields[phase].append((self.shields[phase][-1][0], nan))
            # Every phase has an armor phase
            for leg in self.legs[phase]:
                legs[phase].append(leg - previous_value)
                previous_value = leg
            body_dur[phase] = self.body_kill[phase] - self.body_vuln[phase]
            previous_value = self.body_kill[phase]

            if phase in [1, 3]:  # Phases with pylon phases
                pylon_dur[phase] = self.pylon_end[phase] - self.pylon_start[phase]
                previous_value = self.pylon_end[phase]

            # Set phase duration
            phase_durations[phase] = previous_value - self.heist_start

        # Set phase 3.5 shields
        shields[3.5] = [(shield, nan) for shield, _ in self.shields[3.5]]

        return RelRun(self.run_nr, self.nickname, self.squad_members, pt_found,
                      phase_durations, shields, legs, body_dur, pylon_dur)


def time_from_line(line: str) -> float:
    return float(line.split()[0])


def shield_from_line(line: str) -> tuple[str, float]:
    return dt_dict[line.split()[-1]], time_from_line(line)


def skip_until_one_of(log: Iterator[str], conditions: list[Callable[[str], bool]]) -> tuple[str, int]:
    try:
        line = next(log)
        while not any((condition(line) for condition in conditions)):  # Skip until one of the conditions hold
            line = next(log)
        return line, next((i for i, cond in enumerate(conditions) if cond(line)))  # return the first passing index
    except StopIteration:
        raise LogEnd()


def register_phase(log: Iterator[str], run: AbsRun, phase: int):
    kill_sequence = 0
    while True:  # match exists for phases 1-3, kill_sequence for phase 4.
        line, match = skip_until_one_of(log, [lambda line: Constants.SHIELD_SWITCH in line,
                                              lambda line: Constants.LEG_KILL in line,
                                              lambda line: Constants.BODY_VULNERABLE in line,  # is also phase 4 end
                                              lambda line: Constants.STATE_CHANGE in line,
                                              lambda line: Constants.PYLONS_LAUNCHED in line,
                                              lambda line: Constants.PHASE_1_START in line,
                                              lambda line: phase != Constants.FINAL_PHASE and \
                                                           Constants.PHASE_ENDS[phase] in line,
                                              lambda line: Constants.NICKNAME in line,
                                              lambda line: Constants.ELEVATOR_EXIT in line,
                                              lambda line: Constants.HEIST_START in line,  # Functions as abort as well
                                              lambda line: Constants.HOST_MIGRATION in line,
                                              lambda line: Constants.SQUAD_MEMBER in line])
        if match == 0:  # Shield switch
            # Shield_phase '3.5' is for when shields swap during the pylon phase in phase 3.
            shield_phase = 3.5 if phase == 3 and 3 in run.pylon_start else phase
            run.shields[shield_phase].append(shield_from_line(line))

            if follow_mode and len(run.shields[1]) == 1:  # The first shield can help determine whether to abort.
                print(f'{fg.white}First shield: {fg.li_cyan}{run.shields[phase][0][0]}')
        elif match == 1:  # Leg kill
            run.legs[phase].append(time_from_line(line))
        elif match == 2:  # Body vulnerable / phase 4 end
            if kill_sequence == 0:  # Only register the first invuln message on each phase
                run.body_vuln[phase] = time_from_line(line)
            kill_sequence += 1  # 3x BODY_VULNERABLE in one phase means PT dies.
            if kill_sequence == 3:  # PT dies.
                run.body_kill[phase] = time_from_line(line)
                return
        elif match == 3:  # Generic state change
            # Generic match on state change to find things we can't reliably find otherwise
            new_state = int(line.split()[8])
            # State 3, 5 and 6 are body kills for phases 1, 2 and 3.
            if new_state in [3, 5, 6]:
                run.body_kill[phase] = time_from_line(line)
        elif match == 4:  # Pylons launched
            run.pylon_start[phase] = time_from_line(line)
        elif match == 5:  # Profit-Taker found
            run.pt_found = time_from_line(line)
        elif match == 6:  # Phase endings (excludes phase 4)
            if phase in [1, 3]:  # Ignore phase 2 as it already matches body_kill.
                run.pylon_end[phase] = time_from_line(line)
            return
        elif match == 7:  # Nickname
            run.nickname = line.replace(',', '').split()[-2]
        elif match == 8:  # Elevator exit (start of speedrun timing)
            if not run.heist_start:  # Only use the first time that the zone is left aka heist is started.
                run.heist_start = time_from_line(line)
        elif match == 9:  # New heist start found
            raise RunAbort(require_heist_start=False)
        elif match == 10:  # Host migration
            raise RunAbort(require_heist_start=True)
        elif match == 11:  # Squad member
            run.squad_members.add(line.split()[-4])


def read_run(log: Iterator[str], run_nr: int, require_heist_start=False) -> AbsRun:
    """
    Reads a run.
    :param log: Iterator of the ee.log, expects a line with every next() call.
    :param run_nr: The number assigned to this run if it does not end up being aborted.
    :param require_heist_start: Indicate whether the start of this run indicates a previous run that was aborted.
    Necessary to properly initialize this run.
    :return: Absolute timings from the fight.
    """
    # Find heist load.
    if require_heist_start:  # Heist load is not required if the previous abort signifies the start of a new mission
        skip_until_one_of(log, [lambda line: Constants.HEIST_START in line])

    run = AbsRun(run_nr)

    for phase in [1, 2, 3, 4]:
        register_phase(log, run, phase)  # Adds information to run, including the start time
    run.post_process()  # Apply shield phase corrections

    return run


def print_summary(runs: list[RelRun]):
    assert len(runs) > 0
    best_run = min(runs, key=lambda run: run.length())
    print(f'{fg.li_green}Best run:\t\t'
          f'{fg.li_cyan}{time_str(best_run.length(), "units")} '
          f'{fg.cyan}(Run #{best_run.run_nr})')
    print(f'{fg.li_green}Average time:\t\t'
          f'{fg.li_cyan}{time_str(sum((run.length() for run in runs)) / len(runs), "units")}')
    print(f'{fg.li_green}Average fight duration:\t'
          f'{fg.li_cyan}{time_str(sum((run.length() - run.pt_found for run in runs)) / len(runs), "units")}\n\n')


def get_file() -> str:
    global follow_mode
    try:
        follow_mode = False
        return sys.argv[1]
    except IndexError:
        print(fr"{fg.li_grey}Opening Warframe's default log from %LOCALAPPDATA%\Warframe\EE.log in follow mode.")
        print('Follow mode means that runs will appear as you play. '
              'The first shield will also be printed when Profit-Taker spawns.')
        print('Note that you can analyze another file by dragging it into the exe file.')
        follow_mode = True
        return os.getenv('LOCALAPPDATA') + r'\Warframe\EE.log'


def error_msg():
    traceback.print_exc()
    print(
        color("\nAn error might have occured, please screenshot this and report this along with your EE.log attached.",
              fg.li_red))
    input('Press ENTER to exit..')
    sys.exit()


def follow(filename: str):
    """generator function that yields new lines in a file"""
    known_size = os.stat(filename).st_size
    with open(filename, 'r', encoding='latin-1') as file:
        # Start infinite loop
        cur_line = []  # Store multiple parts of the same line to deal with the logger comitting incomplete lines.
        while True:
            if (new_size := os.stat(filename).st_size) < known_size:
                print(f'{fg.white}Restart detected.')
                file.seek(0)  # Go back to the start of the file
                print('Succesfully reconnected to ee.log. Now listening for new Profit-Taker runs.')
            known_size = new_size

            # Yield lines until the last line of file and follow the end on a delay
            while line := file.readline():
                cur_line.append(line)  # Store whatever is found.
                if line[-1] == '\n':  # On newline, commit the line
                    yield ''.join(cur_line)
                    cur_line = []
            # No more lines are in the file - wait for more input before we yield it.
            sleep(.1)


def analyze_log(dropped_file: str):
    with open(dropped_file, 'r', encoding='latin-1') as it:
        try:
            runs = []
            require_heist_start = True
            while True:
                try:
                    runs.append(read_run(it, len(runs) + 1, require_heist_start).to_rel())
                    require_heist_start = True
                except RunAbort as abort:
                    require_heist_start = abort.require_heist_start
        except LogEnd:
            pass
    if len(runs) > 0:
        best_run = min(runs, key=lambda run: run.length())
        best_run.best_run = True
        for run in runs:
            run.pretty_print()

        print_summary(runs)
    else:
        print(f'{fg.white}No Profit-Taker runs found.\n'
              f'Note that you have to be host throughout the entire run for it to show up as a valid run.')

    input(f'{rs.fg}Press ENTER to exit...')


def follow_log(filename: str):
    it = follow(filename)
    best_time = float('inf')
    runs = []
    require_heist_start = True
    while True:
        try:
            run = read_run(it, len(runs) + 1, require_heist_start).to_rel()
            runs.append(run)
            require_heist_start = True

            if run.length() < best_time:
                best_time = run.length()
                run.best_run_yet = True
            run.pretty_print()
            print_summary(runs)
        except RunAbort as abort:
            require_heist_start = abort.require_heist_start


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


def main():
    colorama.init()  # To make ansi colors work.
    print(f'{fg.cyan}Profit-Taker Analyzer {VERSION} by {fg.li_cyan}ReVoltage#3425{fg.cyan}, rewritten by '
          f'{fg.li_cyan}Iterniam#5829.')
    print(color("https://github.com/revoltage34/ptanalyzer \n", fg.li_grey))

    check_version()

    filename = get_file()
    if follow_mode:
        follow_log(filename)
    else:
        analyze_log(filename)


if __name__ == "__main__":
    # noinspection PyBroadException
    try:
        main()
    except KeyboardInterrupt as e:  # To gracefully exit on ctrl + c
        pass
    except Exception:
        error_msg()
