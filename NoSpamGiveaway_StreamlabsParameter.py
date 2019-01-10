import sys
import clr
clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")
import os
import json
import codecs
import shutil
import errno
from random import SystemRandom
from datetime import datetime

ScriptName = "No Spam Giveaway"
Website = "https://sehales.net/"
Description = "The parameter selects a random winner and saves usernames, prizes and times of winning to a csv file.\nFiles: Chatbot\\Services\\Scripts\\Data\\ winners.csv, users.txt"
Creator = "Sehales"
Version = "2.0.0"


sysRandom = SystemRandom()
#File to store all users who have been picked already to ensure winners winning only once
dataFolder = os.path.join(os.path.dirname(__file__), "data/")
blacklistFile = os.path.join(dataFolder, "blacklist.txt")
userListFile = os.path.join(dataFolder, "users.txt")
winnerListFile = os.path.join(dataFolder, "winners.csv")
settingsFile = os.path.join(dataFolder, "settings.json")

class Settings(object):
    def __init__(self, settingsfile=None):
        """ Load saved settings from file if available otherwise set default values. """
        try:
            with codecs.open(settingsfile, encoding="utf-8", mode="r") as f:
                self.__dict__ = json.load(f, encoding="utf-8")
        except:
                Parent.Log("NSG", "Couldn't load settings. Using default values.")
                self.parameter = "$nsgUser"
                self.last_parameter = "$lastNsgUser"
                self.unique_users = True
                self.remove_moderators = True
                Parent.Log("NSG", str(self.__dict__))

    def reload(self, jsondata):
        """ Reload settings from AnkhBot user interface by given json data. """
        self.__dict__ = json.loads(jsondata, encoding="utf-8")

#External
def Init():
    global ruuSettings
    ruuSettings = Settings(settingsFile)
    global lastUser
    lastUser = ""
    #just making sure the directory and file exist
    try:
        if not os.path.isdir(dataFolder):
            os.makedirs(dataFolder)

        codecs.open(userListFile, encoding="utf-8", mode="a").close()
        codecs.open(blacklistFile, encoding="utf-8", mode="a").close()
        codecs.open(winnerListFile, encoding="utf-8", mode="a").close()
    except:
        Parent.Log("NSG", "Unexpected error: " + str(sys.exc_info()))
        raise


#External
def Parse(parseString,user,target,message):
    Parent.Log("NSG", parseString + " - " + user + " - " + target + " - " + message)
    global ruuSettings
    if ruuSettings.parameter in parseString:
        parseString = parseString.replace(ruuSettings.parameter, getRandomUniqueActiveUser(message))

    if ruuSettings.last_parameter in parseString:
        global lastUser
        parseString = parseString.replace(ruuSettings.last_parameter, lastUser)

    return parseString


#External
def ReloadSettings(jsonData):
    global ruuSettings
    ruuSettings.reload(jsonData)
    Parent.Log("NSG", "Reloaded settings!")


def getRandomUniqueActiveUser(message):
    global ruuSettings
    saveUnique = True
    activeUsers = Parent.GetActiveUsers()
    blacklist = readBlacklist()

    userList = None
    if ruuSettings.unique_users:
        savedUsers = readSavedUserList()
        userList = [x for x in activeUsers if not isStaff(x) and x not in blacklist and x not in savedUsers]
    else:
        userList = [x for x in activeUsers if not isStaff(x) and x not in blacklist]

    #check if any users are left, otherwise just pick a lucky winner from the original list
    if len(userList) == 0:
        userList = activeUsers
        Parent.Log("NSG", "Warning: no unique active users left; picked random user!")
        saveUnique = False

    index = sysRandom.randint(0,len(userList)-1)
    userString = userList[index]

    #Save only if a unique winner was picked
    if saveUnique:
        saveUser(userString)

    saveWinner(userString,message)
    global lastUser
    lastUser = userString
    return userString

# Check if the user is a staff member
def isStaff(userString):
    global ruuSettings
    if Parent.HasPermission(userString, "Caster", "") or (ruuSettings.remove_moderators and Parent.HasPermission(userString, "Moderator", "")):
        Parent.Log("NSG", "Removed staff user %s from draw" % userString)
        return True
    return False


# Reads and returns the list of users who have been chosen already
def readSavedUserList():
    try:
        with codecs.open(userListFile, encoding="utf-8", mode="r") as f:
            users = f.read().splitlines()
    except:
        Parent.Log("NSG", "Unexpected error: " + str(sys.exc_info()))
        raise
    return users


# Reads and returns the list of users who have been chosen already
def readBlacklist():
    try:
        with codecs.open(blacklistFile, encoding="utf-8", mode="r") as f:
            blacklist = f.read().splitlines()
    except:
        Parent.Log("NSG", "Unexpected error: " + str(sys.exc_info()))
        raise
    return blacklist


# Save a chosen user to avoid any appearance in a future draw
def saveUser(userString):
    try:
        with codecs.open(userListFile, encoding="utf-8", mode="a") as f:
            f.write("%s\n" % userString)
    except:
        Parent.Log("NSG", "Unexpected error: " + str(sys.exc_info()))
        raise


#save winner to the given file
def saveWinner(userString, message):
    try:
        with codecs.open(winnerListFile, encoding="utf-8", mode="a") as f:
            f.write("%s,%s,%s\n" % (userString, message, datetime.now().strftime("%Y%m%d-%H_%M_%S")))
    except:
        Parent.Log("NSG", "Unexpected error: " + str(sys.exc_info()))
        raise


def resetUniqueUsers():
    try:
        with codecs.open(userListFile, encoding="utf-8", mode="r+") as f:
            f.truncate(0)
            Parent.Log("NSG", "Unique users reset")
    except:
        Parent.Log("NSG", "Unexpected error: " + str(sys.exc_info()))
        raise


def rotateWinnersFile():
    try:
        newFile = os.path.join(dataFolder, "winners_%s.csv" % datetime.now().strftime("%Y%m%d-%H_%M_%S"))
        shutil.move(winnerListFile, newFile)
        wf = codecs.open(winnerListFile, encoding="utf-8", mode="a")
        wf.close()
        Parent.Log("NSG", "Winners file backup: " + newFile)
    except:
        Parent.Log("NSG", "Unexpected error: " + str(sys.exc_info()))
        raise


def openFolder():
    try:
        os.startfile(dataFolder)
    except:
        Parent.Log("NSG", "Unexpected error: " + str(sys.exc_info()))
        raise


def openWinners():
    try:
        os.startfile(winnerListFile)
    except:
        Parent.Log("NSG", "Unexpected error: " + str(sys.exc_info()))
        raise


def openUnique():
    try:
        os.startfile(userListFile)
    except:
        Parent.Log("NSG", "Unexpected error: " + str(sys.exc_info()))
        raise


def openBlacklist():
    try:
        os.startfile(blacklistFile)
    except:
        Parent.Log("NSG", "Unexpected error: " + str(sys.exc_info()))
        raise