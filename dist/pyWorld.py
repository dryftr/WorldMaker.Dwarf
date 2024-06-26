import libtcodpy as libtcod
import time
from random import randint
from random import uniform
import cProfile

## MY IMPORTS - THIS IS TO HANDLE THE WORLDGEN DATA DISPLAY IN THE SECONDARY CONSOLE ##
import os
# pyWorld.py or Civilization.py
from logger_config import logger, setup_logging
## handle the setup for logging now if this is running on Linux variants
if os.name == 'nt':  # Windows
    print("Windows OS detected. Logging disabled. Using console instead.")
elif os.name == 'posix':  # Linux
    # Call this function at the start of your script or when you initialize your module
    setup_logging()
    logger.info("Linux OS detected. Logging started.")
    logger.info("----------------------------------------------")


pr = cProfile.Profile()
pr.enable()

WORLD_WIDTH = 200
WORLD_HEIGHT = 80

SCREEN_WIDTH = 200
SCREEN_HEIGHT = 80

CIVILIZED_CIVS = 2
TRIBAL_CIVS = 2

MIN_RIVER_LENGHT = 3

CIV_MAX_SITES = 20
EXPANSION_DISTANCE = 10
WAR_DISTANCE = 8


###################################################################################### - Classes - ######################################################################################

class Tile:

    def __init__(self, height, temp, precip, drainage, biome):
        self.temp = temp
        self.height = height
        self.precip = precip
        self.drainage = drainage
        self.biome = biome

    hasRiver = False
    isCiv = False

    biomeID = 0
    prosperity = 0


class Race:

    def __init__(self, Name, PrefBiome, Strenght, Size, ReproductionSpeed, Aggressiveness, Form):
        self.Name = Name
        self.PrefBiome = PrefBiome
        self.Strenght = Strenght
        self.Size = Size
        self.ReproductionSpeed = ReproductionSpeed
        self.Aggressiveness = Aggressiveness
        self.Form = Form


class CivSite:

    def __init__(self, x, y, category, suitable, popcap):
        self.x = x
        self.y = y
        self.category = category
        self.suitable = suitable
        self.popcap = popcap

    Population = 0

    isCapital = False


class Army:

    def __init__(self, x, y, Civ, Size):
        self.x = x
        self.y = y
        self.Civ = Civ
        self.Size = Size


class Civ:

    def __init__(self, Race, Name, Government, Color, Flag, Aggression):
        self.Name = Name
        self.Race = Race
        self.Government = Government
        self.Color = Color
        self.Flag = Flag
        self.Aggression = Race.Aggressiveness + Government.Aggressiveness

    def PrintInfo(self):
        display_data(
            self.Name)
        display_data(
            self.Race.Name)
        display_data(
            self.Government.Name)
        display_data("Aggression: {}".format(self.Aggression))
        display_data("Suitable Sites: {}\n".format(len(self.SuitableSites)))

    Sites = []
    SuitableSites = []

    atWar = False

    Army = Army(None, None, None, None)
    TotalPopulation = 0


class GovernmentType:

    def __init__(self, Name, Description, Aggressiveness, Militarization, TechBonus):
        self.Name = Name
        self.Description = Description
        self.Aggressiveness = Aggressiveness
        self.Militarization = Militarization
        self.TechBonus = TechBonus


class War:

    def __init__(self, Side1, Side2):
        self.Side1 = Side1
        self.Side2 = Side2


##################################################################################### - Functions - #####################################################################################

# - General Functions -

def display_data(data):
    """
    Display data by printing or logging depending on the operating system.
    On Windows, it prints to the console; on Linux, it logs to a file.

    Parameters:
    - data: The data to be displayed.

    Returns:
    None
    """
    if os.name == 'nt':  # Windows
        print(data)
    elif os.name == 'posix':  # Linux
        logger.info(data)
    # honestly I'd like to be able to support other OS's as well, but need to figure out how to do that.
    #else:
    #    raise NotImplementedError("OS not supported.")

def ClearConsole():
    ### NOTE FOR ME: This never triggered an error...could this be the "second console"? need to track this code better.
    for x in list(range(SCREEN_WIDTH)):
        for y in list(range(SCREEN_HEIGHT)):
            libtcod.console_put_char_ex(0, x, y, ' ', libtcod.black, libtcod.black)

    libtcod.console_flush()

    return


def PointDistRound(pt1x, pt1y, pt2x, pt2y):
    distance = abs(pt2x - pt1x) + abs(pt2y - pt1y);

    distance = round(distance)

    return distance


