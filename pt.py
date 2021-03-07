#############################################
# Profit-Taker Analyzer by ReVoltage#3425   #
# https://github.com/revoltage34/ptanalyzer #
#############################################

import sys
        
class Analyzer(object):
    def __init__(self):
        self.state = 0
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
            return True
        if self.state > 0 and 'SwitchShieldVulnerability' in line:
            self.damageType.append(self.dictDT[line.split()[-1]])
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
        return False
    
    
try:
    droppedFile = sys.argv[1]
except:
    print("Profit-Taker Analyzer by ReVoltage#3425")
    print("https://github.com/revoltage34/ptanalyzer \n")
    print("How to use:")
    print("Drag your EE.log to the .exe file or this terminal then hit ENTER")
    print("Support multiple Profit-Taker run per EE.log\n")
    fname = input('Or just hit ENTER now to exit..\n')
    droppedFile = str(fname).replace("\"", "")

text = open(droppedFile, 'r').readlines()

PT = [] #List of class Analyzer
RT = [] #Timestamps
RT_c = [] #Gap between timestamps

found = False
run = 0


PT.append(Analyzer())
RT.append([])
RT_c.append([])

for line in text:
    if (PT[run].state_check(line)):
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
        
        PT.append(Analyzer())
        RT.append([])
        RT_c.append([])
        run += 1
    

if (not found):
    print("Profit-Taker run not found")
else:
    print("Profit-Taker Analyzer by ReVoltage#3425")
    print("https://github.com/revoltage34/ptanalyzer \n\n")
    for i in range(run):
        shieldDT = 0
        print("------------------------------------------------------------------------")
    
        print("Profit-Taker Run #" + str(i + 1) + " beaten in " + str(RT[i][-1]) + "s\n")

        print("Profit-Taker found in " + RT_c[i][2] + "s")
        
        temp = ""
        for t in RT_c[i][3]:
            if temp != "":
                temp += " | "
            temp += PT[i].damageType[shieldDT] + " " + str(t) + "s"
            shieldDT += 1
        print("Shield change: " + temp)
        
        temp = ""
        for t in RT_c[i][4]:
            if temp != "":
                temp += " | "
            temp += str(t) + "s"
        print("Leg break: " + temp)
        
        mins = str(int(RT[i][6]/60))
        secs = str(int(RT[i][6]%60))
        if RT[i][6]%60 < 10:
            secs = "0" + secs
        print("Body destroyed in " + RT_c[i][6] + "s [" + mins + ":" + secs + "]\n")
        
        print("4 Pylons destroyed in " + RT_c[i] [8] + "s (with ~7s pylon land delay)")
        
        temp = ""
        for t in RT_c[i][9]:
            if temp != "":
                temp += " | "
            temp += str(t) + "s"
        print("Leg break: " + temp)
        
        mins = str(int(RT[i][11]/60))
        secs = str(int(RT[i][11]%60))
        if RT[i][11]%60 < 10:
            secs = "0" + secs
        print("Body destroyed in " + RT_c[i][11] + "s [" + mins + ":" + secs + "]\n")
        
        temp = ""
        for t in RT_c[i][12]:
            if temp != "":
                temp += " | "
            temp += PT[i].damageType[shieldDT] + " " + str(t) + "s"
            shieldDT += 1
        print("Shield change: " + temp)
        
        temp = ""
        for t in RT_c[i][13]:
            if temp != "":
                temp += " | "
            temp += str(t) + "s"
        print("Leg break: " + temp)
        
        mins = str(int(RT[i][15]/60))
        secs = str(int(RT[i][15]%60))
        if RT[i][15]%60 < 10:
            secs = "0" + secs
        print("Body destroyed in " + RT_c[i][15] + "s [" + mins + ":" + secs + "]\n")
        
        print("6 Pylons destroyed in " + RT_c[i] [17] + "s (with ~7s pylon land delay)")
        
        temp = ""
        for t in RT_c[i][18]:
            if temp != "":
                temp += " | "
            temp += PT[i].damageType[shieldDT] + " " + str(t) + "s"
            shieldDT += 1
        print("Shield change: " + temp)
        
        temp = ""
        for t in RT_c[i][19]:
            if temp != "":
                temp += " | "
            temp += str(t) + "s"
        print("Leg break: " + temp)
        
        mins = str(int(RT[i][22]/60))
        secs = str(int(RT[i][22]%60))
        if RT[i][22]%60 < 10:
            secs = "0" + secs
        print("Body destroyed in " + str(round(float(RT_c[i][22]), 3)) + "s [" + mins + ":" + secs + "]")
        
        print("------------------------------------------------------------------------\n\n")
    
input('Press ENTER to exit..')