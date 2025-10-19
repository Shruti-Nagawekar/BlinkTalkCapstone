import cv2
import dlib
import numpy as np
import time
import random
import math
import os
import json
from scipy.spatial import distance as dist
from SharedFrame import FrameInstance

class BlinkToMorse:

    def __init__(self):

        # Face & Eye Detection Setup
        self.FrameInstance = FrameInstance
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
        self.LeftEyeIndex = (42, 48)
        self.RightEyeIndex = (36, 42)
        self.SequenceIndex = 0

        # EMPTY MORSE SEQUENCE LIST
        self.MorseSequence = []

        # LISTS FOR RECORDING UNIT DURATIONS AS THEY OCCUR
        self.DitTimes = []
        self.DahTimes = []
        self.IntraTimes = []
        self.InterTimes = []
        self.WordTimes = []

        # LISTS FOR RECORDING UNIT AVERAGES FOR EACH TEST
        if not hasattr(self, "DitTimeAvgList"):
            self.DitTimeAvgList = []
            self.DahTimeAvgList = []
            self.IntraTimeAvgList = []
            self.InterTimeAvgList = []
            self.WordTimeAvgList = []
        
        # TIMERS
        self.BlinkTimer = 0
        self.PauseTimer = 0

        # RUNNING TOTAL TIME TRACKING VARIABLES
        self.DitTimeTtl = 0
        self.DahTimeTtl = 0
        self.InterTimeTtl = 0
        self.IntraTimeTtl = 0
        self.WordTimeTtl = 0

        # RUNNING TOTAL UNIT INSTANCE COUNT 
        self.DitCnt = 0
        self.DahCnt = 0
        self.IntraPauseCnt = 0
        self.InterPauseCnt = 0
        self.WordPauseCnt = 0

        # INITIALIZING AVERAGE VARIABLES
        self.DitTimeAvg = 0
        self.DahTimeAvg = 0
        self.IntraTimeAvg = 0
        self.InterTimeAvg = 0
        self.WordTimeAvg = 0

        # INITIALIZING VARIABLES FOR FINAL THRESHOLD SETTINGS
        self.FinalDitAvg = 0
        self.FinalDahAvg = 0
        self.FinalIntraAvg = 0
        self.FinalInterAvg = 0
        self.FinalWordAvg = 0
        self.FinalDitStdDev = 0
        self.FinalDahStdDev = 0
        self.FinalIntraStdDev = 0
        self.FinalInterStdDev = 0
        self.FinalWordStdDev = 0

        # FINAL SETTINGS
        self.DitMax = 0
        self.DahMin = 0
        self.DahMax = 0
        self.IntraMax = 0
        self.InterMin = 0
        self.InterMax = 0
        self.WordMin = 0

        # Initialize FSM to default (wait) state
        self.state = 1  

        # STORE MORSE CODE DICTIONARY INSIDE CLASS
        self.CharToMorseDictionary = {
            "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
            "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
            "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
            "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
            "Y": "-.--", "Z": "--..", " ": "/"
        }

        self.MorseToCharDictionary = { 
            ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F",
            "--.": "G", "....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
            "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R",
            "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
            "-.--": "Y", "--..": "Z", "/": " "
        }

        self.StringOut = ''



    
    def EAR(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)


    def CalculateEAR(self, shape):
        
        LeftEye = shape[self.LeftEyeIndex[0]:self.LeftEyeIndex[1]]
        RightEye = shape[self.RightEyeIndex[0]:self.RightEyeIndex[1]]

        LeftEAR = self.EAR(LeftEye)
        RightEAR = self.EAR(RightEye)

        return (LeftEAR + RightEAR) / 2.0


    def FreshFrame(self):
        
        # store current frame from CurrentFrame object
        frame = self.FrameInstance.get()
        if frame is None:
            return None, None, None  

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray, 0)

        if len(faces) > 0:
            face = faces[0]
            landmarks = self.predictor(gray, face)
            shape = np.array([[p.x, p.y] for p in landmarks.parts()])
            return frame, gray, shape

        return None, None, None


    def PhraseToMorse(self, TestPhrase):

        # split TestPhrase into seperated words list
        WordsList = TestPhrase.upper().split()

        WordCount = len(WordsList)
        WordIndex = 0

        # for each word in the word list
        for word in WordsList:
            # for each character in the current word
            for character in word:
                # if the character exists in the morse dictionary
                if character in self.CharToMorseDictionary:
                    # retrieve the corresponding morse symbol sequence
                    CurrentCharacter = self.CharToMorseDictionary[character]

                    # for each unit that appears in the current mapped character
                    for unit in CurrentCharacter:
                        # append the morse sequence with that unit
                        self.MorseSequence.append(unit)
                        # append an intra-space character after each real unit
                        self.MorseSequence.append("_")
                    # pop the final hanging intra-space character unit from the sequence
                    self.MorseSequence.pop()
                    # append an inter-character space unit after every symbol for current character is appended     
                    self.MorseSequence.append(" ")
            # pop the final hanging inter-character space
            self.MorseSequence.pop()
            # after going through each character in the word, if the word index is less than the word count
            if WordIndex < WordCount - 1:
                # append a word space
                self.MorseSequence.append("/")
            # incrimint the word index variable
            WordIndex += 1
        # return the morse sequence after every word has been iterated through
        return self.MorseSequence


    def TestingFSM(self):

        # if MorseSequence does not have any attributes break
        if not hasattr(self, "MorseSequence"):
            print("Error: MorseSequence is not set.")
            return  

        print("\n **Blink Detection Started**")
        print(f" **Blink Threshold: EAR < 0.22 | Pause Threshold: EAR > 0.28**")

        # while the sequence index is less than the length of the morse sequence
        while self.SequenceIndex < len(self.MorseSequence):
            # grab fresh frame
            frame, gray, shape = self.FreshFrame()
            # if no frame detected, try again
            if frame is None:
                continue  

            # capture current time
            CurrentTime = time.time()
            # calcualte average ear value for the current frame
            AverageEAR = self.CalculateEAR(shape)

            # store the current expected unit in the morse sequence in ExpectedUnit
            ExpectedUnit = self.MorseSequence[self.SequenceIndex]
            print(f"\n FSM State: {self.state} | Current Morse Unit: {ExpectedUnit} | EAR: {AverageEAR:.3f}")


            # *STATE 1: Waiting for Blink*
            if self.state == 1:

                # when the AveragEAR crosses blink detect threshold
                if AverageEAR < 0.25:
                    # incriment blink frame count
                    self.BlinkFrameCount += 1
                else:
                    # reset the BlinkFrameCount if false blink
                    self.BlinkFrameCount = 0 

                # if blink is detected for three frames
                if self.BlinkFrameCount >= 1:
                    # store current time in blink timer
                    self.BlinkTimer = CurrentTime
                    # transition to state 2
                    self.state = 2
                    print(f"️ Blink Detected! EAR: {AverageEAR:.3f}, Time: {CurrentTime:.3f}")

                    
            # *STATE 2: Blink Holding (Waiting for Eyes to Open)*
            elif self.state == 2:

                # wait for person to end blink by exceeding threshold
                if AverageEAR > 0.28 and self.BlinkTimer is not None:
                    # calculate blink duration
                    BlinkDuration = CurrentTime - self.BlinkTimer
                    # reset blink timer
                    self.BlinkTimer = None
                    # reset blink frame counter
                    self.BlinkFrameCounter = 0
                    print(f" Blink Duration: {BlinkDuration:.3f} sec")

                    # classify blink as Dit or Dah
                    if ExpectedUnit == ".":
                        print(" Detected Dit:", ExpectedUnit)
                        # append BlinkDuration to Dit times list
                        self.DitTimes.append(BlinkDuration)
                        # add to the dit time total
                        self.DitTimeTtl += BlinkDuration
                        # incriment the dit count
                        self.DitCnt += 1
                        self.SequenceIndex += 1

                    elif ExpectedUnit == "-":
                        print(" Detected Dah:", ExpectedUnit)
                        # append BlinkDuration to Dah times list
                        self.DahTimes.append(BlinkDuration)
                        # add the blink duration to the dah time total
                        self.DahTimeTtl += BlinkDuration
                        # incriment the dah count
                        self.DahCnt += 1
                        self.SequenceIndex += 1

                    # store current time in pause timer
                    self.PauseTimer = CurrentTime
                    # transition to state 3
                    self.state = 3
                else:
                    print("waiting for eyes to open")


            # *STATE 3: Detecting Pause (Character or Word Space)*
            elif self.state == 3:
                # when the AveragEAR crosses blink detect threshold
                if AverageEAR < 0.25:
                    # incriment the blink frame counter
                    self.BlinkFrameCount += 1
                else:
                    # otherwise reset the blink frame count
                    self.BlinkFrameCount = 0
                    print("Waiting for Blink Detection")

                # if the blink frame count is and pause timer holds a value
                if self.BlinkFrameCount >= 1 and self.PauseTimer is not None:
                    #calculate pause duration
                    PauseDuration = CurrentTime - self.PauseTimer
                    # reset pause timer
                    self.PauseTimer = None
                    print(f" Pause Duration: {PauseDuration:.3f} sec")

                    # classify as appropriate type of pause
                    if ExpectedUnit == "_":
                        print(" Expected Intra-Space:", ExpectedUnit)
                        # append PauseDuration to Intra-Space Chararacter times list
                        self.IntraTimes.append(PauseDuration)
                        self.IntraTimeTtl += PauseDuration
                        self.IntraPauseCnt += 1
                        self.SequenceIndex += 1
                    
                    elif ExpectedUnit == " ":
                        print(" Expected Character Space:", ExpectedUnit)
                        # append PauseDuration to Inter-Space Chararacter times list
                        self.InterTimes.append(PauseDuration)
                        self.InterTimeTtl += PauseDuration
                        self.InterPauseCnt += 1
                        self.SequenceIndex += 1
                        
                    elif ExpectedUnit == "/":
                        print(" Expected Word Space:", ExpectedUnit)
                        # append PauseDuration to Intra-Space Chararacter times list
                        self.WordTimes.append(PauseDuration)
                        self.WordTimeTtl += PauseDuration
                        self.WordPauseCnt += 1
                        self.SequenceIndex += 1

                    # store current time in blink timer
                    self.BlinkTimer = CurrentTime
                    # transtion to state 2
                    self.state = 2   

            # display the current captured frame
            cv2.imshow("Blink Detection", frame)
            # if the q key is pressed exit message and break from while loop
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n Exiting Blink Detection Mode...")
                break

        # release camera memory space 
        self.capture.release()
        # destroy widows
        cv2.destroyAllWindows()
        

    def CalculateAverages(self):

        if self.DitCnt > 0:
            self.DitTimeAvg = self.DitTimeTtl / self.DitCnt
        self.DitTimeAvgList.append(self.DitTimeAvg)   

        if self.DahCnt > 0:
            self.DahTimeAvg = self.DahTimeTtl / self.DahCnt
        self.DahTimeAvgList.append(self.DahTimeAvg)

        if self.IntraPauseCnt > 0:
            self.IntraTimeAvg = self.IntraTimeTtl / self.IntraPauseCnt
        self.IntraTimeAvgList.append(self.IntraTimeAvg)
        
        if self.InterPauseCnt > 0:
            self.InterTimeAvg = self.InterTimeTtl / self.InterPauseCnt
        self.InterTimeAvgList.append(self.InterTimeAvg)
        
        if self.WordPauseCnt > 0:
            self.WordTimeAvg = self.WordTimeTtl / self.WordPauseCnt
        self.WordTimeAvgList.append(self.WordTimeAvg)
        
        print("\n **New Timing Averages Calculated** ")
        print(f"Dit Avg: {self.DitTimeAvg:.3f} sec")
        print(f"Dah Avg: {self.DahTimeAvg:.3f} sec")
        print(f"Intra-Character Pause Avg: {self.IntraTimeAvg:.3f} sec")
        print(f"Inter-Character Pause Avg: {self.InterTimeAvg:.3f} sec")
        print(f"Word Pause Avg: {self.WordTimeAvg:.3f} sec\n\n")
        print(f"Dit Time Recordings: {self.DitTimes:} sec\n\n")

    
    def StandardDeviation(self, mean, DurationsList):

        # initialize necessarry variables
        DistanceFromMean = 0
        SummationSquaredDFM = 0
        # loop to cyle throught the entirety of the durations list
        for i in range(len(DurationsList)):
            # take absolute value of the current durations distance from the mean
            DistanceFromMean = abs(DurationsList[i] - mean)
            # square the distance from mean and add to running summation
            SummationSquaredDFM = SummationSquaredDFM + (DistanceFromMean * DistanceFromMean)    
        # calculate variance 
        variance =  SummationSquaredDFM / len(DurationsList)
        # calculate standard deviation
        StandardDeviation = math.sqrt(variance)
        # return standard deviation
        return StandardDeviation


    def TestSegment(self, TestPhrase):
        
        print("Current Test Phrase: ", TestPhrase)
        self.MorseSequence = self.PhraseToMorse(TestPhrase)
        print(self.MorseSequence)
        self.SequenceIndex = 0
        UserInput = 0
        while (UserInput != 1):
           UserInput = int(input("Please enter 1 to start: "))
        self.TestingFSM()
        self.CalculateAverages()


    def DetermineValidity(self, ListOne, ListTwo, ListThree, ListFour):

       # create dictionary to store data according to its unit
       ValidityDict = {
           "Dah" : (ListTwo, self.DahTimeAvgList),
       }

       # initialize coorisponiding dictionaries for count and flag variables
       ValidCounts = {unit: 0 for unit in ValidityDict}
       UnitFlags = {unit: 0 for unit in ValidCounts}

       print("\n--- Debug: Checking Standard Deviations Against Corresponding Averages ---")

       # iterate through each unit in the validity dictionary
       for unit in ValidityDict:
           # unpack lists into individual variables for the current unit 
           UnitStdDevList, UnitAvgTimeList = ValidityDict[unit]
           # initialize counter
           count = 0

           print(f"\nChecking Unit: {unit}")
           # tuple standard deviation and average time for current iteration of current unit
           for i, (StdDev, AvgTime) in enumerate(zip(UnitStdDevList, UnitAvgTimeList)):
               print(f"  Iteration {i+1}: StdDev = {StdDev:.6f}, AvgTime = {AvgTime:.6f}, Threshold = {0.3 * AvgTime:.6f}")
               # if the standard deviation is less than 30% of the average time
               if StdDev < (0.3 * AvgTime):
                   # incriment count
                   count += 1
           # store count in ValidCounts dictionary with corresponding unit
           ValidCounts[unit] = count
           print(f"Final Valid Count for {unit}: {ValidCounts[unit]}")

       # print valid tests recorded for each unit
       print("\n--- Debug: Valid Counts for Each Unit ---")
       for unit, count in ValidCounts.items():
           print(f"  {unit}: {count}")
           # set flag if current unit count is not at least two
           if count < 2:
               UnitFlags[unit] = 1

       # display units requiring retest
       print("\n--- Debug: Units Requiring Retest ---")
       for unit, flag in UnitFlags.items():
           if flag == 1:
               print(f"  Retest Required for {unit}")

       # if the sum of unit flags is greater than one
       if sum(UnitFlags.values()) > 1:
           print("\nFull Retest Needed...")
           # return false and full retest
           return False

       # if only one flag, retest for individual unit
       if UnitFlags["Dah"] == 1:
           print("dah retest")

       return True

    def CalibrateThreshold(self, ListOne, ListTwo, ListThree, ListFour, ListFive):

        # create dictionary to store data according to its unit
        ValidityDict = {
            "Dit": (ListOne, self.DitTimeAvgList),
            "Dah": (ListTwo, self.DahTimeAvgList),
            "Intra": (ListThree, self.IntraTimeAvgList),
            "Inter": (ListFour, self.InterTimeAvgList),
            "Word": (ListFive, self.WordTimeAvgList)
        }

        # initialize corresponiding dictionaries for seperating averages from standard deviations 
        StdDevDict = {unit: [] for unit in ValidityDict}
        AvgDict = {unit: [] for unit in ValidityDict}

       # iterate through each unit in the validity dictionary
        for unit in ValidityDict:

            # unpack respective lists for current unit
            UnitStdDevList, UnitAvgTimeList = ValidityDict[unit]
            # extend lists to appropriate dictionary and unit location
            StdDevDict[unit].extend(UnitStdDevList)
            AvgDict[unit].extend(UnitAvgTimeList)

        print("\nRunning Lists Updated:")
        for unit in StdDevDict:
            print(f"{unit}: StdDevList = {StdDevDict[unit]}, AvgList = {AvgDict[unit]}")

        # iterate through each unit in the validity dictionary again
        for unit in ValidityDict:

            # determine length to be used to calculate averages
            length = len(AvgDict[unit])

            # make sure the lenght of the list is not zero for current unit
            if length > 0:
                # final average is the sum of every item in the averages list divided by the length 
                FinalAvg = sum(AvgDict[unit]) / length
                # final standard deviation is the sum of every item in standard deviations the list divided by the length
                FinalStdDev = sum(StdDevDict[unit]) / length

                # determine unit and assign calculated values accordingly
                if unit == "Dit":
                    self.FinalDitAvg = FinalAvg
                    self.FinalDitStdDev = FinalStdDev
                elif unit == "Dah":
                    self.FinalDahAvg = FinalAvg
                    self.FinalDahStdDev = FinalStdDev
                elif unit == "Intra":
                    self.FinalIntraAvg = FinalAvg
                    self.FinalIntraStdDev = FinalStdDev
                elif unit == "Inter":
                    self.FinalInterAvg = FinalAvg
                    self.FinalInterStdDev = FinalStdDev
                elif unit == "Word":
                    self.FinalWordAvg = FinalAvg
                    self.FinalWordStdDev = FinalStdDev

        self.DitMax = (1.5 * self.FinalDitStdDev) + self.FinalDitAvg
        self.DahMin = self.FinalDahAvg - (1.5 * self.FinalDahStdDev)
        self.DahMax = (3 * self.FinalDahStdDev) + self.FinalDahAvg
        self.IntraMax = (1.5 * self.FinalIntraStdDev) + self.FinalIntraAvg
        self.InterMin = self.FinalInterAvg - (1.5 * self.FinalInterStdDev)
        self.InterMax = (1.5 * self.FinalInterStdDev) + self.FinalInterAvg
        self.WordMin = self.FinalWordAvg - (1.5 * self.FinalWordStdDev)

        print("\nFinal Threshold Values:")
        print(f"Dit -> Final Max: {self.DitMax:.6f}")
        print(f"Dah -> Final Min: {self.DahMin:.6f}")
        print(f"Intra -> Final Max: {self.IntraMax:.6f}")
        print(f"Inter -> Final Min: {self.InterMin:.6f}")
        print(f"Inter -> Final Max: {self.InterMax:.6f}")
        print(f"Word -> Final Avg: {self.WordMin:.6f}")
        

    def SequenceGeneratorFSM(self):

        print("\n **Blink Detection Started**")
        print(f" **Blink Threshold: EAR < 0.22 | Pause Threshold: EAR > 0.28**")

        # while the sequence index is less than the length of the morse sequence
        while self.SequenceIndex == 0 or self.MorseSequence[self.SequenceIndex - 1] != '^':


            # grab fresh frame
            frame, gray, shape = self.FreshFrame()
            # if no frame detected, try again
            if frame is None:
                continue  

            # capture current time
            CurrentTime = time.time()
            # calcualte average ear value for the current frame
            AverageEAR = self.CalculateEAR(shape)


            # *STATE 1: Waiting for Blink*
            if self.state == 1:
                print(f"Default EAR: {AverageEAR:.3f}")
                # when the AveragEAR crosses blink detect threshold
                if AverageEAR < 0.25:
                    self.BlinkTimer = CurrentTime
                    # transition to state 2
                    self.state = 2
                    print(f"Blink Detected! EAR: {AverageEAR:.3f}, Time: {CurrentTime:.3f}")

                    
            # *STATE 2: Blink Holding (Waiting for Eyes to Open)*
            elif self.state == 2:
                # wait for person to end blink by exceeding threshold
                if AverageEAR > 0.28 and self.BlinkTimer is not None:
                    # calculate blink duration
                    BlinkDuration = CurrentTime - self.BlinkTimer
                    # reset blink timer
                    self.BlinkTimer = None
                    print(f" Blink Duration: {BlinkDuration:.3f} sec")

                    # classify blink as Dit or Dah
                    if BlinkDuration <= self.DitMax:
                        print(" Detected Dit:")
                        # append BlinkDuration to Dit times list
                        self.MorseSequence.append(".")
                        self.SequenceIndex += 1

                    elif BlinkDuration > self.DitMax and BlinkDuration < self.DahMin:
                        DitDifference = 0
                        DahDifference = 0
                        DitDifference = abs(BlinkDuration - self.DitMax)
                        DahDifference = abs(BlinkDuration - self.DahMin)
                        if DitDifference > DahDifference:
                            self.MorseSequence.append('-')
                            self.SequenceIndex += 1

                        else:
                            self.MorseSequence.append('.')
                            self.SequenceIndex += 1

                    elif BlinkDuration >= self.DahMin and BlinkDuration < (self.DahMax + .5):
                        print(" Detected Dah:")
                        self.MorseSequence.append('-')
                        
                        self.SequenceIndex += 1

                    elif BlinkDuration >= (self.DahMax + 1.0):
                        print("Ending Sequence Appending Process:")
                        self.MorseSequence.append("^")
                        self.SequenceIndex += 1
                        
                    # store current time in pause timer
                    self.PauseTimer = CurrentTime
                    # transition to state 3
                    self.state = 3
                else:
                    print(f"Default EAR During PAUSE Wait: {AverageEAR:.3f}")


            # *STATE 3: Detecting Pause (Character or Word Space)*
            elif self.state == 3:
                # when the AveragEAR crosses blink detect threshold
                if AverageEAR < 0.25:
                    # calculate pause duration
                    PauseDuration = CurrentTime - self.PauseTimer
                    # reset pause timer
                    self.PauseTimer = None

                    # classify as appropriate type of pause
                    if PauseDuration <= self.IntraMax:
                        print(" Expected Intra-Space:")
                        # append PauseDuration to Intra-Space Chararacter times list
                        self.MorseSequence.append('_')
                        self.SequenceIndex += 1
                    
                    elif PauseDuration > self.IntraMax and PauseDuration < self.InterMin:
                        IntraDifference = 0
                        InterDifference = 0
                        IntraDifference = abs(PauseDuration - self.IntraMax)
                        InterDifference = abs(PauseDuration - self.InterMin)
                        if IntraDifference > InterDifference:
                            self.MorseSequence.append(' ')
                            self.SequenceIndex += 1
                        else:
                            self.MorseSequence.append('_')
                            self.SequenceIndex += 1

                    elif PauseDuration >= self.InterMin and PauseDuration <= self.InterMax:
                        # append PauseDuration to Inter-Space Chararacter times list
                        self.MorseSequence.append(' ')
                        self.SequenceIndex += 1
                        
                    elif PauseDuration > self.InterMax and PauseDuration < self.WordMin:
                        InterDifference = 0
                        WordDifference = 0
                        InterDifference = abs(PauseDuration - self.InterMax)
                        WordDifference = abs(PauseDuration - self.WordMin)
                        if WordDifference > InterDifference:
                            self.MorseSequence.append(' ')
                            self.SequenceIndex += 1
                        else:
                            self.MorseSequence.append('/')
                            self.SequenceIndex += 1

                    elif PauseDuration >= self.WordMin:
                        # append PauseDuration to Word-Space Chararacter times list
                        self.MorseSequence.append('/')
                        self.SequenceIndex += 1

                    # store current time in blink timer
                    self.BlinkTimer = CurrentTime
                    # transtion to state 2
                    self.state = 2 
                else:
                    print(f"Default EAR During BLINK Wait: {AverageEAR:.3f}")
                      

            # display the current captured frame
            #cv2.imshow("Blink Detection", frame)
            # if the q key is pressed exit message and break from while loop
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n Exiting Blink Detection Mode...")
                break
            

    def MorseToEnglish(self):

        CurrentMorseEngEq = ""
        EnglishCharacters =[]

        for char in self.MorseSequence:
            if char in ['.', '-']:
                CurrentMorseEngEq += char

            elif char == "_":
                continue

            elif char == " ":
                if CurrentMorseEngEq:
                    print(f"Decoding: '{CurrentMorseEngEq}'")
                    EnglishCharacters.append(self.MorseToCharDictionary.get(CurrentMorseEngEq.strip(), "?"))
                    CurrentMorseEngEq = ""

            elif char == "/":
                if CurrentMorseEngEq:
                    print(f"Decoding: '{CurrentMorseEngEq}'")
                    EnglishCharacters.append(self.MorseToCharDictionary.get(CurrentMorseEngEq.strip(), "?"))
                    CurrentMorseEngEq = ""
                    EnglishCharacters.append(" ")

            elif char == "^":
                if CurrentMorseEngEq:
                    print(f"Decoding: '{CurrentMorseEngEq}'")
                    EnglishCharacters.append(self.MorseToCharDictionary.get(CurrentMorseEngEq.strip(), "?"))
                break

        return "".join(EnglishCharacters)
    

    def CommunicationSession(self):

        self.SequenceGeneratorFSM()
        print("Generated Morse Sequence")
        print(self.MorseSequence)
        self.StringOut = self.MorseToEnglish()

        print(f"Your Morse Phrase In English:")
        print(self.StringOut)
    
    def GetOutput(self):

        return self.StringOut if hasattr(self, "StringOut") else ""


    def SaveCalibration(self):
       
        filename = input("Enter a name to save your calibration settings: ") + ".json"

        # get the directory where the script is located
        ScriptDirectory = os.path.dirname(os.path.abspath(__file__))
    
        # construct the full path
        FilePath = os.path.join(ScriptDirectory, filename)

        CalibrationData = {
            "DitMax": self.DitMax,
            "DahMin": self.DahMin,
            "DahMax": self.DahMax,
            "IntraMax": self.IntraMax,
            "InterMin": self.InterMin,
            "InterMax": self.InterMax,
            "WordMin": self.WordMin
        }

        # write to JSON file in the same directory as the script
        with open(FilePath, 'w') as file:
            json.dump(CalibrationData, file, indent=4)

        print(f"Calibration settings saved as '{FilePath}'.")
    
    def LoadCalibration(self, SwiftString):
        FileName = SwiftString + ".json"

        # get the directory where the script is located
        ScriptDirectory = os.path.dirname(os.path.abspath(__file__))

        # construct the full path
        FilePath = os.path.join(ScriptDirectory, FileName)

        try:
            with open(FilePath, 'r') as file:
                CalibrationData = json.load(file)  

            # assign loaded values to class variables
            self.DitMax = CalibrationData["DitMax"]
            self.DahMin = CalibrationData["DahMin"]
            self.DahMax = CalibrationData["DahMax"]
            self.IntraMax = CalibrationData["IntraMax"]
            self.InterMin = CalibrationData["InterMin"]
            self.InterMax = CalibrationData["InterMax"]
            self.WordMin = CalibrationData["WordMin"]

            print(f"Calibration settings loaded from '{FilePath}'")
            print(f"FrameInstance ID in FinalBT.py: {id(FrameInstance)}")

        except FileNotFoundError:
            print(f"Error: File '{FilePath}' not found.")