def FlagGenerator(Color):
    Flag = [[0 for a in range(4)] for b in range(12)]

    BackColor1 = Color
    BackColor2 = Palette[randint(0, len(Palette) - 1)]

    OverColor1 = Palette[randint(0, len(Palette) - 1)]
    OverColor2 = Palette[randint(0, len(Palette) - 1)]

    BackFile = open("Background.txt", 'r')
    OverlayFile = open("Overlay.txt", 'r')

    BTypes = (sum(1 for line in open('Background.txt')) + 1) / 5
    OTypes = (sum(1 for line in open('Overlay.txt')) + 1) / 5

    Back = randint(1, BTypes)
    Overlay = randint(1, OTypes)

    for a in range(53 * (Back - 1)):
        C = BackFile.read(1)

    for a in range(53 * (Overlay - 1)):
        C = OverlayFile.read(1)

    for y in range(4):
        for x in range(12):

            C = BackFile.read(1)
            while C == '\n':
                C = BackFile.read(1)

            if C == '#':
                Flag[x][y] = BackColor1
            elif C == '"':
                Flag[x][y] = BackColor2

            C = OverlayFile.read(1)
            while C == '\n':
                C = OverlayFile.read(1)

            if C == '#':
                Flag[x][y] = OverColor1
            elif C == '"':
                Flag[x][y] = OverColor2

    BackFile.close()
    OverlayFile.close()

    return Flag


def LowestNeighbour(X, Y, World):  # Diagonals are commented for rivers

    minval = 1

    x = 0
    y = 0

    if World[X + 1][Y].height < minval and X + 1 < WORLD_WIDTH:
        minval = World[X + 1][Y].height
        x = X + 1
        y = Y

    if World[X][Y + 1].height < minval and Y + 1 < WORLD_HEIGHT:
        minval = World[X][Y + 1].height
        x = X
        y = Y + 1

    # if libtcod.heightmap_get_value(hm, X + 1, Y + 1) < minval and X + 1 < WORLD_WIDTH and Y + 1 < WORLD_HEIGHT and minval > 0.2:
    # minval = libtcod.heightmap_get_value(hm, X + 1, Y + 1)
    # x = X + 1
    # y = Y + 1

    # if libtcod.heightmap_get_value(hm, X - 1, Y - 1) < minval and X - 1 > 0 and Y - 1 > 0 and minval > 0.2:
    # minval = libtcod.heightmap_get_value(hm, X - 1, Y - 1)
    # x = X - 1
    # y = Y - 1

    if World[X - 1][Y].height < minval and X - 1 > 0:
        minval = World[X - 1][Y].height
        x = X - 1
        y = Y

    if World[X][Y - 1].height < minval and Y - 1 > 0:
        minval = World[X][Y - 1].height
        x = X
        y = Y - 1

    # f libtcod.heightmap_get_value(hm, X + 1, Y - 1) < minval and X + 1 < WORLD_WIDTH and Y - 1 > 0 and minval > 0.2:
    # minval = libtcod.heightmap_get_value(hm, X + 1, Y - 1)
    # x = X + 1
    # y = Y - 1

    # if libtcod.heightmap_get_value(hm, X - 1, Y + 1) < minval and X - 1 > 0 and Y + 1 < WORLD_HEIGHT and minval > 0.2 :
    # minval = libtcod.heightmap_get_value(hm, X - 1, Y + 1)
    # x = X - 1
    # y = Y + 1

    error = 0

    if x == 0 and y == 0:
        error = 1

    return (x, y, error)


# - MapGen Functions -

def PoleGen(hm, NS):
    if NS == 0:
        rng = randint(2, 5)
        for i in range(WORLD_WIDTH):
            for j in range(rng):
                libtcod.heightmap_set_value(hm, i, WORLD_HEIGHT - 1 - j, 0.31)
            rng += randint(1, 3) - 2
            if rng > 6:
                rng = 5
            if rng < 2:
                rng = 2

    if NS == 1:
        rng = randint(2, 5)
        for i in range(WORLD_WIDTH):
            for j in range(rng):
                libtcod.heightmap_set_value(hm, i, j, 0.31)
            rng += randint(1, 3) - 2
            if rng > 6:
                rng = 5
            if rng < 2:
                rng = 2

    return


