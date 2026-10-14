"""Constanten en spelinhoud voor Grand Line Avontuur."""

W, H = 1280, 720
FPS = 60
TITLE = "Grand Line Avontuur"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 205, 60)
RED = (220, 60, 60)
GREEN = (90, 210, 110)
BLUE = (80, 150, 255)
GREY = (150, 150, 160)
DARK = (20, 24, 36)

# ---------------------------------------------------------------- wapens
# kind: stretch = rubberarm, arc = zwaai, spin = rondtrap, shot = projectiel, bolt = doorborend projectiel
WEAPONS = {
    "vuist": dict(name="Rubbervuist", kind="stretch", dmg=10, range=160, cd=0.33, price=0,
                  color=(240, 190, 150), desc="Je arm rekt uit als elastiek!"),
    "zwaard": dict(name="Houten zwaard", kind="arc", dmg=17, range=90, arc=120, cd=0.38, price=150,
                   color=(170, 120, 70), desc="Brede zwaai, raakt meerdere vijanden."),
    "katapult": dict(name="Katapult", kind="shot", dmg=14, speed=640, cd=0.26, price=260,
                     color=(120, 90, 60), desc="Schiet stenen van ver weg."),
    "trap": dict(name="Zwarte-Been-trap", kind="spin", dmg=26, range=100, cd=0.5, price=450,
                 color=(40, 40, 40), desc="Rondtrap die alles om je heen raakt."),
    "staf": dict(name="Klimaatstaf", kind="bolt", dmg=30, speed=560, cd=0.6, price=650,
                 color=(90, 170, 255), desc="Bliksemschicht die door vijanden heen gaat."),
    "driezwaard": dict(name="Drie-zwaarden-stijl", kind="arc", dmg=40, range=115, arc=160, cd=0.42,
                       price=1100, color=(220, 220, 235), desc="Het sterkste zwaardwerk op zee."),
}
WEAPON_ORDER = ["vuist", "zwaard", "katapult", "trap", "staf", "driezwaard"]

# ---------------------------------------------------------------- vijanden
ENEMY_TYPES = {
    "bandiet": dict(name="Bandiet", hp=30, speed=100, dmg=8, reward=12, radius=18, kind="melee",
                    shirt=(130, 85, 50), pants=(70, 60, 50), hat="bandana", style="normaal"),
    "marinier": dict(name="Marinier", hp=40, speed=92, dmg=9, reward=16, radius=18, kind="shooter",
                     shirt=(240, 240, 245), pants=(40, 70, 150), hat="marine", style="normaal"),
    "clownpiraat": dict(name="Clownpiraat", hp=48, speed=125, dmg=11, reward=20, radius=18, kind="melee",
                        shirt=(230, 80, 160), pants=(80, 60, 200), hat="clown", style="clown"),
    "visman": dict(name="Visman", hp=70, speed=112, dmg=14, reward=28, radius=20, kind="melee",
                   shirt=(60, 120, 170), pants=(30, 60, 90), hat="vin", style="vis"),
    "draak": dict(name="Kleine draak", hp=65, speed=125, dmg=11, reward=35, radius=24, kind="dragon",
                  color=(80, 170, 90)),
    "vuurdraak": dict(name="Vuurdraak", hp=120, speed=135, dmg=16, reward=60, radius=30, kind="dragon",
                      color=(210, 70, 40)),
}
HUMANOID_TYPES = ["bandiet", "marinier", "clownpiraat", "visman"]
DRAGON_TYPES = ["draak", "vuurdraak"]
RESEARCH_KILLS = 5  # zoveel keer verslaan = soort onderzocht (+25% schade)

