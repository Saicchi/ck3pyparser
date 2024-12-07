from cwtypes import *

STARTING_DATES = ["867.1.1", "1066.9.15", "1178.10.1"]
STARTING_DATES = {
    date: 10000 * int(date.split(".")[0])
    + 100 * int(date.split(".")[1])
    + int(date.split(".")[2])
    for date in STARTING_DATES
}

# Order Matters, first defined wins
# Collected from game_start.txt
EXTRA_SPECIAL = [
    ("religion", "islam_religion", "holy_site_mosque_01"),
    ("religion", "christianity_religion", "holy_site_cathedral_01"),
    ("religion", "zoroastrianism_religion", "holy_site_fire_temple_01"),
    ("religion", "hinduism_religion", "holy_site_indian_grand_temple_01"),
    ("religion", "buddhism_religion", "holy_site_indian_grand_temple_01"),
    ("religion", "jainism_religion", "holy_site_indian_grand_temple_01"),
    ("religion", "tani_religion", "holy_site_indian_grand_temple_01"),
    ("religion", "bon_religion", "holy_site_indian_grand_temple_01"),
    ("family", "rf_pagan", "holy_site_pagan_grand_temple_01"),
    ("religion", "any", "holy_site_other_grand_temple_01"),
    ("title", "b_fes", "generic_university"),
    ("title", "b_salamanca", "generic_university"),
    ("title", "b_madrid", "generic_university"),
    ("title", "b_cambridge", "generic_university"),
    ("title", "b_padua", "generic_university"),
    ("title", "b_coimbra", "generic_university"),
    ("title", "b_napoli", "generic_university"),
    ("title", "b_milano", "generic_university"),
    ("title", "b_vienna", "generic_university"),
    ("title", "b_praha", "generic_university"),
    ("title", "b_perugia", "generic_university"),
    ("title", "b_malappuram", "generic_university"),
    ("title", "b_janakpur", "generic_university"),
    ("title", "b_uppsala", "generic_university"),
    ("title", "b_montlhery", "generic_university"),
    ("title", "b_qartajana", "generic_university"),
    ("title", "b_wazwan", "generic_university"),
    ("title", "b_sarsar", "generic_university"),
    ("title", "b_speyer", "generic_university"),
    ("title", "b_krakow", "generic_university"),
    ("title", "b_pisa", "generic_university"),
    ("title", "b_rostock", "generic_university"),
    ("title", "b_turin", "generic_university"),
    ("title", "b_ferrara", "generic_university"),
    ("title", "b_leipzig", "generic_university"),
    ("title", "b_messina", "generic_university"),
    ("title", "b_barcelona", "generic_university"),
    ("title", "b_dumbarton", "generic_university"),
    ("title", "b_bidar", "generic_university"),
]


def map_extra_special() -> dict:
    mapping = {}
    for extra in EXTRA_SPECIAL:
        if extra[0] == "religion":
            if extra[1] == "any":
                faiths = list(CWFaith.ALL.values())
            else:
                faiths = CWReligion.ALL[extra[1]].faiths
            holy_sites = set(sum([faith.holy_site for faith in faiths], []))
            baronies = [site.barony.name for site in holy_sites]
        elif extra[0] == "family":
            if extra[1] == "any":
                faiths = list(CWFaith.ALL.values())
            else:
                faiths = [
                    faith
                    for faith in CWFaith.ALL.values()
                    if faith.family.name == extra[1]
                ]
            holy_sites = set(sum([faith.holy_site for faith in faiths], []))
            baronies = [site.barony.name for site in holy_sites]
        elif extra[0] == "title":
            baronies = [extra[1]]
        else:
            raise Exception(f"unhandled category in extra: {extra[0]}")

        for barony in baronies:
            if barony not in mapping:
                mapping[barony] = []
            mapping[barony].append(extra[2])  # first in list has priority

    return mapping

EXTRA_SPECIAL_MAPPING = map_extra_special()