def TectonicGen(hm, hor):
    TecTiles = [[0 for y in range(WORLD_HEIGHT)] for x in range(WORLD_WIDTH)]

    # Define Tectonic Borders
    if hor == 1:
        pos = randint(WORLD_HEIGHT / 10, WORLD_HEIGHT - WORLD_HEIGHT / 10)
        for x in range(WORLD_WIDTH):
            TecTiles[x][pos] = 1
            pos += randint(1, 5) - 3
            if pos < 0:
                pos = 0
            if pos > WORLD_HEIGHT - 1:
                pos = WORLD_HEIGHT - 1
    if hor == 0:
        pos = randint(WORLD_WIDTH / 10, WORLD_WIDTH - WORLD_WIDTH / 10)
        for y in range(WORLD_HEIGHT):
            TecTiles[pos][y] = 1
            pos += randint(1, 5) - 3
            if pos < 0:
                pos = 0
            if pos > WORLD_WIDTH - 1:
                pos = WORLD_WIDTH - 1

    # Apply elevation to borders.
    for x in list(range(WORLD_WIDTH // 10, WORLD_WIDTH - WORLD_WIDTH // 10)):
        for y in list(range(WORLD_HEIGHT // 10, WORLD_HEIGHT - WORLD_HEIGHT // 10)):
            if TecTiles[x][y] == 1 and libtcod.heightmap_get_value(hm, x, y) > 0.3:
                libtcod.heightmap_add_hill(hm, x, y, randint(2, 4), uniform(0.15, 0.18))

    return


def Temperature(temp, hm):
    # This needed to be upgraded to Python3 using list(range()) instead of xrange()
    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            heighteffect = 0
            if y > WORLD_HEIGHT / 2:
                libtcod.heightmap_set_value(temp, x, y, WORLD_HEIGHT - y - heighteffect)
            else:
                libtcod.heightmap_set_value(temp, x, y, y - heighteffect)
            heighteffect = libtcod.heightmap_get_value(hm, x, y)
            if heighteffect > 0.8:
                heighteffect = heighteffect * 5
                if y > WORLD_HEIGHT / 2:
                    libtcod.heightmap_set_value(temp, x, y, WORLD_HEIGHT - y - heighteffect)
                else:
                    libtcod.heightmap_set_value(temp, x, y, y - heighteffect)
            if heighteffect < 0.25:
                heighteffect = heighteffect * 10
                if y > WORLD_HEIGHT / 2:
                    libtcod.heightmap_set_value(temp, x, y, WORLD_HEIGHT - y - heighteffect)
                else:
                    libtcod.heightmap_set_value(temp, x, y, y - heighteffect)

    return


def Percipitaion(preciphm, temphm):
    libtcod.heightmap_add(preciphm, 2)

    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            temp = libtcod.heightmap_get_value(temphm, x, y)

    precip = libtcod.noise_new(2, libtcod.NOISE_DEFAULT_HURST, libtcod.NOISE_DEFAULT_LACUNARITY)

    libtcod.heightmap_add_fbm(preciphm, precip, 2, 2, 0, 0, 32, 1, 1)

    libtcod.heightmap_normalize(preciphm, 0.0, 1.0)

    return


def RiverGen(World):
    X = randint(0, WORLD_WIDTH - 1)
    Y = randint(0, WORLD_HEIGHT - 1)

    XCoor = []
    YCoor = []

    tries = 0

    prev = ""

    while World[X][Y].height < 0.8:
        tries += 1
        X = randint(0, WORLD_WIDTH - 1)
        Y = randint(0, WORLD_HEIGHT - 1)

        if tries > 2000:
            return

    del XCoor[:]
    del YCoor[:]

    XCoor.append(X)
    YCoor.append(Y)

    while World[X][Y].height >= 0.2:

        X, Y, error = LowestNeighbour(X, Y, World)

        if error == 1:
            return

        try:
            if World[X][Y].hasRiver or World[X + 1][Y].hasRiver or World[X - 1][Y].hasRiver or World[X][
                Y + 1].hasRiver or World[X][Y - 1].hasRiver:
                break
        except IndexError:
            return

        if X in XCoor and Y in YCoor:
            break

        XCoor.append(X)
        YCoor.append(Y)

    if len(XCoor) <= MIN_RIVER_LENGHT:
        return

    for x in range(len(XCoor)):
        if World[XCoor[x]][YCoor[x]].height < 0.2:
            break
        World[XCoor[x]][YCoor[x]].hasRiver = True
        if World[XCoor[x]][YCoor[x]].height >= 0.2 and x == len(XCoor):
            World[XCoor[x]][YCoor[
                x]].hasRiver = True  # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Change to Lake later

    return


def Prosperity(World):
    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            World[x][y].prosperity = (1.0 - abs(World[x][y].precip - 0.6) + 1.0 - abs(World[x][y].temp - 0.5) +
                                        World[x][y].drainage) / 3

    return


def MasterWorldGen():  # ------------------------------------------------------- * MASTER GEN * -------------------------------------------------------------

    display_data(' * World Gen START * ')
    starttime = time.time()

    # Heightmap
    hm = libtcod.heightmap_new(WORLD_WIDTH, WORLD_HEIGHT)

    for i in range(250):
        libtcod.heightmap_add_hill(hm, randint(WORLD_WIDTH / 10, WORLD_WIDTH - WORLD_WIDTH / 10),
                                    randint(WORLD_HEIGHT / 10, WORLD_HEIGHT - WORLD_HEIGHT / 10), randint(12, 16),
                                    randint(6, 10))
    display_data('- Main Hills -')

    for i in range(1000):
        libtcod.heightmap_add_hill(hm, randint(WORLD_WIDTH / 10, WORLD_WIDTH - WORLD_WIDTH / 10),
                                    randint(WORLD_HEIGHT / 10, WORLD_HEIGHT - WORLD_HEIGHT / 10), randint(2, 4),
                                    randint(6, 10))
    display_data('- Small Hills -')

    libtcod.heightmap_normalize(hm, 0.0, 1.0)

    noisehm = libtcod.heightmap_new(WORLD_WIDTH, WORLD_HEIGHT)
    noise2d = libtcod.noise_new(2, libtcod.NOISE_DEFAULT_HURST, libtcod.NOISE_DEFAULT_LACUNARITY)
    libtcod.heightmap_add_fbm(noisehm, noise2d, 6, 6, 0, 0, 32, 1, 1)
    libtcod.heightmap_normalize(noisehm, 0.0, 1.0)
    libtcod.heightmap_multiply_hm(hm, noisehm, hm)
    display_data('- Apply Simplex -')

    PoleGen(hm, 0)
    display_data('- South Pole -')

    PoleGen(hm, 1)
    display_data('- North Pole -')

    TectonicGen(hm, 0)
    TectonicGen(hm, 1)
    display_data('- Tectonic Gen -')
    libtcod.heightmap_rain_erosion(hm, WORLD_WIDTH * WORLD_HEIGHT, 0.07, 0, 0)
    
    display_data('- Erosion -')
    libtcod.heightmap_clamp(hm, 0.0, 1.0)

    # Temperature
    temp = libtcod.heightmap_new(WORLD_WIDTH, WORLD_HEIGHT)
    Temperature(temp, hm)
    libtcod.heightmap_normalize(temp, 0.0, 1.0)
    display_data('- Temperature Calculation -')

    # Precipitation

    preciphm = libtcod.heightmap_new(WORLD_WIDTH, WORLD_HEIGHT)
    Percipitaion(preciphm, temp)
    libtcod.heightmap_normalize(preciphm, 0.0, 1.0)
    display_data('- Percipitaion Calculation -')

    # Drainage

    drainhm = libtcod.heightmap_new(WORLD_WIDTH, WORLD_HEIGHT)
    drain = libtcod.noise_new(2, libtcod.NOISE_DEFAULT_HURST, libtcod.NOISE_DEFAULT_LACUNARITY)
    libtcod.heightmap_add_fbm(drainhm, drain, 2, 2, 0, 0, 32, 1, 1)
    libtcod.heightmap_normalize(drainhm, 0.0, 1.0)
    display_data('- Drainage Calculation -')

    # VOLCANISM - RARE AT SEA FOR NEW ISLANDS (?) RARE AT MOUNTAINS > 0.9 (?) RARE AT TECTONIC BORDERS (?)

    elapsed_time = time.time() - starttime
    display_data(' * World Gen DONE *  in: {} seconds'.format(elapsed_time))

    # Initialize Tiles with Map values
    World = [[0 for y in range(WORLD_HEIGHT)] for x in range(WORLD_WIDTH)]
    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            World[x][y] = Tile(libtcod.heightmap_get_value(hm, x, y),
                               libtcod.heightmap_get_value(temp, x, y),
                               libtcod.heightmap_get_value(preciphm, x, y),
                               libtcod.heightmap_get_value(drainhm, x, y),
                               0)

    display_data('- Tiles Initialized -')

    # Prosperity

    Prosperity(World)
    display_data('- Prosperity Calculation -')

    # Biome info to Tile

    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):

            if World[x][y].precip >= 0.10 and World[x][y].precip < 0.33 and World[x][y].drainage < 0.5:
                World[x][y].biomeID = 3
                if randint(1, 2) == 2:
                    World[x][y].biomeID = 16

            if World[x][y].precip >= 0.10 and World[x][y].precip > 0.33:
                World[x][y].biomeID = 2
                if World[x][y].precip >= 0.66:
                    World[x][y].biomeID = 1

            if World[x][y].precip >= 0.33 and World[x][y].precip < 0.66 and World[x][y].drainage >= 0.33:
                World[x][y].biomeID = 15
                if randint(1, 5) == 5:
                    World[x][y].biomeID = 5

            if World[x][y].temp > 0.2 and World[x][y].precip >= 0.66 and World[x][y].drainage > 0.33:
                World[x][y].biomeID = 5
                if World[x][y].precip >= 0.75:
                    World[x][y].biomeID = 6
                if randint(1, 5) == 5:
                    World[x][y].biomeID = 15

            if World[x][y].precip >= 0.10 and World[x][y].precip < 0.33 and World[x][y].drainage >= 0.5:
                World[x][y].biomeID = 16
                if randint(1, 2) == 2:
                    World[x][y].biomeID = 14

            if World[x][y].precip < 0.10:
                World[x][y].biomeID = 4
                if World[x][y].drainage > 0.5:
                    World[x][y].biomeID = 16
                    if randint(1, 2) == 2:
                        World[x][y].biomeID = 14
                if World[x][y].drainage >= 0.66:
                    World[x][y].biomeID = 8

            if World[x][y].height <= 0.2:
                World[x][y].biomeID = 0

            if World[x][y].temp <= 0.2 and World[x][y].height > 0.15:
                World[x][y].biomeID = randint(11, 13)

            if World[x][y].height > 0.6:
                World[x][y].biomeID = 9
            if World[x][y].height > 0.9:
                World[x][y].biomeID = 10

    display_data('- BiomeIDs Atributed -')

    # River Gen

    for x in range(1):
        RiverGen(World)
    display_data('- River Gen -')

    # Free Heightmaps
    libtcod.heightmap_delete(hm)
    libtcod.heightmap_delete(temp)
    libtcod.heightmap_delete(noisehm)

    display_data(' * Biomes/Rivers Sorted *')

    display_data("returning completed world.")
    return World


def ReadRaces():
    RacesFile = 'Races.txt'

    NLines = sum(1 for line in open('Races.txt'))

    NRaces = NLines // 7

    f = open(RacesFile)

    Races = [0 for x in range(NRaces)]

    for x in range(NRaces):  # Reads info between ']' and '\n'
        Info = [0 for a in range(7)]
        for y in range(7):
            data = f.readline()
            start = data.index("]") + 1
            end = data.index("\n", start)
            Info[y] = data[start:end]
        PreferedBiomes = [int(s) for s in str.split(Info[1]) if s.isdigit()]  # Take numbers from string
        Races[x] = Race(Info[0], PreferedBiomes, int(Info[2]), int(Info[3]), int(Info[4]), int(Info[5]), Info[6])

    f.close()

    display_data('- Races Read -')

    return Races


def ReadGovern():
    GovernFile = 'CivilizedGovernment.txt'

    NLines = sum(1 for line in open('CivilizedGovernment.txt'))

    NGovern = NLines // 5

    f = open(GovernFile)

    Governs = [0 for x in range(NGovern)]

    for x in range(NGovern):  # Reads info between ']' and '\n'
        Info = [0 for a in range(5)]
        for y in range(5):
            data = f.readline()
            start = data.index("]") + 1
            end = data.index("\n", start)
            Info[y] = data[start:end]
        Governs[x] = GovernmentType(Info[0], Info[1], int(Info[2]), int(Info[3]), int(Info[4]))

    f.close()

    display_data('- Government Types Read -')

    return Governs


def CivGen(Races,
           Govern):  # -------------------------------------------------------------------- * CIV GEN * ----------------------------------------------------------------------------------

    Civs = []

    for x in range(CIVILIZED_CIVS):

        libtcod.namegen_parse('namegen/jice_fantasy.cfg')
        Name = libtcod.namegen_generate('Fantasy male')
        libtcod.namegen_destroy()

        Name += " Civilization"

        Race = Races[randint(0, len(Races) - 1)]
        while Race.Form != "civilized":
            Race = Races[randint(0, len(Races) - 1)]

        Government = Govern[randint(0, len(Govern) - 1)]

        Color = Palette[randint(0, len(Palette) - 1)]

        Flag = FlagGenerator(Color)

        # Initialize Civ
        Civs.append(Civ(Race, Name, Government, Color, Flag, 0))

    for a in range(TRIBAL_CIVS):

        libtcod.namegen_parse('namegen/jice_fantasy.cfg')
        Name = libtcod.namegen_generate('Fantasy male')
        libtcod.namegen_destroy()

        Name += " Tribe"

        Race = Races[randint(0, len(Races) - 1)]
        while Race.Form != "tribal":
            Race = Races[randint(0, len(Races) - 1)]

        Government = GovernmentType("Tribal", "*PLACE HOLDER*", 2, 50, 0)

        Color = libtcod.Color(randint(0, 255), randint(0, 255), randint(0, 255))

        Flag = FlagGenerator(Color)

        # Initialize Civ
        Civs.append(Civ(Race, Name, Government, Color, Flag, 0))

    display_data('- Civs Generated -')

    return Civs


def SetupCivs(Civs, World, Chars, Colors):
    for x in range(len(Civs)):

        Civs[x].Sites = []
        Civs[x].SuitableSites = []

        del Civs[x].SuitableSites[:]

        # Civs[x].PrintInfo()

        for i in range(WORLD_WIDTH):
            for j in range(WORLD_HEIGHT):
                for g in range(len(Civs[x].Race.PrefBiome)):
                    if World[i][j].biomeID == Civs[x].Race.PrefBiome[g]:
                        Civs[x].SuitableSites.append(CivSite(i, j, "", 1, 0))

        rand = randint(0, len(Civs[x].SuitableSites) - 1)
        while World[Civs[x].SuitableSites[rand].x][Civs[x].SuitableSites[rand].y].isCiv == True:
            del Civs[x].SuitableSites[rand]
            rand = randint(0, len(Civs[x].SuitableSites) - 1)

        X = Civs[x].SuitableSites[rand].x
        Y = Civs[x].SuitableSites[rand].y

        World[X][Y].isCiv = True

        FinalProsperity = World[X][Y].prosperity * 150
        if World[X][Y].hasRiver:
            FinalProsperity = FinalProsperity * 1.5
        PopCap = 4 * Civs[x].Race.ReproductionSpeed + FinalProsperity
        PopCap = PopCap * 2  # Capital Bonus
        PopCap = round(PopCap)

        Civs[x].Sites.append(CivSite(X, Y, "Village", 0, PopCap))

        Civs[x].Sites[0].isCapital = True

        Civs[x].Sites[0].Population = 20

        Chars[X][Y] = 31
        Colors[X][Y] = Civs[x].Color

        Civs[x].PrintInfo()

    display_data('- Civs Setup -')

    display_data(' * Civ Gen DONE *')

    return Civs


##################################################################################### - PROCESS CIVS - ##################################################################################

def NewSite(Civ, Origin, World, Chars, Colors):
    rand = randint(0, len(Civ.SuitableSites) - 1)

    Tries = 0

    while PointDistRound(Origin.x, Origin.y, Civ.SuitableSites[rand].x,
                         Civ.SuitableSites[rand].y) > EXPANSION_DISTANCE or World[Civ.SuitableSites[rand].x][
        Civ.SuitableSites[rand].y].isCiv:
        if Tries > 200:
            return Civ
        Tries += 1
        rand = randint(0, len(Civ.SuitableSites) - 1)

    X = Civ.SuitableSites[rand].x
    Y = Civ.SuitableSites[rand].y

    World[X][Y].isCiv = True

    FinalProsperity = World[X][Y].prosperity * 150
    if World[X][Y].hasRiver:
        FinalProsperity = FinalProsperity * 1.5
    PopCap = 3 * Civ.Race.ReproductionSpeed + FinalProsperity
    PopCap = round(PopCap)

    Civ.Sites.append(CivSite(X, Y, "Village", 0, PopCap))

    Civ.Sites[len(Civ.Sites) - 1].Population = 20

    Chars[X][Y] = 31
    Colors[X][Y] = Civ.Color

    global needUpdate
    needUpdate = True

    return Civ


def ProcessCivs(World, Civs, Chars, Colors, Month):
    """
    Process the civilizations in the world by updating their population, sites, and handling diplomacy. This
    function is called once per month but will become far more advanced as I start developing for my own
    project.
    NOTE: Previously this function only used print statements to output info to a secondary Windows console.
    I am going to add logging so that I can use "tail" to monitor the output in Linux as it was in Windows.
    Later I can use some version of code from the "os" module to differentiate and use the right method to
    show the update data from here. Eventually though it should have a GUI inside the game itself to display
    the data.
    May just create a new function to do this. Instead of print or log it would be reduced to a function call
    like DisplayData(thedata) and that function would do the OS check and either log or print depending on the OS.
    
    Parameters:
    - World: The world map where the civilizations exist.
    - Civs: List of civilizations to process.
    - Chars: Character representation of the world.
    - Colors: Color representation of the world.
    - Month: The current month in the simulation.
    Returns:
    None
    """
    display_data("------------------------------------------")

    for x in range(CIVILIZED_CIVS + TRIBAL_CIVS):

        display_data(Civs[x].Name)
        display_data(Civs[x].Race.Name)

        Civs[x].TotalPopulation = 0

        # Site
        for y in range(len(Civs[x].Sites)):

            # Population
            NewPop = int(round(Civs[x].Sites[y].Population * Civs[x].Race.ReproductionSpeed / 1500))

            if Civs[x].Sites[y].Population > Civs[x].Sites[y].popcap / 2:
                NewPop /= 6

            Civs[x].Sites[y].Population += NewPop

            # Expand
            if Civs[x].Sites[y].Population > Civs[x].Sites[y].popcap:
                Civs[x].Sites[y].Population = int(round(Civs[x].Sites[y].popcap))
                if len(Civs[x].Sites) < CIV_MAX_SITES:
                    Civs[x].Sites[y].Population = int(round(Civs[x].Sites[y].popcap / 2))
                    Civs[x] = NewSite(Civs[x], Civs[x].Sites[y], World, Chars, Colors)

            Civs[x].TotalPopulation += Civs[x].Sites[y].Population

            # Diplomacy
            for a in range(CIVILIZED_CIVS + TRIBAL_CIVS):
                for b in range(len(Civs[a].Sites)):
                    if x == a:
                        break
                    if PointDistRound(Civs[x].Sites[y].x, Civs[x].Sites[y].y, Civs[a].Sites[b].x,
                                      Civs[a].Sites[b].y) < WAR_DISTANCE:
                        AlreadyWar = False
                        for c in range(len(Wars)):
                            if (Wars[c].Side1 == Civs[x] and Wars[c].Side2 == Civs[a]) or (
                                    Wars[c].Side1 == Civs[a] and Wars[c].Side2 == Civs[x]):
                                # Already at War
                                AlreadyWar = True
                        if AlreadyWar == False:
                            # Start War and form armies if dot have army yet
                            Wars.append(War(Civs[x], Civs[a]))
                            if Civs[a].atWar == False:  # if not already at war form new army
                                Civs[a].Army = Army(Civs[a].Sites[0].x,
                                                    Civs[a].Sites[0].y,
                                                    Civs[a],
                                                    Civs[a].TotalPopulation * Civs[a].Government.Militarization / 100)
                                Civs[a].atWar = True
                            if Civs[x].atWar == False:  # if not already at war form new army
                                Civs[x].Army = Army(Civs[x].Sites[0].x,
                                                    Civs[x].Sites[0].y,
                                                    Civs[x],
                                                    Civs[x].TotalPopulation * Civs[x].Government.Militarization / 100)
                                Civs[x].atWar = True

            display_data(f"X: {Civs[x].Sites[y].x}, Y: {Civs[x].Sites[y].y}, Population: {Civs[x].Sites[y].Population}")

        display_data(f"Army Position: ({Civs[x].Army.x}, {Civs[x].Army.y}) Size: {Civs[x].Army.Size}\n")
        
    return


####################################################################################### - MAP MODES - ####################################################################################

# --------------------------------------------------------------------------------- Print Map (Terrain) --------------------------------------------------------------------------------

def TerrainMap(World):
    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            hm_v = World[x][y].height
            libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '0', libtcod.blue,
                                        libtcod.black)
            if hm_v > 0.1:
                libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '1', libtcod.blue,
                                            libtcod.black)
            if hm_v > 0.2:
                libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '2', Palette[0],
                                            libtcod.black)
            if hm_v > 0.3:
                libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '3', Palette[0],
                                            libtcod.black)
            if hm_v > 0.4:
                libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '4', Palette[0],
                                            libtcod.black)
            if hm_v > 0.5:
                libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '5', Palette[0],
                                            libtcod.black)
            if hm_v > 0.6:
                libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '6', Palette[0],
                                            libtcod.black)
            if hm_v > 0.7:
                libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '7', Palette[0],
                                            libtcod.black)
            if hm_v > 0.8:
                libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '8', libtcod.dark_sepia,
                                            libtcod.black)
            if hm_v > 0.9:
                libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '9', libtcod.light_gray,
                                            libtcod.black)
            if hm_v > 0.99:
                libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '^', libtcod.darker_gray,
                                            libtcod.black)
    libtcod.console_flush()
    return


