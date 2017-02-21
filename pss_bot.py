import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import discord
from discord.ext import commands
import logging
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import Levenshtein

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

search_threshold = 74

time_start=time.clock()

scope = [r'https://spreadsheets.google.com/feeds']

#os.chdir('discord_bots\\pss_bot')

credentials = ServiceAccountCredentials.from_json_keyfile_name('pss_bot.json', scope)

gc = gspread.authorize(credentials)

sheet = gc.open_by_key('1nJFO_nksOxlAW4VMgUjrqljOjKv8CKN665M72h3Jspw')

prestiges = {} #Dictionary containing all prestige information

hero = sheet.worksheet("Legendary-PWW link").get_all_values() #singular indicates sheet name
epic = sheet.worksheet("Heroes-PWW link").get_all_values()
unique = sheet.worksheet("Epics-PWW link").get_all_values()

def all_names(sheet): #Assembles all names in the sheet
    return [x.lower() for x in sheet[0] if x!='']

def add_to_prestiges(name_list, source_sheet): #Adds all values in that sheet to the Prestige dictionary
    for name1 in range(1,len(name_list)+1):
        for name2 in range(1,len(name_list)+1):
            prestiges["%s_%s"%(name_list[name1-1],name_list[name2-1])]=source_sheet[name1][name2].lower()

heroes = all_names(hero) #plural indicates name list
epics = all_names(epic)
uniques = all_names(unique)
sub_hero = [x[0] for x in hero if x[0]!='']
sub_epic = [x[0] for x in epic if x[0]!='']
sub_unique = [x[0] for x in unique if x[0]!='']


add_to_prestiges(heroes,hero)
legendaries=list(set(prestiges.values()))
add_to_prestiges(epics,epic)
add_to_prestiges(uniques,unique)
all_prestige_results = sorted(set([prestiges[combo] for combo in prestiges]))

print ('Prestige data prep complete. Time Elapsed :'+str(time.clock()-time_start))

import urllib.request

def finder(target, source):
    return source[source.find(target)+len(target)+1:source.find('"',source.find(target)+len(target)+2)]

class Crew:
    def __init__(self, source, name):
        '''Crew from Pixel Starships'''
        #self.name = finder("CharacterDesignName=",source)
        self.name = name
        self.gender = finder("GenderType=",source)
        self.race = finder("RaceType=",source)
        self.hp = finder("FinalHp=",source)
        self.pilot = finder("FinalPilot=",source)
        self.attack = finder("FinalAttack=",source)
        self.fire_resistance = finder("FireResistance=",source)
        self.repair = finder("FinalRepair=",source)
        self.weapon = finder("FinalWeapon=",source)
        self.shield = finder("FinalShield=",source)
        self.engine = finder("FinalEngine=",source)
        self.research = finder("FinalResearch=",source)
        self.walking_speed = finder("WalkingSpeed=",source)
        self.running_speed = finder("RunSpeed=",source)
        self.rarity = finder("Rarity=",source)
        self.progression = finder("ProgressionType=",source)
        self.xp = finder("XpRequirementScale=",source)
        self.special_type = finder("SpecialAbilityType=",source)
        self.special = finder("SpecialAbilityFinalArgument=",source)
        self.training = finder("TrainingCapacity=",source)
        self.equipment = finder("EquipmentMask=",source)

crew={}
metrics=['name','gender','race','hp','pilot','attack','fire_resistance','repair','weapon','shield','engine','research','walking_speed','running_speed','rarity','progression','xp','special_type','special','training','equipment']
equipment_loadouts={6:'Chest and Legs', 24:'Shoulder and Hand', 5:'Head and Legs', 8:'Hand', 9:'Head and Hand', 10:'Chest and Hand', 12:'Hand and Legs', 3:'Head and Chest'}

def all_crew_values(source):
    text=source[:]
    while len(text)>0:
        if text.find(r"/CharacterDesign>")>0:
            name=(str(finder("CharacterDesignName=",text)).lower())
            crew[name]=Crew(text,str(name))
            text=text[text.find(r"/CharacterDesign>")+len(r"/CharacterDesign>")+1:]
        else:
            break
        