class Title:
    ALL: dict[str, "Title"] = {}
    RANK: dict[str, "Title"] = {
        CWTitle.BARONY: [],
        CWTitle.COUNTY: [],
        CWTitle.DUCHY: [],
        CWTitle.KINGDOM: [],
        CWTitle.EMPIRE: [],
    }
    RANKS = list(RANK.keys())

    def __init__(self):
        self.name: str = None
        self.rank: str = None
        self.color: CWColor = None
        self.province: int = None
        self.capital: CWTitle = None
        self.altnames: dict[str, list[str]] = {}
        self.altnames_date: list[tuple[CWHistoryDate, str]] = []
        self.parent: list[tuple[CWHistoryDate, Title]] = []
        self.development: list[tuple[CWHistoryDate, int]] = []
        self.children: list[list[Title]] = []
        self.title_history: list[CWHistoryDate] = []
        self.culture: list[tuple[CWHistoryDate, CWCulture]] = []
        self.faith: list[tuple[CWHistoryDate, CWFaith]] = []
        self.special: list[tuple[CWHistoryDate, str]] = []
        self.special_slot: list[tuple[CWHistoryDate, str]] = []
        self.province_history: list[CWHistoryDate] = []
        self.can_create: CWObject = None

    def __repr__(self) -> str:
        return self.name

    @classmethod
    def initialize(cls):
        stubdate = CWHistoryDate()
        stubdate.date = Token("1.1.1")
        stubdate.datenum = 10101

        for cwtitle in CWTitle.ALL.values():
            title = cls()
            title.name = cwtitle.name
            title.rank = cwtitle.rank
            if title in cls.ALL:
                raise Exception(f"Duplicate Title: {title.name}")
            cls.ALL[title.name] = title
            cls.RANK[title.rank].append(title)

            # First value is base
            if len(cwtitle.parents) > 0:
                title.parent.append((stubdate, cwtitle.parents[-1]))
            else:
                title.parent.append((stubdate, None))
            title.children.append([])
            title.development.append((stubdate, 0))
            for _ in STARTING_DATES:
                title.children.append([])
                title.development.append((stubdate, 0))
            title.altnames_date.append((stubdate, None))
            title.culture.append((stubdate, None))
            title.faith.append((stubdate, None))
            title.special.append((stubdate, None))
            title.special_slot.append((stubdate, None))

            title.color = cwtitle.color
            title.province = cwtitle.province
            if title.province:
                title.province = cwtitle.province.token

            title.capital = cwtitle.capital
            for item in cwtitle.cultural_names:
                namelist = item.name
                value = item.values.token
                if value not in title.altnames:
                    title.altnames[value] = []
                if namelist not in title.altnames[value]:  # set messes up order
                    title.altnames[value].append(namelist)

            if title.name in CWHistoryTitle.ALL:
                title.title_history = CWHistoryTitle.ALL[title.name].dates
            if title.province in CWHistoryProvince.ALL:
                title.province_history = CWHistoryProvince.ALL[title.province].dates

            title.can_create = cwtitle.can_create

    @classmethod
    def after_initialize(cls):
        # Resolve History
        # Development Applied from Parent goes down to all children
        # Only apply to de jure
        # Lower Ranked first

        # Compares two dates, returns the bigger one
        # matching conditions
        def compare_history(
            field: str, title: Title, base: CWHistoryDate, limit: str, province: bool
        ):
            comparision_date = base
            if province:
                dates = title.province_history
            else:
                dates = title.title_history
            for date in dates:
                if date.__dict__[field] is None:
                    continue
                if date > STARTING_DATES[limit]:
                    continue
                if date < comparision_date:
                    continue  # dates defined later have priority
                comparision_date = date
            return comparision_date

        print("Resolving de jure")
        # Resolve de jures
        for rank in cls.RANKS:
            for title in cls.RANK[rank]:
                for starting_date in STARTING_DATES:
                    comparision_date = compare_history(
                        "de_jure_liege",
                        title,
                        title.parent[-1][0],
                        starting_date,
                        False,
                    )
                    if comparision_date.de_jure_liege is not None:
                        if type(comparision_date.de_jure_liege) is Token:
                            if comparision_date.de_jure_liege.token != 0:
                                raise Exception(
                                    f"Unexpected Value {comparision_date.de_jure_liege}"
                                )
                            title.parent.append((comparision_date, None))
                        else:
                            title.parent.append(
                                (
                                    comparision_date,
                                    comparision_date.de_jure_liege,
                                )
                            )
                    else:
                        title.parent.append(title.parent[-1])

        print("Resolving children")
        # Resolve children, bigger to smaller pool
        for rank in range(len(cls.RANKS)):
            if cls.RANKS[rank] == CWTitle.EMPIRE:
                continue  # empire is children of none
            for child_title in cls.RANK[cls.RANKS[rank]]:
                for index in range(len(STARTING_DATES) + 1):
                    parent_title = child_title.parent[index][1]  # CWTitle
                    if parent_title is None:
                        continue  # de_jure_liege = 0
                    parent_title = cls.ALL[parent_title.name]  # Title
                    child_title.parent[index] = (
                        child_title.parent[index][0],
                        parent_title,
                    )
                    parent_title.children[index].append(child_title)

        print("Resolving capital")
        for rank in range(len(cls.RANKS)):
            if cls.RANKS[rank] == CWTitle.EMPIRE:
                continue  # barony has no capital
            for title in cls.RANK[cls.RANKS[rank]]:
                if title.capital is not None:
                    title.capital = cls.ALL[title.capital.name]

        print("Resolving development and alternative date names")
        # Resolve development, top to bottom
        for rank in reversed(range(len(cls.RANKS))):
            if cls.RANKS[rank] == CWTitle.BARONY:
                continue  # barony has no development
            for title in cls.RANK[cls.RANKS[rank]]:
                for index, starting_date in enumerate(STARTING_DATES):
                    # Development
                    comparision_date = compare_history(
                        "change_development_level",
                        title,
                        title.development[index + 1][0],
                        starting_date,
                        False,
                    )
                    if comparision_date.change_development_level is not None:
                        title.development[index + 1] = (
                            comparision_date,
                            comparision_date.change_development_level.token,
                        )
                    else:
                        title.development[index + 1] = title.development[index]
                    if title.rank != CWTitle.COUNTY:
                        # barony has no development
                        for child_title in title.children[index + 1]:
                            # top to bottom, pass development to children
                            child_title.development[index + 1] = title.development[
                                index + 1
                            ]

                    # Alternative Name
                    # 'reset_name = yes' can be ignored for the wiki
                    # Modification from compare_history function
                    comparision_date = title.altnames_date[-1][0]
                    datename = None
                    for date in title.title_history:
                        if date > STARTING_DATES[starting_date]:
                            continue
                        if date < comparision_date:
                            continue  # dates defined later have priority
                        if date.name is not None:
                            comparision_date = date
                            datename = comparision_date.name.token
                        elif date.effect is not None:
                            if type(date.effect[0]) is not CWObject:
                                continue
                            effect = date.effect[0]
                            if effect.name != "set_title_name":
                                continue
                            comparision_date = date
                            datename = effect.values.token
                    if datename is not None:
                        title.altnames_date.append((comparision_date, datename))
                    else:
                        title.altnames_date.append(title.altnames_date[-1])

        print("Resolving baronies values")
        for title in cls.RANK[CWTitle.BARONY]:
            for starting_date in STARTING_DATES:
                # Culture
                comparision_date = compare_history(
                    "culture", title, title.culture[-1][0], starting_date, True
                )
                if comparision_date.culture is not None:
                    title.culture.append((comparision_date, comparision_date.culture))
                else:
                    title.culture.append(title.culture[-1])

                # Faith
                comparision_date = compare_history(
                    "religion", title, title.faith[-1][0], starting_date, True
                )
                if comparision_date.religion is not None:
                    title.faith.append((comparision_date, comparision_date.religion))
                else:
                    title.faith.append(title.faith[-1])

                # Special Building
                comparision_date = compare_history(
                    "special_building", title, title.special[-1][0], starting_date, True
                )
                if comparision_date.special_building is not None:
                    title.special.append(
                        (comparision_date, comparision_date.special_building)
                    )
                else:
                    title.special.append(title.special[-1])

                # Special Building Slot
                comparision_date = compare_history(
                    "special_building_slot",
                    title,
                    title.special_slot[-1][0],
                    starting_date,
                    True,
                )
                if comparision_date.special_building_slot is not None:
                    title.special_slot.append(
                        (comparision_date, comparision_date.special_building_slot)
                    )
                else:
                    title.special_slot.append(title.special_slot[-1])

                    # effect = { set_title_name = c_lower_silesia }

            # Check if county capital
            county = cls.ALL[title.parent[0][1].name]
            if title.name == county.capital.name:
                county.culture = title.culture
                county.faith = title.faith

            # Add extra special buildings
            if title.name in EXTRA_SPECIAL_MAPPING:
                specials = [value[1] for value in title.special]
                specials += [value[1] for value in title.special_slot]
                specials = set(specials)
                if len(specials) == 1:  # None is always present
                    # baronies with a special building are skipped
                    building = CWBuilding.ALL[
                        EXTRA_SPECIAL_MAPPING[title.name][0]
                    ]  # first one wins
                    for index in range(len(STARTING_DATES) + 1):
                        title.special[index] = (title.special[index][0], building)


