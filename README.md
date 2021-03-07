# Profit-Taker Analyzer
Analyze Warframe Profit-Taker run from EE.log, marking important timestamps and total time elapsed.
For example: time betweens shield changes and leg breaks.

**Only works correctly when you are the host when taking down Profit-Taker**

Can be used for estimated time of an RTA speedrun.

Time starts when you exit the elevator, and ends on final blow to Profit-Taker. (Tested to be accurate)

Example output:
![Screenshot_1](https://user-images.githubusercontent.com/43719375/110228787-67b7ea80-7f36-11eb-8137-3733ccf689c2.png)

**How to use:**
1. Drag your EE.log to the .exe file or the terminal then hit ENTER
2. Your PT run(s) will be generated if it exists

EE.log can be found in `C:\Users\<USERNAME>\AppData\Local\Warframe` (EE.log is saved per session)

Support multiple Profit-Taker run per EE.log

**Limitation:**
1. Cannot detect whether shield is destroyed or reset using Amp or by time limit, only able to detect shield change.
2. If Profit-Taker regenerate on of it's legs, the run won't break, but break the timing about leg break and body break.