#pss_api=open("ListAllCharacterDesigns2.txt","r+").read()
with urllib.request.urlopen(r'http://api2.pixelstarships.com/CharacterService/ListAllCharacterDesigns2?languageKey=en') as response:
    pss_api = response.read()
pss_api = pss_api.decode("utf-8")
all_crew_values(pss_api)

def lined_string(text):
    return "```\n"+"%s\n"*len(text)%tuple(text)+"```\n"

source_check = "Feel free to check my source at"+r"https://docs.google.com/spreadsheets/d/11ZXN22CTmItPMVduRdpEwf6wR9KRMJR7Ro9HensEWSk/edit#gid=656420900 and report any errors to @DT-1236#0629"

print ('Crew data prep complete. Time Elapsed :'+str(time.clock()-time_start))

#######

description = """A bot designed to relay known information regarding Pixel Starships."""

bot = commands.Bot(command_prefix='?', description=description)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print ('Full prep complete. Time Elapsed :'+str(time.clock()-time_start))
    await bot.change_presence(game=discord.Game(name='Try ?commandlist'))
 
@bot.command(aliases=["CommandList", "Commandlist", "Command List", "command list", "commands", "Commands", "command", "Command"])
async def commandlist(*, request : str=None):
    request = process.extractOne(request, ['prestige','names','recipe','stats'])[0]
    try:
        if request=="prestige":
            await bot.say("Input: 1 crew name or 2 crew names separated by a comma. Gives result of crew prestige if known. Gives known possibilities for prestige if only 1 name is given")
        elif request=="names":
            await bot.say("Gives acceptable spelling for Hero, Epic, or Unique crew")
        elif request=="recipe":
            await bot.say("Gives known combinations which result in the given name. If 1 parent and 1 child are given, a list of other parents will be given which can produce the desired child.")
        elif request=="stats":
            await bot.say("Gives requested stats for listed crew member. Use ?stats help for more information")
    except:
        await bot.say("Try ?command with prestige, recipes, stats, or namelist")

@bot.command(aliases=["recipes", "Recipe", "Recipes"])
async def recipe(*,request : str):
    """Gives listed combinations to make single crew OR gives listed combinations including component crew member to make result crew member"""
    if request.lower()=='help' or request.lower()=='names':
        await bot.say("Names for prestige results are: "+lined_string(all_prestige_results)+"** = confirmed since December update\n# = rumored\nunmarked = NOT confirmed since December update")
        return
    if ',' in request:
        names = request.lower().split(',')
        if names[1][0] == ' ':
            names[1] = names[1][1:]
    else: #This will handle single name requests
        result=[]
        for combo in prestiges: #Find all prestige combinations that generate the request
            if fuzz.partial_ratio(request.lower(), prestiges[combo]) > search_threshold:
                result.append("%s = %s"%(([combo.title().split('_')][0]),prestiges[combo].title()))
        if result==[]:
            await bot.say("There are no recorded recipes for %s"%(request.title())+source_check)
            return
        else:
            phrase = "These combinations are listed as potentially making %s:"%request.title()+lined_string(result)+"\nConsider double checking your chosen recipe with ?prestige or the spreadsheet"+"\n** = confirmed since December update\n# = rumored\nunmarked = NOT confirmed since December update"
            while len(phrase) > 1950:
                await bot.say(phrase[:phrase.find('[',1800)]+"```")
                phrase = "```"+phrase[phrase.find('[',1800):]
            await bot.say(phrase)
            return
    result=[]
    for combo in prestiges:#This tree will handle prospective parent/child combinations
        if fuzz.partial_ratio(names[0], prestiges[combo]) > search_threshold: #names[0] is the child/product here. This yields a list of all recipes making the child/product
            result.append("%s = %s"%(([combo.title().split('_')][0]),prestiges[combo])) #entries in result will be the full combination
    result = [x for x in result if fuzz.partial_ratio(names[1],x) > search_threshold]#Take only entries which contain the parent/reagent, names[1]    
    if not result:#If no entries contained the prevoius parent/reagent, names[1]...
        for combo in prestiges:#try it the other way around with names[1] as the child/product
            if fuzz.partial_ratio(names[1], prestiges[combo]) > search_threshold: #names[1] is the child here
                result.append("%s = %s"%(([combo.title().split('_')][0]),prestiges[combo]))
        result = [x for x in result if fuzz.partial_ratio(names[0],x) > search_threshold]#Take only entries which contain the parent/reagent, names[0]
        if not result:
            await bot.say("I see no relation between %s and %s"%(names[0].title(),names[1].title())+source_check)
            return
        else:
            phrase = "According to records, pertinent combinations between %s and %s are as follows:"%(names[0].title(),names[1].title())+lined_string(sorted(set([x.title() for x in result])))+"Remember, only Legendary combinations are guaranteed by Savy\nAdditionally, fuzzy searching is imperfect, so double check your results with ?prestige or with the spreadsheet"
            while len(phrase) > 1950:
                await bot.say(phrase[:phrase.find('[',1800)]+"```")
                phrase = "```"+phrase[phrase.find('[',1800):]
            await bot.say(phrase)
            return
    else:
        phrase = "According to records, pertinent combinations between %s and %s are as follows:"%(names[0].title(),names[1].title())+lined_string(sorted(set([x.title() for x in result])))+"Remember, only Legendary combinations are guaranteed by Savy\nAdditionally, fuzzy searching is imperfect, so double check your results with ?prestige or with the spreadsheet"
        while len(phrase) > 1950:
                await bot.say(phrase[:phrase.find('[',1800)]+"```")
                phrase = "```"+phrase[phrase.find('[',1800):]
        await bot.say(phrase)
        return
    