Title.initialize()
Title.after_initialize()


def get_altnames(title: Title) -> str:
    altnames = {}
    for altname in title.altnames:
        if altname in CWLoc.ALL:
            localtname = CWLoc[altname].value
        else:
            localtname = CWLoc[altname].value
        altnames[localtname] = []
        for namelist in title.altnames[altname]:
            altnames[localtname].append(CWLoc[namelist].value)
        altnames[localtname] = ", ".join(altnames[localtname])
    altnames = "<br>".join([f"{key} ({value})" for key, value in altnames.items()])

    datealtnames = []
    for index, starting_date in enumerate(STARTING_DATES):
        if title.altnames_date[index + 1][1] is None:
            continue
        if title.altnames_date[index + 1][1] == title.altnames_date[index][1]:
            continue  # no repeats
        datealtnames.append(
            f"{CWLoc[title.altnames_date[index+1][1]].value} ({starting_date.split(".")[0]})"
        )
    datealtnames = "<br>".join(datealtnames)
    if datealtnames:
        if altnames:
            return f"{datealtnames}<br>{altnames}"
        else:
            return datealtnames
    else:
        if altnames:
            return altnames
        else:
            return ""


def list_of_couties():
    # https://ck3.paradoxwikis.com/List_of_counties
    TABLE = """{{| class="wikitable sortable" style="text-align: left;"
! colspan="2" rowspan="2" | County
! rowspan="2" | [[List_of_duchies|Duchy]]
! colspan="3" | [[List_of_kingdoms|Kingdom]]
! colspan="3" | [[List_of_empires|Empire]]
! rowspan="2" | [[Barony|Baronies]]
! colspan="3" | [[Development]]
! rowspan="2" | [[Special buildings|Special Buildings]]
! colspan="3" | [[Culture]]
! colspan="3" | [[Religion]]
! rowspan="2" | Alternative Names
! rowspan="2" | ID
|-
! 867 !! 1066 !! 1178
! 867 !! 1066 !! 1178
! 867 !! 1066 !! 1178
! 867 !! 1066 !! 1178
! 867 !! 1066 !! 1178
{ROWS}
|}}"""
    TABLEROW = """|- id="{NAME}"
{{{{title with color|{NAME}|{RED}|{GREEN}|{BLUE}}}}}
|{DUCHY}||{KINGDOM867}||{KINGDOM1066}||{KINGDOM1178}||{EMPIRE867}||{EMPIRE1066}||{EMPIRE1178}
|align="right"|{BARONIES}||align="right"|{DEVELOPMENT867}||align="right"|{DEVELOPMENT1066}||align="right"|{DEVELOPMENT1178}
|{SPECIAL}||{CULTURE867}||{CULTURE1066}||{CULTURE1178}||{RELIGION867}||{RELIGION1066}||{RELIGION1178}||{ALTNAMES}||{ID}
"""

    wrows = []
    for title in Title.RANK[CWTitle.COUNTY]:
        color = title.color.rgb()

        specials = []
        for child_title in title.children[1]:
            barony_specials = [value[1] for value in child_title.special]
            barony_specials += [value[1] for value in child_title.special_slot]
            barony_specials = [
                building.building_line[0]
                for building in barony_specials
                if building is not None
            ]
            specials += set(barony_specials)
        specials = "<br>".join(
            [CWLoc[f"building_{building.name}"].value for building in specials]
        )

        wrow = TABLEROW.format(
            NAME=CWLoc[title.name].value,
            RED=color[0],
            GREEN=color[1],
            BLUE=color[2],
            # --
            DUCHY=CWLoc[title.parent[1][1].name].value,  # 867 Value
            # --
            KINGDOM867=CWLoc[title.parent[1][1].parent[1][1].name].value,
            KINGDOM1066=CWLoc[title.parent[2][1].parent[2][1].name].value,
            KINGDOM1178=CWLoc[title.parent[3][1].parent[3][1].name].value,
            # --
            EMPIRE867=CWLoc[title.parent[1][1].parent[1][1].parent[1][1].name].value,
            EMPIRE1066=CWLoc[title.parent[2][1].parent[2][1].parent[2][1].name].value,
            EMPIRE1178=CWLoc[title.parent[3][1].parent[3][1].parent[3][1].name].value,
            # --
            BARONIES=len(title.children[1]),
            DEVELOPMENT867=title.development[1][1],
            DEVELOPMENT1066=title.development[2][1],
            DEVELOPMENT1178=title.development[3][1],
            # --
            SPECIAL=specials,
            RELIGION867=CWLoc[title.faith[1][1].name].value,
            RELIGION1066=CWLoc[title.faith[2][1].name].value,
            RELIGION1178=CWLoc[title.faith[3][1].name].value,
            # --
            CULTURE867=CWLoc[title.culture[1][1].name].value,
            CULTURE1066=CWLoc[title.culture[2][1].name].value,
            CULTURE1178=CWLoc[title.culture[3][1].name].value,
            # --
            ALTNAMES=get_altnames(title),
            ID=title.name,
        )
        wrows.append(wrow)

    with open("wikifiles/wikitable_counties.txt", "w", encoding="utf8") as f:
        content = TABLE.format(ROWS="".join(wrows))
        f.write(content)