if __name__ == "__main__":

    DitStdDevList = []
    DahStdDevList = []
    IntraStdDevList = []
    InterStdDevList = []
    WordStdDevList = []
    
    InstanceBT = BlinkToMorse()

    UserInput = int(input("\n Enter 1 To Test A New User: "))
    if UserInput == 1:
        with open("phrases.txt") as file:
            PhraseOptions = [phrase.strip() for phrase in file.readlines()]
        i = 0
        while i != 3:
            InstanceBT.__init__()
            x = random.randint(0,18)
            RandomPhrase = PhraseOptions[x]
            print(f"Random Test Phrase for test #{i + 1}: ", RandomPhrase)
            InstanceBT.TestSegment(RandomPhrase)
            SuccessfulTest = 0
            UserInput = int(input("\n\nSuccessful Test (1) Unsuccessful(2): "))
            if UserInput == 1:
                DitStdDevList.append(InstanceBT.StandardDeviation(self.DitTimeAvg, self.DitTimes))
                DahStdDevList.append(InstanceBT.StandardDeviation(self.DahTimeAvg, self.DahTimes))
                IntraStdDevList.append(InstanceBT.StandardDeviation(self.IntraTimeAvg, self.IntraTimes))
                InterStdDevList.append(InstanceBT.StandardDeviation(self.InterTimeAvg, self.InterTimes))
                WordStdDevList.append(InstanceBT.StandardDeviation(self.WordTimeAvg, self.WordTimes))
                i += 1
            else:
                print("Retest Activated")
        
        ValidityBool = InstanceBT.DetermineValidity(DitStdDevList, DahStdDevList, IntraStdDevList, InterStdDevList)
        if ValidityBool == True:
            print("Success")
            InstanceBT.CalibrateThreshold(DitStdDevList, DahStdDevList, IntraStdDevList, InterStdDevList, WordStdDevList)
            UserInput = int(input("\n Press 1 to Save Settings: "))
            if UserInput == 1:
                InstanceBT.SaveCalibration()
        else:
            print("false")

    
    UserInput = int(input("\n Press 1 to Load User Settings: "))
    if UserInput == 1:
        InstanceBT.__init__()
        InstanceBT.LoadCalibration()
        InstanceBT.CommunicationSession() 
    else:
        print("Communication Session Aborted")   
    