@bot.command(aliases=["names"])
async def namelist(request : str=''):
    """returns a list of valid names"""
    if request.lower()=='legendary' or request.lower()=='legendaries' or request.lower()=='legend':
        await bot.say('The following is a list of all known names of Legendary Crew. I will likely only understand names that are typed as follows:')
        await bot.say(legendaries)
    elif request.lower()=='hero' or request.lower()=='heroes':
        await bot.say('The following is a list of all known names of Hero Crew. I will likely only understand names that are typed as follows:')
        await bot.say(heroes)
    elif request.lower()=='epic' or request.lower()=='epics':
        await bot.say('The following is a list of all known names of Epic Crew. I will likely only understand names that are typed as follows:')
        await bot.say(epics)
    elif request.lower()=='unique' or request.lower()=='uniqes':
        await bot.say('The following is a list of all known names of "Unique" Crew. I will likely only understand names that are typed as follows:')
        await bot.say(uniques)
    else:
        await bot.say('Valid inputs include hero, epic, or unique')

@bot.command(aliases=["Prestige"])
async def prestige(*,request : str):
    """Returns data on prestige results for the two crew members entered as input"""
    if ',' in request:
        names = request.lower().split(',')
    else: #If there's only one name, this tree will handle it. It will try to give all receipes for the one crew member
        if process.extractOne(request, sub_hero+sub_epic+sub_unique, scorer=fuzz.partial_ratio)[1] > search_threshold:
            crew = process.extractOne(request, sub_hero+sub_epic+sub_unique, scorer=fuzz.partial_ratio)[0]
        else:
            await bot.say("Unrecognized or the crew is not hero, epic, or unique")
            return
        if crew in sub_hero: #blocks beneath will return the list which has the target in the 0th position, a column or row in the spreadsheet
            result = sorted(set([x for x in hero if x[0]==crew][0][1:]))
        elif crew in sub_epic: 
            result = sorted(set([x for x in epic if x[0]==crew][0][1:]))
        elif crew in sub_unique: 
            result = sorted(set([x for x in unique if x[0]==crew][0][1:]))
        if result==set():
            await bot.say("There are no known recipes including %s"%crew+source_check)
            return
        else:
            phrase = "%s was parsed to mean \"%s\" who is listed as being used in:"%(request,crew)+lined_string(result)+"** = confirmed since December update\n# = rumored\nunmarked = NOT confirmed since December update"
            while len(phrase) > 1950:
                await bot.say(phrase[:phrase.find('[',1800)]+"```")
                phrase = "```"+phrase[phrase.find('[',1800):]
            await bot.say(phrase)
            return
    key_1 = process.extractOne(request,prestiges.keys(),scorer=fuzz.partial_ratio)[0]
    if prestiges[key_1]:
        result_1 = prestiges[key_1].title()
    else:
        result_1 = "Unlisted"
    key_2 = process.extractOne(names[1]+names[0],prestiges.keys(),scorer=fuzz.partial_ratio)[0]
    if prestiges[key_2]:
        result_2 = prestiges[key_2].title()
    else:
        result_2 = "Unlisted"
    phrase = "%s was parsed as %s which yields:```\n%s```\n%s yields:\n```\n%s```"%(request,key_1,result_1,key_2,result_2)+"** = confirmed since December update\n# = rumored\nunmarked = NOT confirmed since December update"
    await bot.say(phrase)

