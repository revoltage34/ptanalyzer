# Profit-Taker Analyzer
Analyze Warframe Profit-Taker (Phase 4) run from EE.log, marking important timestamps and total time elapsed.
For example: times between shield changes and leg breaks.

**Only works correctly when you are the host when taking down Profit-Taker** (Also solo recommended, co-op untested)

Can be used to approximate the time of an RTA speedrun.

Time starts when you exit the elevator, and ends on the final blow to Profit-Taker. (Tested to be accurate)

**Approved tool by Warframe Speedrun!
 https://www.speedrun.com/wf/resources** 

Example output:
![image](https://user-images.githubusercontent.com/24490028/113636080-2704db80-9672-11eb-8364-3ac6dc652f28.png)

**How to use:**  
1. A: Simply run the program and have it use your default EE.log. Both old and new Profit-Taker runs will be analyzed.   
   B: Alternatively, drag your EE.log to the .exe file or the terminal, then hit ENTER
2. Your PT run(s) will be generated if the log file contains completed Profit-Taker runs.

EE.log can be found in `%LOCALAPPDATA%\Local\Warframe` (EE.log is saved per session)

Supports multiple Profit-Taker run per EE.log

**Limitation:**
1. The tool can only detect shield changes, not the cause of it. This means it cannot differentiate between it being destroyed and it getting reset by an Amp or the time limit.
2. Because the log only shows whenever shield changes, we don't know when exactly it's broken. The only way to know is when the shield element changes, but this does not apply to last shield before breaking legs. So no time will be shown for last shield of each phase. (Last shield of each phase's time is shown as **?s**)

Feel free to contact me in Discord about this tool: **ReVoltage#3425**
