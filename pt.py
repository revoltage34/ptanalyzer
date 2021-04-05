#############################################
# Profit-Taker Analyzer by ReVoltage#3425   #
# Rewritten by Iterniam#5829                #
# https://github.com/revoltage34/ptanalyzer #
# Requires Python 3.9                       #
#############################################

import traceback
import sys
import os
from collections import defaultdict
from math import nan, isnan
from queue import Queue
from time import sleep
from typing import Iterator, Callable

from sty import fg, rs
from colorama import init

init()

version = "v2.0"

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
    pass


class LogEnd(Exception):
    pass


class Constants:
    NICKNAME = 'Player name is'
    HEIST_START = 'jobId=/Lotus/Types/Gameplay/Venus/Jobs/Heists/HeistProfitTakerBountyFour'
    HEIST_ABORT = 'SetReturnToLobbyLevelArgs: '
    ELEVATOR_EXIT = 'EidolonMP.lua: EIDOLONMP: Avatar left the zone'
    SHIELD_SWITCH = 'SwitchShieldVulnerability'
    LEG_KILL = 'Leg freshly destroyed at part'
    BODY_VULNERABLE = 'Camper->StartVulnerable() - The Camper can now be damaged!'
    BODY_KILLED = 'Camper->GetUpFromStun()'  # Note that there is also a CompleteGetUpFromStun() function
    PYLONS_LAUNCHED = 'Pylon launch complete'
    PHASE_1_START = 'Orb Fight - Starting first attack Orb phase'
    PHASE_ENDS = {1: 'Orb Fight - Starting second attack Orb phase',
                  2: 'Orb Fight - Starting third attack Orb phase',
                  3: 'Orb Fight - Starting final attack Orb phase',
                  4: ''}
    FINAL_PHASE = 4


def color(text: str, col: str) -> str:
    return col + text + rs.fg


class RelRun:

    def __init__(self,
                 nickname: str,
                 pt_found: float,
                 phase_durations: dict[int, float],
                 shields: dict[int, list[tuple[str, float]]],
                 legs: dict[int, list[float]],
                 body_dur: dict[int, float],
                 pylon_dur: dict[int, float]):
        self.nickname = nickname
        self.pt_found = pt_found
        self.phase_durations = phase_durations
        self.shields = shields
        self.legs = legs
        self.body_dur = body_dur
        self.pylon_dur = pylon_dur

    def __str__(self):
        return '\n'.join((f'{key}: {val}' for key, val in vars(self).items()))

    def pretty_print(self, run_nr: int = 1):
        print(color('-' * 72, fg.white))  # header

        tot_time = self.phase_durations[4]
        print(f'{fg.cyan}Profit-Taker Run #{run_nr} by {fg.li_cyan}{self.nickname}{fg.cyan} cleared in '
              f'{fg.li_cyan}{int(tot_time / 60)}m {int(tot_time % 60)}s {int(tot_time % 1 * 1000)}ms\n')

        print(f'{fg.li_red}From elevator to Profit-Taker took {self.pt_found:.3f}s.\n')

        for i in [1, 2, 3, 4]:
            self.pretty_print_phase(i)

        self.pretty_print_sum_of_parts()

        print(f'{fg.white}{"-" * 72}\n\n')  # footer

    def pretty_print_phase(self, phase: int):
        white_dash = f'{fg.white} - '
        print(f'{fg.li_green}> Phase {phase} {fg.li_cyan}'
              f'[{int(self.phase_durations[phase] / 60)}:{int(self.phase_durations[phase] % 60):02d}]')

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
        print('')  # to print an enter

    def pretty_print_sum_of_parts(self):
        shield_sum = sum(time for times in self.shields.values() for _, time in times if not isnan(time))
        leg_sum = sum(time for times in self.legs.values() for time in times)
        body_sum = sum(self.body_dur.values())
        pylon_sum = sum(self.pylon_dur.values())
        total_sum = shield_sum + leg_sum + body_sum + pylon_sum

        print(f'{fg.li_green}> Sum of parts {fg.li_cyan}[{int(total_sum / 60)}:{int(total_sum % 60):02d}]')
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

    def __init__(self, nickname: str, heist_start: float):
        self.nickname = nickname
        self.heist_start = heist_start
        self.pt_found = 0.0
        self.shields: dict[int, list[tuple[str, float]]] = defaultdict(list)  # phase -> list((type, absolute time))
        self.legs: dict[int, list[float]] = defaultdict(list)  # phase -> list(absolute time)
        self.body_vuln: dict[int, float] = {}  # phase -> vuln-time
        self.body_kill: dict[int, float] = {}  # phase -> kill-time
        self.pylon_start: dict[int, float] = {}  # phase -> start-time
        self.pylon_end: dict[int, float] = {}  # phase -> end-time

    def __str__(self):
        return '\n'.join((f'{key}: {val}' for key, val in vars(self).items()))

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

        return RelRun(self.nickname, pt_found, phase_durations, shields, legs, body_dur, pylon_dur)


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
                                              lambda line: Constants.BODY_KILLED in line,
                                              lambda line: Constants.PYLONS_LAUNCHED in line,
                                              lambda line: Constants.PHASE_1_START in line,
                                              lambda line: phase != Constants.FINAL_PHASE and \
                                                           Constants.PHASE_ENDS[phase] in line,
                                              lambda line: Constants.HEIST_START in line])  # Functions as abort as well
        if match == 0:
            run.shields[phase].append(shield_from_line(line))
        elif match == 1:
            run.legs[phase].append(time_from_line(line))
        elif match == 2:
            if kill_sequence == 0:  # Only register the first invuln message on each phase
                run.body_vuln[phase] = time_from_line(line)
            kill_sequence += 1  # 3x BODY_VULNERABLE in one phase means PT dies.
            if kill_sequence == 3:  # PT dies.
                run.shields[phase].pop()  # We get a random extra shield we don't need.
                run.body_kill[phase] = time_from_line(line)
                return
        elif match == 3:
            run.body_kill[phase] = time_from_line(line)
        elif match == 4:
            run.pylon_start[phase] = time_from_line(line)
        elif match == 5:
            run.pt_found = time_from_line(line)
        elif match == 6:
            if phase in [1, 3]:  # Ignore phase 2 as it already matches body_kill.
                run.pylon_end[phase] = time_from_line(line)
            if phase == 3:  # Put the final shield from phase 3 as the first of phase 4.
                run.shields[phase + 1].append(run.shields[phase].pop())
            return
        elif match == 7:
            raise RunAbort()


