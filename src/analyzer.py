import os
import sys
from collections import defaultdict
from math import nan, isnan
from statistics import median
from time import sleep
from typing import Iterator, Callable

from sty import rs, fg

from src.enums.damage_types import DT
from src.exceptions.log_end import LogEnd
from src.exceptions.run_abort import RunAbort
from src.utils import color, time_str, oxfordcomma


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


class RelRun:

    def __init__(self,
                 run_nr: int,
                 nickname: str,
                 squad_members: set[str],
                 pt_found: float,
                 phase_durations: dict[int, float],
                 shield_phases: dict[float, list[tuple[DT, float]]],
                 legs: dict[int, list[float]],
                 body_dur: dict[int, float],
                 pylon_dur: dict[int, float]):
        self.run_nr = run_nr
        self.nickname = nickname
        self.squad_members = squad_members
        self.pt_found = pt_found
        self.phase_durations = phase_durations
        self.shield_phases = shield_phases
        self.legs = legs
        self.body_dur = body_dur
        self.pylon_dur = pylon_dur
        self.best_run = False
        self.best_run_yet = False

    def __str__(self):
        return '\n'.join((f'{key}: {val}' for key, val in vars(self).items()))

    @property
    def length(self):
        return self.phase_durations[4]

    @property
    def shield_sum(self) -> float:
        """Sum of shield times over all phases, excluding the nan values."""
        return sum(time for times in self.shield_phases.values() for _, time in times if not isnan(time))

    @property
    def leg_sum(self) -> float:
        """Sum of the leg times over all phases."""
        return sum(time for times in self.legs.values() for time in times)

    @property
    def body_sum(self) -> float:
        """Sum of the body times over all phases."""
        return sum(self.body_dur.values())

    @property
    def pylon_sum(self) -> float:
        """"Sum of the pylon times over all phases."""
        return sum(self.pylon_dur.values())

    @property
    def sum_of_parts(self) -> float:
        """"Sum of the individual parts of the fight. This cuts out some animations/waits."""
        return self.shield_sum + self.leg_sum + self.body_sum + self.pylon_sum

    @property
    def shields(self) -> list[tuple[str, float]]:
        """The shields without their phases, flattened."""
        return [shield_tuple for shield_phase in self.shield_phases.values() for shield_tuple in shield_phase]

    def pretty_print(self):
        print(color('-' * 72, fg.white))  # header

        self.pretty_print_run_summary()

        print(f'{fg.li_red}From elevator to Profit-Taker took {self.pt_found:.3f}s. '
              f'Fight duration: {time_str(self.length - self.pt_found, "units")}.\n')

        for i in [1, 2, 3, 4]:
            self.pretty_print_phase(i)

        self.pretty_print_sum_of_parts()

        print(f'{fg.white}{"-" * 72}\n\n')  # footer

    def pretty_print_run_summary(self):
        players = oxfordcomma([self.nickname] + list(self.squad_members - {self.nickname}))
        run_info = f'{fg.cyan}Profit-Taker Run #{self.run_nr} by {fg.li_cyan}{players}{fg.cyan} cleared in ' \
                   f'{fg.li_cyan}{time_str(self.length, "units")}'
        if self.best_run:
            run_info += f'{fg.white} - {fg.li_magenta}Best run!'
        elif self.best_run_yet:
            run_info += f'{fg.white} - {fg.li_magenta}Best run yet!'
        print(f'{run_info}\n')

    def pretty_print_phase(self, phase: int):
        white_dash = f'{fg.white} - '
        print(f'{fg.li_green}> Phase {phase} {fg.li_cyan}{time_str(self.phase_durations[phase], "brackets")}')

        if phase in self.shield_phases:
            shield_sum = sum(time for _, time in self.shield_phases[phase] if not isnan(time))
            shield_str = f'{fg.white} | '.join((f'{fg.li_yellow}{s_type} {"?" if isnan(s_time) else f"{s_time:.3f}"}s'
                                                for s_type, s_time in self.shield_phases[phase]))
            print(f'{fg.white} Shield change:\t{fg.li_green}{shield_sum:7.3f}s{white_dash}{fg.li_yellow}{shield_str}')

        normal_legs = [f'{fg.li_yellow}{time:.3f}s' for time in self.legs[phase][:4]]
        leg_regen = [f'{fg.red}{time:.3f}s' for time in self.legs[phase][4:]]
        leg_str = f"{fg.white} | ".join(normal_legs + leg_regen)
        print(f'{fg.white} Leg break:\t{fg.li_green}{sum(self.legs[phase]):7.3f}s{white_dash}{leg_str}')
        print(f'{fg.white} Body killed:\t{fg.li_green}{self.body_dur[phase]:7.3f}s')

        if phase in self.pylon_dur:
            print(f'{fg.white} Pylons:\t{fg.li_green}{self.pylon_dur[phase]:7.3f}s')

        if phase == 3 and self.shield_phases[3.5]:  # Print phase 3.5
            print(f'{fg.white} Extra shields:\t\t   {fg.li_yellow}'
                  f'{" | ".join((str(shield) for shield, _ in self.shield_phases[3.5]))}')
        print('')  # to print an enter

    def pretty_print_sum_of_parts(self):
        print(f'{fg.li_green}> Sum of parts {fg.li_cyan}{time_str(self.sum_of_parts, "brackets")}')
        print(f'{fg.white} Shield change:\t{fg.li_green}{self.shield_sum:7.3f}s')
        print(f'{fg.white} Leg Break:\t{fg.li_green}{self.leg_sum:7.3f}s')
        print(f'{fg.white} Body Killed:\t{fg.li_green}{self.body_sum:7.3f}s')
        print(f'{fg.white} Pylons:\t{fg.li_green}{self.pylon_sum:7.3f}s')


