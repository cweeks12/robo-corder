import sys #To get input from the console
import time # To implement waits
import Adafruit_PCA9685 # PWM Drivers

### There are three systems.
### Hole 7 is its own system, controlled by the breath boolean
### The front 7 are controlled by one system
### The back hole is its own system that switches as needed

#Dictionary containing available notes. Currently, Low C# and D# are unavailable
#with my hardware setup. I didn't think it necessary to include them, because
#they add a lot of complication for little satisfaction and use

# I know these look weird, but the pattern is as follows: H means high, # means sharp, B means flat.
# I put them in all caps to ease the music writing process

#These are the servo numbers hooked up to each hole

#  ------|  |--------------------------------------
# |   _   --    6    5    4    3    2    1    0   |  8 IS HALF ON BACK
# |  |7|        O    O    O    O    O    O    O   |  9 IS FULL ON BACK
# |   -   --   MSB                           LSB  |
#  ------|  |--------------------------------------

# Front hole patterns for each note. 1 is closed, 0 is open
frontSevenBitmaps = dict([('C', 0b1111111), ('C#', 0b1111111), ('DB', 0b1111111), # C#, Db not functional in the current config
                ('D', 0b1111110), ('D#', 0b1111110), ('EB', 0b1111110), # D#, Eb also not functional
                ('E', 0b1111100), ('F', 0b1111000), ('F#', 0b1110111),
                ('GB', 0b1110111), ('G', 0b1110000), ('G#', 0b1101110),
                ('AB', 0b1101110), ('A', 0b1100000), ('A#', 0b1011000),
                ('BB', 0b1011000), ('B', 0b1000000), ('HC', 0b0100000),
                ('HC#', 0b1100000), ('HDB', 0b1100000), ('HD', 0b0100000),
                ('HD#', 0b0111110), ('HEB', 0b0111110), ('HE', 0b1111100),
                ('HF', 0b1111000), ('HF#', 0b1110101), ('HGB', 0b111010),
                ('HG', 0b1110000), ('HG#', 0b1110111), ('HAB', 0b1110111),
                ('HA', 0b1100000), ('HA#', 0b1101110), ('HBB', 0b1101110),
                ('HB', 0b1101100), ('SHC', 0b1001100)])

# 0 corresponds to open hole, 1 is closed, 2 is half open
# Values for back hole
backHoleValues = dict([('C', 1), ('C#', 1), ('DB', 1), # C#, Db not functional in the current config
                ('D', 1), ('D#', 1), ('EB', 1), # D#, Eb also not functional
                ('E', 1), ('F', 1), ('F#', 1),
                ('GB', 1), ('G', 1), ('G#', 1),
                ('AB', 1), ('A', 1), ('A#', 1),
                ('BB', 1), ('B', 1), ('HC', 1),
                ('HC#', 0), ('HDB', 0), ('HD', 0),
                ('HD#', 0), ('HEB', 0), ('HE', 2),
                ('HF', 2), ('HF#', 2), ('HGB', 2),
                ('HG', 2), ('HG#', 2), ('HAB', 2),
                ('HA', 2), ('HA#', 2), ('HBB', 2),
                ('HB', 2), ('SHC', 2)])

pwm = Adafruit_PCA9685.PCA9685() # New PWM Instance
pwm.set_pwm_freq(60) #Good for Servos

CLOSED_VALUE = 150 # Constant to set width of pulse
OPEN_VALUE = 600 # Width Constant

def FingerClose(holeNo):
    pwm.set_pwm(holeNo, 0, CLOSED_VALUE)
    return

def FingerOpen(holeNo):
    pwm.set_pwm(holeNo, 0, OPEN_VALUE)
    return


# Function to set the front holes
# A binary array gets passed to this function
def FrontHoleRegisterSet(HoleValues):
    for i in range(7): # Pushes the bit back one step at a time to see if it's set
        if(0b1<<i & HoleValues): # If it is set
            FingerClose(i) # Close the hole
        else: 
            FingerOpen(i) # If it's not, leave it shut