@bot.command(aliases=["Stats", 'stat', 'Stat'])
async def stats(*,request : str):
    """Provides stat readouts for requested crew"""
    initial_request = request
    if request.lower()=='help':
        await bot.say("Give a crew name or a crew name and a stat separated by a comma. All stats will be given if no specific stat is provided. Valid names can be found with ?stat names. Valid stats are ```gender, race, hp, pilot, attack, fire_resistance, repair, weapon, shield, engine, research, walking_speed, running_speed, rarity, progression, xp, special_type, special, training, and equipment.```")
        return
    if request.lower()=='equip' or request.lower()=='equipment':
        await bot.say("```%s```"%(equipment_loadouts))
        return
    if request.lower()=='names':
        await bot.say("Valid names are: ```%s```"%(crew.keys()))
        return
    if ',' in request:
        request = request.lower().split(',')
    else:
        request = process.extractOne(request,crew.keys(),scorer=fuzz.partial_ratio)[0]
        phrase = "%s was parsed as %s\n"%(initial_request,request.title())+"```Name: %s \nGender: %s\nRace: %s \nHP: %s \nPilot: %s \nAttack: %s \nFire Resistance: %s \nRepair: %s \nWeapon: %s \nShield: %s \nEngine: %s \nResearch: %s \nWalking Speed: %s \nRunning Speed: %s\nRarity: %s \nProgression: %s \nXP: %s \nSpecial Type: %s \nSpecial: %s \nTraining: %s \nEquipment: %s - %s```"%(getattr(crew[request],metrics[0]).title(),getattr(crew[request],metrics[1]),getattr(crew[request],metrics[2]),getattr(crew[request],metrics[3]),getattr(crew[request],metrics[4]),getattr(crew[request],metrics[5]),getattr(crew[request],metrics[6]),getattr(crew[request],metrics[7]),getattr(crew[request],metrics[8]),getattr(crew[request],metrics[9]),getattr(crew[request],metrics[10]),getattr(crew[request],metrics[11]),getattr(crew[request],metrics[12]),getattr(crew[request],metrics[13]),getattr(crew[request],metrics[14]),getattr(crew[request],metrics[15]),getattr(crew[request],metrics[16]),getattr(crew[request],metrics[17]),getattr(crew[request],metrics[18]),getattr(crew[request],metrics[19]),getattr(crew[request],metrics[20]),equipment_loadouts[int(getattr(crew[request],metrics[20]))])
        await bot.say(phrase)
        return
    if request[1][0] == ' ':
        request[1] = request[1][1:]
    if request[0].lower()=='equip' or request[0].lower()=='equipment':
        try:
            await bot.say("Loadout %s is for ```%s```"%(request[1],equipment_loadouts[int(request[1])]))
            return
        except:
            await bot.say("I don't know how you got here")
            return
    try:
        await bot.say("%s's %s is: %s"%(request[0].title(), request[1], getattr(crew[request[0]],request[1])))
        if request[1].lower=='equip' or request[1].lower()=='equipment':
            await bot.say("```%s```"%(equipment_loadouts[int(getattr(crew[request[0]],request[1]))]))
    except:
        await bot.say("I don't understand something. Try ```?stats names``` to correct spelling")
  
bot.run('Mjc0NDU1NTg5NTY2ODA4MDc2.C2yWMw.uFEcuSxiZRJPp-UkloTvWV0z84Q')