def read_run(log: Iterator[str], aborted=False) -> AbsRun:
    """
    Reads a run.
    :param log: Iterator of the ee.log, expects a line with every next() call
    :param aborted: Indicate whether the start of this run indicates a previous run that was aborted.
    Necessary to properly initialize this run.
    :return: Absolute timings from the fight.
    """
    # Find heist load.
    if not aborted:  # Only demand the heist load if the run doesn't indicate another was aborted.
        skip_until_one_of(log, [lambda line: Constants.HEIST_START in line])

    nickname = skip_until_one_of(log, [lambda line: Constants.NICKNAME in line])[0].split()[-1]

    # Find heist start
    line, _ = skip_until_one_of(log, [lambda line: Constants.ELEVATOR_EXIT in line])
    run = AbsRun(nickname, time_from_line(line))

    for phase in [1, 2, 3, 4]:
        register_phase(log, run, phase)  # Adds information to run

    return run


def get_file() -> Iterator[str]:
    try:
        dropped_file = sys.argv[1]
        return open(dropped_file, 'r')
    except IndexError:
        print(r'Analyzing %LOCALAPPDATA%\Warframe\EE.log.')
        print('Note that you can analyze another file by dragging it into the exe file.')
        dropped_file = os.getenv('LOCALAPPDATA') + r'\Warframe\EE.log'
        print('The file is being followed, meaning that runs will appear as you play.')
        return follow(dropped_file)


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
    file = open(filename, "r")

    # Start infinite loop
    cur_line = []  # Store multiple parts of the same line to deal with the logger comitting incomplete lines.
    while True:
        if (new_size := os.stat(filename).st_size) < known_size:
            print('Restart detected.')
            file = open(filename, 'r')
            print('Succesfully reconnected to ee.log. Now listening for new Profit-Taker runs.')
        known_size = new_size

        # Yield lines until the last line of file and follow the end on a delay
        while line := file.readline():
            cur_line.append(line)  # Store whatever is found.
            if line[-1] == '\n':  # On newline, commit the line
                yield ''.join(cur_line)
                cur_line = []
            else:  # No newline means we wait for more input before we yield it.
                sleep(1)


def main():
    it = get_file()
    try:
        run_nr = 1
        aborted = False
        while True:
            try:
                read_run(it, aborted).to_rel().pretty_print(run_nr)
                run_nr += 1
                aborted = False
            except RunAbort:
                aborted = True
    except LogEnd:
        input(f'{rs.fg}Press ENTER to exit...')


if __name__ == "__main__":
    print(f'{fg.cyan}Profit-Taker Analyzer {version} by {fg.li_cyan}ReVoltage#3425{fg.cyan}, rewritten by '
          f'{fg.li_cyan}Iterniam#5829.')
    print(color("https://github.com/revoltage34/ptanalyzer \n", fg.white))
    # noinspection PyBroadException
    try:
        main()
    except Exception:
        error_msg()