class AbsRun:

    def __init__(self, run_nr: int):
        self.run_nr = run_nr
        self.nickname = ''
        self.squad_members: set[str] = set()
        self.heist_start = 0.0
        self.pt_found = 0.0
        self.shield_phases: dict[float, list[tuple[DT, float]]] = defaultdict(list)
        # phase -> list((type, absolute time))
        self.legs: dict[int, list[float]] = defaultdict(list)  # phase -> list(absolute time)
        self.body_vuln: dict[int, float] = {}  # phase -> vuln-time
        self.body_kill: dict[int, float] = {}  # phase -> kill-time
        self.pylon_start: dict[int, float] = {}  # phase -> start-time
        self.pylon_end: dict[int, float] = {}  # phase -> end-time

    def __str__(self):
        return '\n'.join((f'{key}: {val}' for key, val in vars(self).items()))

    def post_process(self):
        # Take the final shield from shield phase 3.5 and prepend it to phase 4.
        if len(self.shield_phases[3.5]) > 0:  # If the player is too fast, there won't be phase 3.5 shields.
            self.shield_phases[4] = [self.shield_phases[3.5].pop()] + self.shield_phases[4]
        # Remove the extra shield from phase 4.
        self.shield_phases[4].pop()

    def to_rel(self) -> RelRun:
        pt_found = self.pt_found - self.heist_start
        phase_durations = {}
        shield_phases = defaultdict(list)
        legs = defaultdict(list)
        body_dur = {}
        pylon_dur = {}

        previous_value = self.pt_found
        for phase in [1, 2, 3, 4]:
            if phase in [1, 3, 4]:  # Phases with shield phases
                for i in range(len(self.shield_phases[phase]) - 1):
                    shield_type, _ = self.shield_phases[phase][i]
                    _, shield_end = self.shield_phases[phase][i + 1]
                    shield_phases[phase].append((shield_type, shield_end - previous_value))
                    previous_value = shield_end
                shield_phases[phase].append((self.shield_phases[phase][-1][0], nan))
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
        shield_phases[3.5] = [(shield, nan) for shield, _ in self.shield_phases[3.5]]

        return RelRun(self.run_nr, self.nickname, self.squad_members, pt_found,
                      phase_durations, shield_phases, legs, body_dur, pylon_dur)