def BiomeMap(Chars, Colors):
    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, Chars[x][y], Colors[x][y],
                                        libtcod.black)

    libtcod.console_flush()
    return


def HeightGradMap(
        World):  # ------------------------------------------------------------ Print Map (Heightmap Gradient) -------------------------------------------------------------------
    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            hm_v = World[x][y].height
            HeightColor = libtcod.Color(255, 255, 255)
            libtcod.color_set_hsv(HeightColor, 0, 0,
                                  hm_v)  # Set lightness to hm_v so higher heightmap value -> "whiter"
            libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '\333', HeightColor,
                                        libtcod.black)
    libtcod.console_flush()
    return


def TempGradMap(
        World):  # ------------------------------------------------------------ Print Map (Surface Temperature Gradient) white -> cold red -> warm --------------------------------
    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            tempv = World[x][y].temp
            tempcolor = libtcod.color_lerp(libtcod.white, libtcod.red, tempv)
            libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '\333', tempcolor,
                                        libtcod.black)
    libtcod.console_flush()
    return


def PrecipGradMap(
        World):  # ------------------------------------------------------------ Print Map (Precipitation Gradient) white -> low blue -> high --------------------------------
    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            tempv = World[x][y].precip
            tempcolor = libtcod.color_lerp(libtcod.white, libtcod.light_blue, tempv)
            libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '\333', tempcolor,
                                        libtcod.black)
    libtcod.console_flush()
    return


