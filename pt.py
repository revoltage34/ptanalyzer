#############################################
# Profit-Taker Analyzer by ReVoltage#3425   #
# https://github.com/revoltage34/ptanalyzer #
#############################################

import traceback
import sys
from sty import ef, fg, rs
from colorama import init
init()

version = "v1.2"
     
class Analyzer(object):
    def __init__(self):
        self.state = 0
        self.nickname = False
        self.stateLoop = [3, 4, 9, 12, 13, 18, 19]
        self.stateText = [
        'jobId=/Lotus/Types/Gameplay/Venus/Jobs/Heists/HeistProfitTakerBountyFour', #Get PT Heist
        #'Orb Fight - Starting find Orb phase', #PT Spawn
        'EidolonMP.lua: EIDOLONMP: Avatar left the zone', #Player leave elevator
        'Orb Fight - Starting first attack Orb phase', #PT found
        'SwitchShieldVulnerability', #Shield break/change
        'DestroyLeg', #Leg break
        'StartVulnerable', #2s body vulnerable delay
        'Orb Fight - Starting first Destroy Pylons phase', #Body destroyed
        'Pylon launch complete', #Pylon launched
        'Orb Fight - Starting second attack Orb phase', #Pylon destroyed
        'DestroyLeg', #Leg break
        'StartVulnerable', #2s body vulnerable delay
        'Orb Fight - Starting third attack Orb phase', #Body destroyed
        'SwitchShieldVulnerability', #Shield break/change
        'DestroyLeg', #Leg break
        'StartVulnerable', #2s body vulnerable delay
        'Orb Fight - Starting third Destroy Pylons phase', #Body destroyed
        'Pylon launch complete', #Pylon launched
        'Orb Fight - Starting final attack Orb phase', #Pylon destroyed
        'SwitchShieldVulnerability', #Shield break/change
        'DestroyLeg', #Leg break
        'StartVulnerable', #2s body vulnerable delay
        'StartVulnerable', #Filler
        'StartVulnerable' #Finish
        ]
        self.dictDT = {
        'DT_IMPACT' : "Impact",
        'DT_PUNCTURE' : "Puncture",
        'DT_SLASH' : "Slash",

        'DT_FREEZE' : "Cold",
        'DT_FIRE' : "Heat",
        'DT_POISON' : "Toxin",
        'DT_ELECTRICITY' : "Electricity",

        'DT_GAS' : "Gas",
        'DT_VIRAL' : "Viral",
        'DT_MAGNETIC' : "Magnetic",
        'DT_RADIATION' : "Radiation",
        'DT_CORROSIVE' : "Corrosive",
        'DT_EXPLOSION' : "Blast"
        }
        self.damageType = []
        self.stateTime = [0, 0, 0, [], [], 0, 0, 0, 0, [], 0, 0, [], [], 0, 0, 0, 0, [], [], 0, 0, 0]

    def state_check(self, line):
        if self.state == len(self.stateText):
            return 1 #Run complete
        if self.state > 0 and 'SwitchShieldVulnerability' in line:
            self.damageType.append(self.dictDT[line.split()[-1]])
        if self.state > 0 and 'jobId=/Lotus/Types/Gameplay/Venus/Jobs/Heists/HeistProfitTakerBountyFour' in line:
            return -1 #Run abort detected
        if not self.nickname and 'Player name is ' in line:
            self.nickname = line.split()[-1]
        if self.state in self.stateLoop:
            if not self.stateText[self.state + 1] in line:
                if self.stateText[self.state] in line:
                    self.stateTime[self.state].append(float(line.split(' ', 1)[0]))
            else:
                self.state += 1
                self.state_check(line)
        elif self.stateText[self.state] in line:
            if self.state == 0:
                self.stateTime[self.state] = 0
            else:
                self.stateTime[self.state] = float(line.split(' ', 1)[0])             
            self.state += 1
        return 0 #Still running
    
def color(text, col):
    return col + text + rs.fg
    
def ErrorMsg():
    traceback.print_exc()
    print(color("\nAn error might have occured, please screenshot this and report this along with your EE.log attached.", fg.li_red))
    input('Press ENTER to exit..')
    sys.exit()


print(fg.cyan + "Profit-Taker Analyzer " + version + " by " + fg.li_cyan + "ReVoltage#3425")
print(color("https://github.com/revoltage34/ptanalyzer \n", fg.white))

try:
    droppedFile = sys.argv[1]
except:
    print(fg.li_green + "How to use:" + fg.li_yellow)
    print("Drag your EE.log to the .exe file or this terminal then hit ENTER")
    print("Support multiple Profit-Taker run per EE.log\n")
    print("Or just hit ENTER now to exit..\n" + fg.rs)
    fname = input()
    droppedFile = str(fname).replace("\"", "")

if droppedFile != "":
    text = open(droppedFile, 'r', encoding='utf-8', errors='ignore').readlines()
else:
    sys.exit()

PT = [] #List of class Analyzer
RT = [] #Timestamps
RT_c = [] #Gap between timestamps

found = False
run = 0