class Analyzer:

    def __init__(self):
        self.follow_mode = False
        self.runs: list[RelRun] = []

    def run(self):
        filename = self.get_file()
        if self.follow_mode:
            self.follow_log(filename)
        else:
            self.analyze_log(filename)

    def get_file(self) -> str:
        try:
            self.follow_mode = False
            return sys.argv[1]
        except IndexError:
            print(fr"{fg.li_grey}Opening Warframe's default log from %LOCALAPPDATA%/Warframe/EE.log in follow mode.")
            print('Follow mode means that runs will appear as you play. '
                  'The first shield will also be printed when Profit-Taker spawns.')
            print('Note that you can analyze another file by dragging it into the exe file.')
            self.follow_mode = True
            try:
                return os.getenv('LOCALAPPDATA') + r'/Warframe/EE.log'
            except TypeError:
                print(f'{fg.li_red}Hi there Linux user! Check the README on github.com/revoltage34/ptanalyzer or '
                      f'idalon.com/pt to find out how to get follow mode to work.')
                print(f'{rs.fg}Press ENTER to exit...')
                input()  # input(prompt) doesn't work with color coding, so we separate it from the print.
                exit(-1)

    @staticmethod
    def follow(filename: str):
        """generator function that yields new lines in a file"""
        known_size = os.stat(filename).st_size
        with open(filename, 'r', encoding='latin-1') as file:
            # Start infinite loop
            cur_line = []  # Store multiple parts of the same line to deal with the logger committing incomplete lines.
            while True:
                if (new_size := os.stat(filename).st_size) < known_size:
                    print(f'{fg.white}Restart detected.')
                    file.seek(0)  # Go back to the start of the file
                    print('Successfully reconnected to ee.log. Now listening for new Profit-Taker runs.')
                known_size = new_size

                # Yield lines until the last line of file and follow the end on a delay
                while line := file.readline():
                    cur_line.append(line)  # Store whatever is found.
                    if line[-1] == '\n':  # On newline, commit the line
                        yield ''.join(cur_line)
                        cur_line = []
                # No more lines are in the file - wait for more input before we yield it.
                sleep(.1)

    def analyze_log(self, dropped_file: str):
        with open(dropped_file, 'r', encoding='latin-1') as it:
            try:
                require_heist_start = True
                while True:
                    try:
                        self.runs.append(self.read_run(it, len(self.runs) + 1, require_heist_start).to_rel())
                        require_heist_start = True
                    except RunAbort as abort:
                        require_heist_start = abort.require_heist_start
            except LogEnd:
                pass
        if len(self.runs) > 0:
            best_run = min(self.runs, key=lambda run_: run_.length)
            best_run.best_run = True
            for run in self.runs:
                run.pretty_print()

            self.print_summary()
        else:
            print(f'{fg.white}No Profit-Taker runs found.\n'
                  f'Note that you have to be host throughout the entire run for it to show up as a valid run.')

        print(f'{rs.fg}Press ENTER to exit...')
        input()  # input(prompt) doesn't work with color coding, so we separate it in a print and an empty input.

    def follow_log(self, filename: str):
        it = Analyzer.follow(filename)
        best_time = float('inf')
        require_heist_start = True
        while True:
            try:
                run = self.read_run(it, len(self.runs) + 1, require_heist_start).to_rel()
                self.runs.append(run)
                require_heist_start = True

                if run.length < best_time:
                    best_time = run.length
                    run.best_run_yet = True
                run.pretty_print()
                self.print_summary()
            except RunAbort as abort:
                require_heist_start = abort.require_heist_start

    def read_run(self, log: Iterator[str], run_nr: int, require_heist_start=False) -> AbsRun:
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
            Analyzer.skip_until_one_of(log, [lambda line: Constants.HEIST_START in line])

        run = AbsRun(run_nr)

        for phase in [1, 2, 3, 4]:
            self.register_phase(log, run, phase)  # Adds information to run, including the start time
        run.post_process()  # Apply shield phase corrections

        return run

    def register_phase(self, log: Iterator[str], run: AbsRun, phase: int):
        kill_sequence = 0
        while True:  # match exists for phases 1-3, kill_sequence for phase 4.
            try:
                line = next(log)
            except StopIteration:
                raise LogEnd()

            if Constants.SHIELD_SWITCH in line:  # Shield switch
                # Shield_phase '3.5' is for when shields swap during the pylon phase in phase 3.
                shield_phase = 3.5 if phase == 3 and 3 in run.pylon_start else phase
                run.shield_phases[shield_phase].append(Analyzer.shield_from_line(line))

                # The first shield can help determine whether to abort.
                if self.follow_mode and len(run.shield_phases[1]) == 1:
                    print(f'{fg.white}First shield: {fg.li_cyan}{run.shield_phases[phase][0][0]}')
            elif Constants.LEG_KILL in line:  # Leg kill
                run.legs[phase].append(Analyzer.time_from_line(line))
            elif Constants.BODY_VULNERABLE in line:  # Body vulnerable / phase 4 end
                if kill_sequence == 0:  # Only register the first invuln message on each phase
                    run.body_vuln[phase] = Analyzer.time_from_line(line)
                kill_sequence += 1  # 3x BODY_VULNERABLE in one phase means PT dies.
                if kill_sequence == 3:  # PT dies.
                    run.body_kill[phase] = Analyzer.time_from_line(line)
                    return
            elif Constants.STATE_CHANGE in line:  # Generic state change
                # Generic match on state change to find things we can't reliably find otherwise
                new_state = int(line.split()[8])
                # State 3, 5 and 6 are body kills for phases 1, 2 and 3.
                if new_state in [3, 5, 6]:
                    run.body_kill[phase] = Analyzer.time_from_line(line)
            elif Constants.PYLONS_LAUNCHED in line:  # Pylons launched
                run.pylon_start[phase] = Analyzer.time_from_line(line)
            elif Constants.PHASE_1_START in line:  # Profit-Taker found
                run.pt_found = Analyzer.time_from_line(line)
            elif Constants.PHASE_ENDS[phase] in line and phase != Constants.FINAL_PHASE:  # Phase endings minus phase 4
                if phase in [1, 3]:  # Ignore phase 2 as it already matches body_kill.
                    run.pylon_end[phase] = Analyzer.time_from_line(line)
                return
            elif Constants.NICKNAME in line:  # Nickname
                run.nickname = line.replace(',', '').split()[-2]
            elif Constants.ELEVATOR_EXIT in line:  # Elevator exit (start of speedrun timing)
                if not run.heist_start:  # Only use the first time that the zone is left aka heist is started.
                    run.heist_start = Analyzer.time_from_line(line)
            elif Constants.HEIST_START in line:  # New heist start found
                raise RunAbort(require_heist_start=False)
            elif Constants.HOST_MIGRATION in line:  # Host migration
                raise RunAbort(require_heist_start=True)
            elif Constants.SQUAD_MEMBER in line:  # Squad member
                run.squad_members.add(line.split()[-4])

    @staticmethod
    def time_from_line(line: str) -> float:
        return float(line.split()[0])

    @staticmethod
    def shield_from_line(line: str) -> tuple[DT, float]:
        return DT.from_internal_name(line.split()[-1]), Analyzer.time_from_line(line)

    @staticmethod
    def skip_until_one_of(log: Iterator[str], conditions: list[Callable[[str], bool]]) -> tuple[str, int]:
        try:
            line = next(log)
            while not any((condition(line) for condition in conditions)):  # Skip until one of the conditions hold
                line = next(log)
            return line, next((i for i, cond in enumerate(conditions) if cond(line)))  # return the first passing index
        except StopIteration:
            raise LogEnd()

    def print_summary(self):
        assert len(self.runs) > 0
        best_run = min(self.runs, key=lambda run: run.length)
        print(f'{fg.li_green}Best run:\t\t'
              f'{fg.li_cyan}{time_str(best_run.length, "units")} '
              f'{fg.cyan}(Run #{best_run.run_nr})')
        print(f'{fg.li_green}Median time:\t\t'
              f'{fg.li_cyan}{time_str(median(run.length for run in self.runs), "units")}')
        print(f'{fg.li_green}Median fight duration:\t'
              f'{fg.li_cyan}{time_str(median(run.length - run.pt_found for run in self.runs), "units")}\n')
        print(f'{fg.li_green}Median sum of parts {fg.li_cyan}'
              f'{time_str(median(run.sum_of_parts for run in self.runs), "brackets")}')
        print(f'{fg.white} Median shield change:\t{fg.li_green}'
              f'{median(run.shield_sum for run in self.runs):7.3f}s')
        print(f'{fg.white} Median leg break:\t{fg.li_green}'
              f'{median(run.leg_sum for run in self.runs):7.3f}s')
        print(f'{fg.white} Median body killed:\t{fg.li_green}'
              f'{median(run.body_sum for run in self.runs):7.3f}s')
        print(f'{fg.white} Median pylons:\t\t{fg.li_green}'
              f'{median(run.pylon_sum for run in self.runs):7.3f}s')