BOSSES = {
    "hakbijl": dict(name="Bergbandiet Hakbijl", hp=260, dmg=14, speed=120, r=40, look="human",
                    shirt=(110, 70, 40), pants=(60, 50, 40), hat="bandana", extra="baard",
                    patterns=["charge", "slam", "aimed"], summon="bandiet", reward=300, seed=11),
    "ijzerhand": dict(name="Kapitein IJzerhand", hp=520, dmg=17, speed=115, r=44, look="human",
                      shirt=(235, 235, 240), pants=(40, 70, 150), hat="marine", extra="bijl",
                      patterns=["charge", "slam", "aimed", "summon"], summon="marinier", reward=500, seed=23),
    "clown": dict(name="Kapitein Clown", hp=820, dmg=19, speed=135, r=42, look="human",
                  shirt=(200, 40, 60), pants=(250, 200, 40), hat="clown", extra="clown",
                  patterns=["spray", "aimed", "summon", "charge"], summon="clownpiraat", reward=750, seed=37),
    "oerdraak": dict(name="De Oerdraak", hp=1400, dmg=22, speed=150, r=60, look="dragon",
                     color=(150, 40, 170), patterns=["breath", "spray", "charge", "slam"],
                     summon="draak", reward=1100, seed=41),
    "zeedraak": dict(name="Zeedraak Leviathan", hp=2400, dmg=26, speed=150, r=70, look="dragon",
                     color=(40, 110, 200), patterns=["breath", "slam", "spray", "summon", "charge"],
                     summon="visman", reward=2000, seed=53),
}