def list_of_duchies():
    # https://ck3.paradoxwikis.com/List_of_duchies
    TABLE = """{{| class="wikitable sortable" style="text-align: left;"
! colspan="2" rowspan="2" | Duchy
! colspan="3" | [[List_of_kingdoms|Kingdom]]
! colspan="3" | [[List_of_empires|Empire]]
! rowspan="2" | [[List_of_counties|Counties]]
! rowspan="2" | [[Barony|Baronies]]
! colspan="3" | [[County#Development|Average Development]]
! rowspan="2" | [[Special buildings|Special Buildings]]
! rowspan="2" | Alternative Names
! rowspan="2" | Capital
! rowspan="2" | ID
|-
! rowspan="2" | 867 !! rowspan="2" | 1066 !! rowspan="2" | 1178
! rowspan="2" | 867 !! rowspan="2" | 1066 !! rowspan="2" | 1178
! rowspan="2" | 867 !! rowspan="2" | 1066 !! rowspan="2" | 1178
{ROWS}
|}}"""

    TABLEROW = """|- id="{NAME}"
{{{{title with color|{NAME}|{RED}|{GREEN}|{BLUE}}}}}
|{KINGDOM867}||{KINGDOM1066}||{KINGDOM1178}||{EMPIRE867}||{EMPIRE1066}||{EMPIRE1178}
|align="right"|{COUNTIES}||align="right"|{BARONIES}
|align="right"|{DEV_AVG867}||align="right"|{DEV_AVG1066}||align="right"|{DEV_AVG1178}
|{SPECIAL}||{ALTNAMES}||{CAPITAL}||{ID}
"""

    def counties_dev(title: Title, index: int):
        dev = []
        for child_title in title.children[index]:
            dev.append(child_title.development[index][1])
        return dev

    wrows = []
    for title in Title.RANK[CWTitle.DUCHY]:
        children = set(sum(title.children, []))
        if len(children) == 0:
            # hof titles, adventurer titles, estates, etc
            continue  # no counties in any starting date

        color = title.color.rgb()

        specials = []
        for county_title in title.children[1]:  # 867
            for barony_title in county_title.children[1]:
                barony_specials = [value[1] for value in barony_title.special]
                barony_specials += [value[1] for value in barony_title.special_slot]
                barony_specials = [
                    building.building_line[0]
                    for building in barony_specials
                    if building is not None
                ]
                specials += set(barony_specials)
        specials = "<br>".join(
            [CWLoc[f"building_{building.name}"].value for building in specials]
        )

        dev867 = counties_dev(title, 1)
        dev1066 = counties_dev(title, 2)
        dev1178 = counties_dev(title, 3)

        wrow = TABLEROW.format(
            NAME=CWLoc[title.name].value,
            RED=color[0],
            GREEN=color[1],
            BLUE=color[2],
            # --
            KINGDOM867=CWLoc[title.parent[1][1].name].value,
            KINGDOM1066=CWLoc[title.parent[2][1].name].value,
            KINGDOM1178=CWLoc[title.parent[3][1].name].value,
            # --
            EMPIRE867=CWLoc[title.parent[1][1].parent[1][1].name].value,
            EMPIRE1066=CWLoc[title.parent[2][1].parent[2][1].name].value,
            EMPIRE1178=CWLoc[title.parent[3][1].parent[3][1].name].value,
            # --
            COUNTIES=len(title.children[1]),
            BARONIES=sum([len(child.children[1]) for child in title.children[1]]),
            # --
            DEV_AVG867=int(sum(dev867) / len(dev867)),
            DEV_AVG1066=int(sum(dev1066) / len(dev1066)),
            DEV_AVG1178=int(sum(dev1178) / len(dev1178)),
            # --
            SPECIAL=specials,
            ALTNAMES=get_altnames(title),
            CAPITAL=CWLoc[title.capital.name].value,
            ID=title.name,
        )
        wrows.append(wrow)

    with open("wikifiles/wikitable_duchies.txt", "w", encoding="utf8") as f:
        content = TABLE.format(ROWS="".join(wrows))
        f.write(content)


