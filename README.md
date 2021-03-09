# Profit-Taker Analyzer
Analyze Warframe Profit-Taker (Phase 4) run from EE.log, marking important timestamps and total time elapsed.
For example: time betweens shield changes and leg breaks.

**Only works correctly when you are the host when taking down Profit-Taker** (Also solo recommended, co-op untested)

Can be used for estimated time of an RTA speedrun.

Time starts when you exit the elevator, and ends on final blow to Profit-Taker. (Tested to be accurate)

**Approved tool by Warframe Speedrun!
 https://www.speedrun.com/wf/resources** 

Example output:
![image](https://user-images.githubusercontent.com/43719375/110268549-6c42d880-7ff4-11eb-80a9-f4a39b3a00ff.png)

**How to use:**
1. Drag your EE.log to the .exe file or the terminal then hit ENTER
2. Your PT run(s) will be generated if it exists

EE.log can be found in `C:\Users\<USERNAME>\AppData\Local\Warframe` (EE.log is saved per session)

Support multiple Profit-Taker run per EE.log

**Limitation:**
1. Cannot detect whether shield is destroyed or reset using Amp or by time limit, only able to detect shield change.
2. If Profit-Taker regenerate on of it's legs, the run won't break, but break the timing about leg break and body break.
3. Because the log only shows whenever shield changes, we don't know when exactly it's broken. The only way to know is when the shield element changes, but this does not apply to last shield before breaking legs. So no time will be shown for last shield of each phase.

Feel free to contact me in Discord about this tool: **ReVoltage#3425**