# ---------------------------------------------------------------- eilanden
# Elke riddle: q, options (eerste = juist), clue (wat je ontdekt)
ISLANDS = [
    dict(
        name="Windmolendorp", sub="Waar het avontuur begint", map_pos=(175, 560), size=(2400, 1700),
        grass=(108, 178, 78), grass2=(96, 162, 68), sand=(234, 214, 150), decor="dorp",
        enemies={"bandiet": 10, "draak": 1}, boss="hakbijl",
        intro=[
            ("Makino", "Welkom in Windmolendorp, kapitein! Bergbandieten maken het dorp onveilig."),
            ("Makino", "Hun leider Hakbijl zit in een hol achter de poort, rechtsboven op het eiland."),
            ("Makino", "Onderzoek de drie ?-plekken. Met drie aanwijzingen vind je de weg naar zijn hol."),
            ("Makino", "In de winkel koop je kracht en wapens met Berries. Die verdien je met vechten en voetballen!"),
        ],
        npcs=[
            ("Makino", "Die strohoed op je hoofd? Die was van Shanks, de roodharige piraat. Hij gaf hem aan jou!"),
            ("Burgemeester Woop", "In de taverne tellen we bandieten. Optellen en aftrekken, dat kan elke piraat!"),
            ("Visser Jan", "Boven het oosten van het eiland vliegt een kleine draak. Ontwijk zijn vuur met Shift!"),
        ],
        riddles=[
            dict(q="Je vindt een oude foto van een strohoed. Wie droeg die hoed vóór jou?",
                 options=["Shanks de Roodharige", "Kapitein Clown", "Garp de Vuist"],
                 clue="Op de achterkant van de foto staat een kaart: het hol ligt achter een houten poort."),
            dict(q="Op het prikbord van de taverne: 3 bandieten + 4 bandieten - 2 bandieten = ?",
                 options=["5", "9", "7"],
                 clue="Vijf bandieten bewaken de poort. Je noteert hun looproutes."),
            dict(q="Op de molen staat: 'Ik heb wieken maar ik vlieg niet.' Wat ben ik?",
                 options=["Een windmolen", "Een meeuw", "Een vlieger"],
                 clue="In de molen ligt de sleutel van de poort! Het hol van Hakbijl is nu bereikbaar."),
        ],
    ),
    dict(
        name="Schelpenstad", sub="Marinebasis van IJzerhand", map_pos=(420, 395), size=(2600, 1800),
        grass=(150, 170, 110), grass2=(136, 156, 98), sand=(226, 210, 160), decor="stad",
        enemies={"marinier": 10, "bandiet": 4, "draak": 2}, boss="ijzerhand",
        intro=[
            ("Coby", "Kapitein! De marine van Schelpenstad wordt geleid door de wrede Kapitein IJzerhand."),
            ("Coby", "Hij heeft een bijl in plaats van een hand. Zijn mariniers schieten met musketten!"),
            ("Coby", "Onderzoek de stad. Met drie aanwijzingen vinden we de weg naar zijn fort."),
        ],
        npcs=[
            ("Coby", "Iedereen hier noemt hem Kapitein IJzerhand. Niemand durft tegen hem in te gaan."),
            ("Rika", "Er zit een zwaardvechter vast op het plein. Hij vecht met drie zwaarden tegelijk!"),
            ("Oude matroos", "De vlag van de marine is wit met blauw, met een meeuw erop."),
        ],
        riddles=[
            dict(q="Hoe noemen de inwoners de baas van de marinebasis?",
                 options=["Kapitein IJzerhand", "Admiraal Hamer", "Kapitein Zwaardvis"],
                 clue="Je vindt het rooster van IJzerhand: hij zit elke middag in zijn fort in het noordoosten."),
            dict(q="Een zwaardvechter heeft 3 zwaarden. Hoeveel zwaarden hebben 4 zulke zwaardvechters?",
                 options=["12", "7", "9"],
                 clue="Een wapenkist met de inventaris van het fort. Je weet nu hoeveel mariniers er zijn."),
            dict(q="Welke vlag hangt er op de marinebasis?",
                 options=["Wit met blauw en een meeuw", "Zwart met een doodshoofd", "Roze met stippen"],
                 clue="Achter de vlaggenmast zit een geheime deur. Het fort van IJzerhand staat open!"),
        ],
    ),
    dict(
        name="Clownstad", sub="Het circus van Kapitein Clown", map_pos=(655, 565), size=(2600, 1800),
        grass=(176, 160, 110), grass2=(160, 146, 98), sand=(236, 206, 140), decor="circus",
        enemies={"clownpiraat": 12, "draak": 3}, boss="clown",
        intro=[
            ("Hondje Chouchou", "Waf! (Een hondje bewaakt de winkel. De stad is overgenomen door clownpiraten.)"),
            ("Burgemeester Boodle", "Kapitein Clown heeft de stad bezet! Hij kan zijn lichaam in stukken splitsen."),
            ("Burgemeester Boodle", "Zijn piraten zijn gek op voetbal. Win van ze op het veld voor de laatste aanwijzing!"),
        ],
        npcs=[
            ("Burgemeester Boodle", "Kapitein Clown at een duivelsvrucht. Sindsdien kan hij nooit meer zwemmen!"),
            ("Jongleur Mohji", "Ik jongleer, laat er een paar vallen en pak er weer bij. Kun jij nog tellen?"),
            ("Kind Lotte", "Wat heeft wijzers maar kan niet wijzen? De klok op het circus, natuurlijk!"),
        ],
        riddles=[
            dict(q="Kapitein Clown at een duivelsvrucht. Wat gebeurt er als je een duivelsvrucht eet?",
                 options=["Je kunt niet meer zwemmen", "Je kunt voortaan vliegen", "Je wordt onzichtbaar"],
                 clue="Clown is bang voor water. Zijn tent staat ver van de zee, in het noordoosten."),
            dict(q="Een clown jongleert met 7 ballen, laat er 2 vallen en pakt er 3 bij. Hoeveel nu?",
                 options=["8", "6", "12"],
                 clue="Je vindt het circusprogramma: de grote show begint na de voetbalwedstrijd."),
            dict(q="Wat heeft wijzers maar kan niet wijzen?",
                 options=["Een klok", "Een kompas", "Een wegwijzer"],
                 clue="Achter de circusklok zit de sleutel van de tent."),
        ],
        football_clue=True,
    ),
    dict(
        name="Drakeneiland", sub="Vulkaan vol draken", map_pos=(885, 330), size=(2700, 1900),
        grass=(92, 84, 76), grass2=(80, 72, 66), sand=(150, 120, 100), decor="vulkaan",
        enemies={"draak": 8, "vuurdraak": 4}, boss="oerdraak",
        intro=[
            ("Kluizenaar Gaimon", "Je bent gek dat je hier komt! Dit eiland wordt geregeerd door draken."),
            ("Kluizenaar Gaimon", "De Oerdraak slaapt in de krater. Zoek drie aanwijzingen om hem te vinden."),
            ("Kluizenaar Gaimon", "Draken blijven op afstand en spuwen vuur. Gebruik afstandswapens of rek je arm!"),
        ],
        npcs=[
            ("Kluizenaar Gaimon", "Draken leggen eieren in rijen van zes. Het grootste nest heeft twee rijen."),
            ("Verdwaalde scout", "Als je brandt: water helpt! Gelukkig ligt de zee rondom het eiland."),
            ("Stenen beeld", "...hoe meer je wegneemt, hoe groter ik word... (iemand heeft dit ingekrast)"),
        ],
        riddles=[
            dict(q="In een drakennest liggen 2 rijen van 6 eieren. Hoeveel eieren zijn het?",
                 options=["12", "8", "26"],
                 clue="De nesten liggen in een cirkel rond de krater van de Oerdraak."),
            dict(q="Een draak spuwt vuur op je schip. Waarmee blus je het best?",
                 options=["Water", "Olie", "Hout"],
                 clue="Verbrande voetafdrukken lopen naar het noordoosten."),
            dict(q="'Hoe meer je ervan wegneemt, hoe groter ik word.' Wat ben ik?",
                 options=["Een gat", "Een berg", "Een draak"],
                 clue="Een gat in de rotswand: de geheime ingang naar de krater!"),
        ],
    ),
    dict(
        name="Zeemanspark", sub="Laatste strijd tegen de Zeedraak", map_pos=(1110, 180), size=(2800, 1900),
        grass=(70, 150, 140), grass2=(62, 136, 128), sand=(240, 220, 170), decor="koraal",
        enemies={"visman": 12, "vuurdraak": 3}, boss="zeedraak",
        intro=[
            ("Nojiko", "De vismannen hebben het dorp van onze navigator Nami jarenlang onderdrukt."),
            ("Nojiko", "Hun meester is Leviathan, een reusachtige zeedraak. Dit wordt je zwaarste gevecht!"),
            ("Nojiko", "Zorg dat je sterk genoeg bent: koop kracht, HP en betere wapens voor je verdergaat."),
        ],
        npcs=[
            ("Nojiko", "Mijn zus Nami komt uit dit dorp. Ze tekent de mooiste zeekaarten ter wereld."),
            ("Dokter Nako", "Op de Grand Line werkt een gewoon kompas niet. Je hebt een Log Pose nodig."),
            ("Genzo", "De zeedraak is zo lang als 30 mannen. Zijn staart is een derde van zijn lengte."),
        ],
        riddles=[
            dict(q="Welke navigator van de strohoedbemanning komt uit dit dorp?",
                 options=["Nami", "Usopp", "Sanji"],
                 clue="Nami's oude kaarten tonen een onderwatergrot in het noordoosten."),
            dict(q="De zeedraak is 30 meter lang. Zijn staart is een derde daarvan. Hoe lang is de staart?",
                 options=["10 meter", "3 meter", "15 meter"],
                 clue="Je berekent hoe ver je moet wegblijven van zijn staartslag."),
            dict(q="Wat heb je nodig om te navigeren op de Grand Line?",
                 options=["Een Log Pose", "Een vergrootglas", "Een vlieger"],
                 clue="De Log Pose wijst naar de grot van Leviathan. Tijd voor de laatste strijd!"),
        ],
    ),
]