# Sets the back hole so that they don't smash into each other
def BackHoleRegisterSet(current, newvalue):
    
    waitingConstant = .15
    
    if(current == newvalue): # If you don't have to change
        return current# Don't
    
    elif(current == 0): # If it's not closed
        FingerClose(newvalue+7) # Go ahead and close it
        current = newvalue # Set the new value
        # It's +7 because the servo numbers are 7 above what the values say
        # 1 is fully closed, but it's servo number 8
        
    # If it is to be open
    elif(newvalue == 0):
        FingerOpen(current+7) # Open whatever is closed
        current = 0
        
    # The program gets here only if the hole isn't open and doesn't want to be
    elif(current == 1):
        FingerOpen(8) # Open the closed
        time.sleep(waitingConstant)
        FingerClose(9) # Close the open
        current = 2 # Set a new one
    
    # And this is the opposite 
    elif(current == 2):
        FingerOpen(9) # Open the closed
        time.sleep(waitingConstant)
        FingerClose(8) # Close the open
        current = 1 # Change the value
    
    return current
    
# Variable to track where the hole is right now
BackHoleCurrentValue = 1
tempo = 0 #Variable that stands in for my function on the pi
breath = False #Determines whether or not there is a break between notes
firstline = True #Used to determine where the top line is
rest = False # Used to determine whether the last note was a rest

##### INITIAL CONDITIONS #####
for i in range(7):
    FingerClose(i)

#Open the music file
with open(sys.argv[1], "r") as music:
    for line in music: # Pull one line at a time

        if(firstline): #If it's the first line
            print "\n\nNow playing: " + line #Tell what the song name is
            firstline = False #Then make sure nothing else is the first line
            continue #Then skip to the next line

        #These are used to mark convenient breaks in the music and are not used for anything
        if(line[0] == '-' or line[0].isspace()):
            print '' #Print an endline
            continue # Just skip it

        if(line[0].isdigit()): #If the first character is a digit
            tempo = int(line) #Set the tempo
            print "Tempo: " + str(tempo) + " bpm\n"
            continue #Then skip to the next line

        #Check to see if there is a breath
        if ('-' in line): # If you find a dash
            breath = True # Take a break
        else: # If you don't
            breath = False # Don't

        # Runs through the line until it finds a digit
        i = 0 # Resets variables
        note = ''# Name of the note

        # Go until you see that there is a digit, or an endline gets the letters
        #T his grabs the name of the note
        while(not line[i].isdigit() and not line[i].isspace()):
            note += line[i].upper() # Builds the name of the note
            i += 1

        # Reset length of note
        length = ''
        while(line[i].isdigit() or line[i] == '.'): # Get anything that's a decimal or digit
            length += line[i] #Add slowly
            i += 1

        # Testing and it WORKS!!!
        print "Note: " + note + " Beats: " + length + " Break: %s" % ("Yes" if breath else "No")
        
        if (note == "REST"): # If they want a rest
            FingerClose(7) # Give them a rest
            time.sleep(float(length)*60/tempo) # For however long they want it
            rest = True # Tell everyone else
            continue # And move on to the next note

        #Iterate over the note names
        for key in frontSevenBitmaps:
            if (key == note): # If you find the name you're looking for
                FrontHoleRegisterSet(frontSevenBitmaps[key]) #Set the front holes
                BackHoleRegisterSet(BackHoleCurrentValue, backHoleValues[key]) # Set the back hole
                if (rest): # If the last one was a rest
                    FingerOpen(7) # Stop the rest
                
        delay = float(float(length)/float(tempo)*60) # This calculates the seconds the note should play
        breathtime = float(1/float(tempo)*60*float(length)*.25)
        
        #If you take a breath and you're not already closed on a rest
        if(breath and note != "REST"):
            delay -= breathtime # Cut some time off the note

        if (delay <= 0): # If the note is too short
            continue # Skip the breath
            
        #Hold it for how long you need to    
        time.sleep(delay)
        
        # Then put the break in
        if(breath):
            FingerClose(7) # Close the hole
            time.sleep(breathtime) # Wait
            FingerOpen(7) # Open the hole
            
    
        