PT.append(Analyzer())
RT.append([])
RT_c.append([])
try:
    for line in text:
        check = PT[run].state_check(line)
        if check > 0:
            count = 0
            start = PT[run].stateTime[1]
            for t in PT[run].stateTime:
                if count in PT[run].stateLoop:
                    temp = []
                    for x in t:
                        temp.append(round(x - start, 3))
                    RT[run].append(temp)
                else:
                    RT[run].append(round(t - start, 3))
                count += 1
                
            RT[run][4].pop()
            RT[run][9].pop()
            RT[run][13].pop()
            RT[run][19].pop()
                
            count = 0
            before = RT[run][1]
            for t in RT[run]:
                if count in PT[run].stateLoop:
                    temp = []
                    for x in t:
                        temp.append(str(round(x - before, 3)))
                        before = x
                    RT_c[run].append(temp)
                else:
                    RT_c[run].append(str(round(t - before, 3)))
                    before = t
                count += 1
                
            #for t in RT_c[run]:
                #print(str(t) + '\n')
            found = True
            nickname = PT[run].nickname
            
            PT.append(Analyzer())
            RT.append([])
            RT_c.append([])
            run += 1
        elif check < 0:
            PT[run] = Analyzer()
except:
    ErrorMsg()
    
try:
    if (not found):
        print("Profit-Taker run not found")
    else:
        for i in range(run):
            shieldDT = 0
            print(fg.white + "------------------------------------------------------------------------" + rs.fg)
            
            mins = str(int(RT[i][-1]/60))
            secs = str(int(RT[i][-1]%60))
            ms = str(int(RT[i][-1]%1*1000))
            print(fg.cyan + "Profit-Taker Run #" + str(i + 1) + " by " + color(nickname, fg.li_cyan) + fg.cyan + " cleared in " + color(mins + "m " + secs + "s " + ms + "ms\n", fg.li_cyan))

            print(color("From elevator to Profit-Taker took " + RT_c[i][2] + "s\n", fg.li_red))
            
            #--PHASE 1--#
            mins = str(int(RT[i][6]/60))
            secs = str(int(RT[i][6]%60))
            if RT[i][6]%60 < 10:
                secs = "0" + secs
            print(color("> Phase 1 ", fg.li_green) + color("[" + mins + ":" + secs + "]", fg.li_cyan))
            temp = ""
            for t in RT_c[i][3]:
                if temp != "":
                    temp += " | "
                temp += PT[i].damageType[shieldDT] + " " + str(t) + "s"
                shieldDT += 1
            print(color(" Shield change: ", fg.white) + fg.li_yellow + temp)
            
            temp = ""
            for t in RT_c[i][4]:
                if temp != "":
                    temp += " | "
                temp += str(t) + "s"
            print(color(" Leg break: ", fg.white) + fg.li_yellow + temp)
            
            
            print(color(" Body destroyed in " + RT_c[i][6] + "s\n", fg.white))
            
            #--PHASE 2--#
            mins = str(int(RT[i][11]/60))
            secs = str(int(RT[i][11]%60))
            if RT[i][11]%60 < 10:
                secs = "0" + secs
            print(color("> Phase 2 ", fg.li_green) + color("[" + mins + ":" + secs + "]", fg.li_cyan))
            print(color(" 4 Pylons destroyed in " + RT_c[i] [8] + "s", fg.white))
            
            temp = ""
            for t in RT_c[i][9]:
                if temp != "":
                    temp += " | "
                temp += str(t) + "s"
            print(color(" Leg break: ", fg.white) + fg.li_yellow + temp)
            
            
            print(color(" Body destroyed in " + RT_c[i][11] + "s\n", fg.white))
            
            #--PHASE 3--#
            mins = str(int(RT[i][15]/60))
            secs = str(int(RT[i][15]%60))
            if RT[i][15]%60 < 10:
                secs = "0" + secs
            print(color("> Phase 3 ", fg.li_green) + color("[" + mins + ":" + secs + "]", fg.li_cyan))
            temp = ""
            for t in RT_c[i][12]:
                if temp != "":
                    temp += " | "
                temp += PT[i].damageType[shieldDT] + " " + str(t) + "s"
                shieldDT += 1
            print(color(" Shield change: ", fg.white) + fg.li_yellow + temp)
            
            temp = ""
            for t in RT_c[i][13]:
                if temp != "":
                    temp += " | "
                temp += str(t) + "s"
            print(color(" Leg break: ", fg.white) + fg.li_yellow + temp)
            
            print(color(" Body destroyed in " + RT_c[i][15] + "s\n", fg.white))
            
            #--PHASE 4--#
            mins = str(int(RT[i][22]/60))
            secs = str(int(RT[i][22]%60))
            if RT[i][22]%60 < 10:
                secs = "0" + secs
            print(color("> Phase 4 ", fg.li_green) + color("[" + mins + ":" + secs + "]", fg.li_cyan))
            print(color(" 6 Pylons destroyed in " + RT_c[i] [17] + "s", fg.white))
            
            temp = ""
            for t in RT_c[i][18]:
                if temp != "":
                    temp += " | "
                temp += PT[i].damageType[shieldDT] + " " + str(t) + "s"
                shieldDT += 1
            print(color(" Shield change: ", fg.white) + fg.li_yellow + temp)
            
            temp = ""
            for t in RT_c[i][19]:
                if temp != "":
                    temp += " | "
                temp += str(t) + "s"
            print(color(" Leg break: ", fg.white) + fg.li_yellow + temp)
            
            print(color(" Body destroyed in " + RT_c[i][22] + "s\n", fg.white))
            
            print(fg.white + "------------------------------------------------------------------------\n\n" + rs.fg)
        
    input('Press ENTER to exit..')
except:
    ErrorMsg()