# ---------------------------------------------------------------- uitdagingen
CHALLENGES = [
    ("eerste", "Eerste gevecht", "Versla je eerste vijand.", 50),
    ("jager", "Mannetjesjager", "Versla 25 mannetjes met rare gezichten.", 250),
    ("draak1", "Drakentemmer", "Versla je eerste draak.", 150),
    ("draak10", "Drakendoder", "Versla 10 draken.", 500),
    ("hattrick", "Hattrick!", "Scoor 3 goals in één voetbalwedstrijd.", 250),
    ("spits", "Topspits", "Scoor 20 goals in totaal.", 400),
    ("kampioen", "Kampioen", "Win 5 voetbalwedstrijden.", 400),
    ("speurneus", "Speurneus", "Vind 6 aanwijzingen.", 200),
    ("professor", "Professor", "Onderzoek alle 6 vijandsoorten (elk 5x verslaan).", 600),
    ("onaantastbaar", "Onaantastbaar", "Versla een baas met meer dan de helft van je HP over.", 400),
    ("sterk", "Krachtpatser", "Bereik kracht-niveau 10.", 300),
    ("wapens", "Wapenverzamelaar", "Bezit alle 6 wapens.", 500),
    ("koning", "Koning der Piraten", "Versla Zeedraak Leviathan.", 1000),
]
