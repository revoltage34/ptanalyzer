# Profit-Taker Analyzer
Analyze Warframe Profit-Taker (Phase 4) run from EE.log, marking important timestamps and total time elapsed.
For example: times between shield changes and leg breaks.

**Ignores Profit-Taker runs where you are not the host.** 

Can be used to approximate the time of an RTA speedrun.

Time starts when you exit the elevator, and ends on the final blow to Profit-Taker. (Tested to be accurate)

**Approved tool by Warframe Speedrun!
 https://www.speedrun.com/wf/resources** 

Example output:  
![image](https://user-images.githubusercontent.com/24490028/114284985-0793f700-9a54-11eb-9d9f-ed3f8e316514.png)

**Usage:**  
* Either run the program to follow the game's log files and have your runs analyzed live.
* Or drag a specific log file onto the .exe file.

EE.log can be found in `%LOCALAPPDATA%\Local\Warframe` (EE.log is saved per session)

**Features:**
1. Analyzes specific log files by dragging one onto the .exe file.
2. Follows the game's log file analyze your runs live (survives game restarts!)
3. Displays the first shield element as soon as Profit-Taker spawns in follow mode.
4. Marks the best run and displays timestamps and phase durations.
5. Supports multiple Profit-Taker runs per EE.log
6. Automatically checks for newer versions.

**Limitation:**
1. The tool can only detect shield changes, not the cause of it. This means it cannot differentiate between it being destroyed and it getting reset by an Amp or the time limit.
2. Because the log only shows whenever shield changes, we don't know when exactly it's broken. The only way to know is when the shield element changes, but this does not apply to last shield before breaking legs. So no time will be shown for last shield of each phase. (Last shield of each phase's time is shown as **?s**)

Feel free to contact me in Discord about this tool: **ReVoltage#3425**