def DrainageGradMap(
        World):  # ------------------------------------------------------------ Print Map (Drainage Gradient) brown -> low white -> high --------------------------------
    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            drainv = World[x][y].drainage
            draincolor = libtcod.color_lerp(libtcod.darkest_orange, libtcod.white, drainv)
            libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '\333', draincolor,
                                        libtcod.black)
    libtcod.console_flush()
    return


def ProsperityGradMap(
        World):  # ------------------------------------------------------------ Print Map (Prosperity Gradient) white -> low green -> high --------------------------------
    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            prosperitynv = World[x][y].prosperity
            prosperitycolor = libtcod.color_lerp(libtcod.white, libtcod.darker_green, prosperitynv)
            libtcod.console_put_char_ex(0, x, y + SCREEN_HEIGHT // 2 - WORLD_HEIGHT // 2, '\333', prosperitycolor,
                                        libtcod.black)
    libtcod.console_flush()
    return


def NormalMap(
        World):  # ------------------------------------------------------------ Normal Map (Biome + Entities) --------------------------------

    Chars = [[0 for y in range(WORLD_HEIGHT)] for x in range(WORLD_WIDTH)]
    Colors = [[0 for y in range(WORLD_HEIGHT)] for x in range(WORLD_WIDTH)]

    def SymbolDictionary(x):
        char = ''
        if x == 15 or x == 8:
            if randint(1, 2) == 2:
                char = 251
            else:
                char = ','
        if x == 1:
            if randint(1, 2) == 2:
                char = 244
            else:
                char = 131
        if x == 2:
            if randint(1, 2) == 2:
                char = '"'
            else:
                char = 163
        return {
            0: '\367',
            1: char,
            2: char,
            3: 'n',
            4: '\367',
            5: 24,
            6: 6 - randint(0, 1),
            8: char,
            9: 127,
            10: 30,
            11: 176,
            12: 177,
            13: 178,
            14: 'n',
            15: char,
            16: 139
        }[x]

    def ColorDictionary(x):
        badlands = libtcod.Color(204, 159, 81)
        icecolor = libtcod.Color(176, 223, 215)
        darkgreen = libtcod.Color(68, 158, 53)
        lightgreen = libtcod.Color(131, 212, 82)
        water = libtcod.Color(13, 103, 196)
        mountain = libtcod.Color(185, 192, 162)
        desert = libtcod.Color(255, 218, 90)
        return {
            0: water,
            1: darkgreen,
            2: lightgreen,
            3: lightgreen,
            4: desert,
            5: darkgreen,
            6: darkgreen,
            8: badlands,
            9: mountain,
            10: mountain,
            11: icecolor,
            12: icecolor,
            13: icecolor,
            14: darkgreen,
            15: lightgreen,
            16: darkgreen
        }[x]

    for x in list(range(WORLD_WIDTH)):
        for y in list(range(WORLD_HEIGHT)):
            Chars[x][y] = SymbolDictionary(World[x][y].biomeID)
            Colors[x][y] = ColorDictionary(World[x][y].biomeID)
            if World[x][y].hasRiver:
                Chars[x][y] = 'o'
                Colors[x][y] = libtcod.light_blue

    return Chars, Colors


