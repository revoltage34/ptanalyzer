# Profit-Taker Analyzer
Analyze Warframe Profit-Taker (Phase 4) run from EE.log, marking important timestamps and total time elapsed.
For example: times between shield changes and leg breaks.

**Ignores Profit-Taker runs where you are not the host.** 

Can be used to approximate the time of an RTA speedrun.

Time starts when you exit the elevator, and ends on the final blow to Profit-Taker. (Tested to be accurate)

**Approved tool by Warframe Speedrun!
 https://www.speedrun.com/wf/resources** 

Example output:  
![image](https://user-images.githubusercontent.com/24490028/113768421-1f9c0b80-9720-11eb-9618-f157ee17e86d.png)



**Usage:**  
* Either run the program to follow the game's log files and have your runs analyzed live.
* Or drag a specific log file onto the .exe file.

EE.log can be found in `%LOCALAPPDATA%\Local\Warframe` (EE.log is saved per session)

**Features:**
1. Analyze specific log files by dragging one onto the .exe file.
2. 'Follow' the game's log file to have your runs analyzed live (survives game restarts!)
3. Automatically mark the best run.
4. Easily view important timestamps and phase durations.
5. Supports multiple Profit-Taker runs per EE.log

**Limitation:**
1. The tool can only detect shield changes, not the cause of it. This means it cannot differentiate between it being destroyed and it getting reset by an Amp or the time limit.
2. Because the log only shows whenever shield changes, we don't know when exactly it's broken. The only way to know is when the shield element changes, but this does not apply to last shield before breaking legs. So no time will be shown for last shield of each phase. (Last shield of each phase's time is shown as **?s**)

Feel free to contact me in Discord about this tool: **ReVoltage#3425**