def list_of_kingdoms():
    # https://ck3.paradoxwikis.com/List_of_kingdoms
    TABLE = """{{| class="wikitable sortable" style="text-align: left;"
! colspan="2" rowspan="2" | Kingdom
! colspan="3" | [[List_of_empires|Empire]]
! colspan="3" | [[List_of_duchies|Duchies]]
! rowspan="2" | [[List_of_counties|Counties]]
! rowspan="2" | Special Requirements
! rowspan="2" | AI Requirements
! rowspan="2" | Alternative Names
! rowspan="2" | Capital
! rowspan="2" | ID
|-
! rowspan="2" | 867 !! rowspan="2" | 1066 !! rowspan="2" | 1178
! rowspan="2" | 867 !! rowspan="2" | 1066 !! rowspan="2" | 1178
! rowspan="2" | 867 !! rowspan="2" | 1066 !! rowspan="2" | 1178
{ROWS}
|}}"""

    TABLEROW = """|- id="{NAME}"
{{{{title with color|{NAME}|{RED}|{GREEN}|{BLUE}}}}}
|{EMPIRE867}||{EMPIRE1066}||{EMPIRE1178}
|align="right"|{DUCHY867}||align="right"|{DUCHY1066}|align="right"|{DUCHY1178}
|align="right"|{COUNTY867}||align="right"|{COUNTY1066}||align="right"|{COUNTY1178}
|{SPECIAL_REQ}||{AI_REQ}||{ALTNAMES}||{CAPITAL}||{ID}
"""

    def get_name(title: Title | None) -> str:
        if title is None:
            return ""
        return CWLoc[title.name].value

    wrows = []
    for title in Title.RANK[CWTitle.KINGDOM]:
        children = set(sum(title.children, []))
        if len(children) == 0:
            # hof titles, formable, etc
            continue  # no duchies in any starting date

        color = title.color.rgb()

        wrow = TABLEROW.format(
            NAME=CWLoc[title.name].value,
            RED=color[0],
            GREEN=color[1],
            BLUE=color[2],
            # --
            EMPIRE867=get_name(title.parent[1][1]),
            EMPIRE1066=get_name(title.parent[2][1]),
            EMPIRE1178=get_name(title.parent[3][1]),
            # --
            DUCHY867=len(title.children[1]),
            DUCHY1066=len(title.children[2]),
            DUCHY1178=len(title.children[3]),
            # --
            COUNTY867=sum([len(duchy.children[1]) for duchy in title.children[1]]),
            COUNTY1066=sum([len(duchy.children[2]) for duchy in title.children[2]]),
            COUNTY1178=sum([len(duchy.children[3]) for duchy in title.children[3]]),
            # --
            SPECIAL_REQ="TEST",
            AI_REQ="AI TEST",
            # --
            ALTNAMES=get_altnames(title),
            CAPITAL=CWLoc[title.capital.name].value,
            ID="",
        )
        wrows.append(wrow)

    with open("wikifiles/wikitable_kingdoms.txt", "w", encoding="utf8") as f:
        content = TABLE.format(ROWS="".join(wrows))
        f.write(content)

    pass


list_of_couties()
list_of_duchies()

pass