###################################################################################### - Startup - ######################################################################################

# Start Console and set costum font
libtcod.console_set_custom_font("Andux_cp866ish.png", libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'pyWorld', False,
                          libtcod.RENDERER_SDL)  # Set True for Fullscreen

# Palette
Palette = [libtcod.Color(255, 45, 33),  # Red
           libtcod.Color(254, 80, 0),  # Orange
           libtcod.Color(0, 35, 156),  # Blue
           libtcod.Color(71, 45, 96),  # Purple
           libtcod.Color(0, 135, 199),  # Ocean Blue
           libtcod.Color(254, 221, 0),  # Yellow
           libtcod.Color(255, 255, 255),  # White
           libtcod.Color(99, 102, 106)]  # Gray

# libtcod.sys_set_fps(30)
# libtcod.console_set_fullscreen(True)

################################################################################# - Main Cycle / Input - ##################################################################################

isRunning = False
needUpdate = False

# World Gen
World = [[0 for y in range(WORLD_HEIGHT)] for x in range(WORLD_WIDTH)]
World = MasterWorldGen()

# Normal Map Initialization
Chars, Colors = NormalMap(World)

# Read Races
Races = ReadRaces()

# Read Governments
Govern = ReadGovern()

# Civ Gen
Civs = [0 for x in range(CIVILIZED_CIVS + TRIBAL_CIVS)]
Civs = CivGen(Races, Govern)

# Setup Civs
Civs = SetupCivs(Civs, World, Chars, Colors)

# Print Map
BiomeMap(Chars, Colors)

# Month 0
Month = 0

# Reset Wars
Wars = []
del Wars[:]

# Select Map Mode
while not libtcod.console_is_window_closed():

    # Simulation
    while isRunning == True:

        ProcessCivs(World, Civs, Chars, Colors, Month)

        # DEBUG Print Mounth
        Month += 1
        display_data(f'Month: {Month}')


        # End Simulation
        libtcod.console_check_for_keypress(True)
        if libtcod.console_is_key_pressed(libtcod.KEY_SPACE):
            timer = 0
            isRunning = False
            display_data("*PAUSED*")
            time.sleep(1)

        # Flush Console
        if needUpdate:
            BiomeMap(Chars, Colors)
            needUpdate = False

    key = libtcod.console_wait_for_keypress(True)

    # Start Simulation
    if libtcod.console_is_key_pressed(libtcod.KEY_SPACE):
        isRunning = True
        display_data("*RUNNING*")
        time.sleep(1)

    # Profiler
    if libtcod.console_is_key_pressed(libtcod.KEY_ESCAPE):
        isRunning = False

        pr.disable()
        pr.print_stats(sort='time')

    if key.vk == libtcod.KEY_CHAR:
        if key.c == ord('t'):
            TerrainMap(World)
        elif key.c == ord('h'):
            HeightGradMap(World)
        elif key.c == ord('w'):
            TempGradMap(World)
        elif key.c == ord('p'):
            PrecipGradMap(World)
        elif key.c == ord('d'):
            DrainageGradMap(World)
        elif key.c == ord('f'):
            ProsperityGradMap(World)
        elif key.c == ord('b'):
            BiomeMap(Chars, Colors)
        elif key.c == ord('r'):

            display_data("\n" * 100)
            display_data(" * NEW WORLD *")
            Month = 0
            Wars = []
            del Wars[:]
            World = MasterWorldGen()
            Races = ReadRaces()
            Govern = ReadGovern()
            Civs = CivGen(Races, Govern)
            Chars, Colors = NormalMap(World)
            SetupCivs(Civs, World, Chars, Colors)
            BiomeMap(Chars, Colors)
