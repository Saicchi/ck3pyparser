import pathlib
import copy
from cwparser import *

BASEPATH = pathlib.Path(
    r"C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game"
)


def load_loc(file: pathlib.Path) -> dict:
    locs = {}
    for cwloc in parse_file_yml(read_file(file)):
        if cwloc.name in locs:
            raise Exception(f"Duplicate Loc: {cwloc.name}")
        locs[cwloc.name] = cwloc
    return locs


class CWItem:
    PATH = BASEPATH
    PATH_LOC = BASEPATH
    ALL: dict[str, "CWItem"] = {}
    LOC: dict[str, CWLocalization] = {}

    def __init__(self):
        self.raw = None
        self.name = None
        # Default Values Here
        self.error("__init__ called")

    def __repr__(self):
        return self.name

    @classmethod
    def handle_object(cls, _: CWObject):
        cls.error("handle_object not implemented")

    @classmethod
    def after_load(cls):
        pass

    @classmethod
    def load_files(cls):
        if cls.PATH.is_file():
            files = [cls.PATH]
        else:
            files = cls.PATH.glob("*.txt")
        for file in files:
            print(f"<{cls.__name__}> Reading: {file.relative_to(BASEPATH)}")
            tokens = tokenize(read_file(file), file)
            cwobjects = parse_group(tokens)
            for cwobject in cwobjects:
                cls.handle_object(cwobject)
        cls.after_load()
        cls.load_localization()

    @classmethod
    def load_localization(cls):
        if cls.PATH_LOC == BASEPATH:
            return  # do not load all files!!!
        if cls.PATH_LOC.is_file():
            files = [cls.PATH_LOC]
        else:
            files = cls.PATH_LOC.glob("*.yml")
        for file in files:
            print(f"<{cls.__name__}> Reading: {file.relative_to(BASEPATH)}")
            cwlocs = parse_file_yml(read_file(file))
            for cwloc in cwlocs:
                if cwloc.name in cls.LOC:
                    cls.error(f"Duplicate Loc: {cwloc.name}")
                cls.LOC[cwloc.name] = cwloc

    @classmethod
    def error(cls, message: str):
        raise Exception(f"<{cls.__name__}> {message}")

    @classmethod
    def serialize(cls):
        cls.error("serialize not implemented")

    @classmethod
    def deserialize(cls):
        cls.error("deserialize not implemented")


class CWLocal(CWItem):
    ALL: dict[str, "CWLocal"] = {}

    def __init__(self):
        self.raw = None
        self.name = None
        self.value = None

    @classmethod
    def load(cls):
        raise Exception(f"<{cls.__name__}> load called")

    @classmethod
    def handle_object(cls, cwobject: CWObject):
        if cwobject.token.type != Token.LOCAL:
            cls.error(f"Token not Local: {repr(cwobject.token)}")
        filename = cwobject.token.filename
        if filename is None:
            cls.error("local variable with null filename")
        if filename not in cls.ALL:
            cls.ALL[filename] = []
        cwitem = cls()
        cwitem.raw = cwobject
        cwitem.name = cwobject.token.token
        cwitem.value = cwobject.values
        cls.ALL[filename].append(cwobject)


class CWColor(CWItem):
    PATH = CWItem.PATH.joinpath("common/named_colors")
    ALL: dict[str, "CWColor"] = {}

    # Types
    REGULAR = "REGULAR"
    HSV = "HSV"
    HSV360 = "HSV360"

    def __init__(self):
        self.raw: CWObject = None
        self.name: str = None
        self.values: list[Token] = []
        self.type: str = None
        # REGULAR - NUMBER or FLOAT * 255
        # HSV - NUMBER or FLOAT * 360

    def __repr__(self):
        return self.name if self.name else "NONAME"

    def rgb() -> tuple:
        # todo implement this
        pass

    @staticmethod
    def get_color(cwobject: CWObject) -> "CWColor":
        # For calling from outside
        # color = { 255 255 255 } color = hsv { 0.1 0.1 0.1 }
        cwcolor = CWColor()
        colors = cwobject.get("color", return_value=False)
        if colors is None:
            cwcolor.values = [Token("255"), Token("255"), Token("255")]
            cwcolor.type = CWColor.REGULAR
            return cwcolor

        if type(colors.values) is Token:
            if colors.values.token == "hsv":
                cwcolor.type == CWColor.HSV
            elif colors.values.token == "hsv360":
                cwcolor.type == CWColor.HSV360
            else:  # reference
                return CWColor.ALL[colors.values.token]
            colors = CWObject.ALL[colors.index + 1]

        if len(colors.values[0].values) != 3:
            cwcolor.error("amount of values in colors incorect")
        for item in colors.values[0].values:
            if item.type != Token.NUMBER:
                cwcolor.error(f"Token not a number: {repr(item)}>{item.filename}")
            cwcolor.values.append(item)
        return cwcolor

    @classmethod
    def handle_object(cls, cwobject: CWObject):
        if cwobject.token.type == Token.LOCAL:
            CWLocal.handle_object(cwobject)
            return
        elif cwobject.token.type != Token.IDENTIFIER:
            cls.error(f"Token not Identifier: {repr(cwobject.token)}")

        if cwobject.token.token != "colors":
            cls.error("colors object not found")
        if len(cwobject.values) == 0:
            cls.error("colors object empty")

        index = 0
        while index < len(cwobject.values):
            #  red = hsv  { 0.1 0.5 0.3 }  blue = { 10 15 255 }
            # | -- 0 -- | | ---- 1 ---- | | ------- 2 ------- |
            color = cwobject.values[index]
            if color.token is None:
                cls.error("token without name when there should be one")

            cwitem = cls()
            cwitem.name = color.token.token
            if cwitem.name in cls.ALL:
                cls.error(f"duplicate color: {cwitem.name}")
            cls.ALL[cwitem.name] = cwitem

            if type(color.values) == Token:
                if color.values.token == "hsv":
                    cwitem.type = cls.HSV
                elif color.values.token == "hsv360":
                    cwitem.type = cls.HSV360
                else:
                    cls.error(f"non supported color type: {color.values.token}")
                index += 1
                color = cwobject.values[index]
            else:
                cwitem.type = cls.REGULAR
            index += 1

            if len(color.values[0].values) != 3:
                cls.error("amount of values in colors incorect")
            for item in color.values[0].values:
                if item.type != Token.NUMBER:
                    cls.error(f"token not a number: {repr(item)}>{item.filename}")
                cwitem.values.append(item)


class CWTitle(CWItem):
    PATH = CWItem.PATH.joinpath("common/landed_titles")
    PATH_LOC = CWItem.PATH.joinpath("localization/english/titles_l_english.yml")
    ALL: dict[str, "CWTitle"] = {}
    PROVINCES: dict[int, "CWTitle"] = {}

    # Ranks
    BARONY = "BARONY"
    COUNTY = "COUNTY"
    DUCHY = "DUCHY"
    KINGDOM = "KINGDOM"
    EMPIRE = "EMPIRE"

    # Rank Prefix
    RANKS = {
        "e_": EMPIRE,
        "k_": KINGDOM,
        "d_": DUCHY,
        "c_": COUNTY,
        "b_": BARONY,
    }

    def __init__(self):
        self.raw: CWObject = None
        self.name: str = None
        self.rank: str = None
        self.parents: list[CWTitle] = []
        self.children: list[CWTitle] = []
        self.color: CWColor = None
        self.landless: Token = None
        self.destroy_if_invalid_heir: Token = None
        self.no_automatic_claims: Token = None
        self.definite_form: Token = None
        self.always_follows_primary_heir: Token = None
        self.ruler_uses_title_name: Token = None
        self.can_be_named_after_dynasty: Token = None
        self.province: Token = None
        self.capital: CWTitle = None
        self.de_jure_drift_disabled: Token = None
        self.male_names: list[Token] = []
        self.female_names: list[Token] = []
        self.ai_primary_priority: CWObject = None
        self.can_create: CWObject = None
        self.can_create_on_partition: CWObject = None
        self.can_destroy: CWObject = None
        self.cultural_names: list[Token] = []

    @staticmethod
    def rank_from_name(name: str):
        if name[:2] not in CWTitle.RANKS:
            CWItem.error(f"Rank not found: {name}")
        return CWTitle.RANKS[name[:2]]

    def __recurse_find_first_county(self) -> "CWTitle":
        if self.rank in (CWTitle.BARONY, CWTitle.COUNTY):
            self.error("recursive hit invalid title rank")
        for child in self.children:
            if child.rank == CWTitle.COUNTY:
                return child
            recurse_capital = child.__recurse_find_first_county()
            if recurse_capital is not None:
                return recurse_capital
        return None

    @classmethod
    def after_load(cls):
        # Resolve Capital
        for title in cls.ALL.values():
            if title.capital:
                title.capital = cls.ALL[title.capital.token]
            else:
                if len(title.children) == 0:
                    continue
                if title.rank == cls.BARONY:
                    continue
                if title.rank == cls.COUNTY:
                    title.capital = title.children[0]  # first defined barony
                    continue
                title.capital = title.__recurse_find_first_county()

    @classmethod
    def handle_object(cls, cwobject: CWObject, parent: "CWTitle" = None):
        if cwobject.token.type == Token.LOCAL:
            CWLocal.handle_object(cwobject)
            return
        elif cwobject.token.type != Token.IDENTIFIER:
            cls.error(f"Token not Identifier: {repr(cwobject.token)}")

        cwitem = cls()
        cwitem.raw = cwobject
        cwitem.name = cwobject.token.token
        cwitem.rank = cls.rank_from_name(cwitem.name)
        if parent:
            cwitem.parents = parent.parents.copy()
            if parent in cwitem.parents:
                cls.error(f"{parent.name} parent duplicate for child {cwitem.name}")
            cwitem.parents.append(parent)
            if cwitem in parent.children:
                cls.error(f"{cwitem.name} child duplicate for parent {parent.name}")
            parent.children.append(cwitem)

        if cwitem.name in cls.ALL:
            cls.error(f"Duplicate Title: {cwitem.name}")
        cls.ALL[cwitem.name] = cwitem

        cwitem.color = CWColor.get_color(cwobject)

        # There are missing entries here on purpose
        # as they are not used in the game code
        cwitem.landless = cwobject.get("landless", default_value=Token("no"))
        cwitem.destroy_if_invalid_heir = cwobject.get(
            "destroy_if_invalid_heir", default_value=Token("no")
        )
        cwitem.no_automatic_claims = cwobject.get(
            "no_automatic_claims", default_value=Token("no")
        )
        cwitem.definite_form = cwobject.get("definite_form", default_value=Token("no"))
        cwitem.always_follows_primary_heir = cwobject.get(
            "always_follows_primary_heir", default_value=Token("no")
        )
        cwitem.ruler_uses_title_name = cwobject.get(
            "ruler_uses_title_name", default_value=Token("yes")
        )
        cwitem.can_be_named_after_dynasty = cwobject.get(
            "can_be_named_after_dynasty", default_value=Token("yes")
        )

        province = cwobject.get("province", allow_multiple=True)
        if province is not None:
            if cwitem.rank != CWTitle.BARONY:
                cls.error(f"{cwitem.rank} has defined province")
            cwitem.province = province[-1].values
            if cwitem.province.token in cls.PROVINCES:
                cls.error(f"Duplicate Province: {cwitem.province}")
            cls.PROVINCES[cwitem.province.token] = cwitem

        cwitem.capital = cwobject.get("capital")  # Handled Later
        cwitem.de_jure_drift_disabled = cwobject.get(
            "de_jure_drift_disabled", default_value=Token("no")
        )
        cwitem.male_names = cwobject.get("male_names", default_value=cwitem.male_names)
        cwitem.female_names = cwobject.get(
            "female_names", default_value=cwitem.female_names
        )
        cwitem.ai_primary_priority = cwobject.get(
            "ai_primary_priority", default_value=cwitem.ai_primary_priority
        )
        cwitem.can_create = cwobject.get("can_create", default_value=cwitem.can_create)
        cwitem.can_create_on_partition = cwobject.get(
            "can_create_on_partition", default_value=cwitem.can_create_on_partition
        )
        cwitem.can_destroy = cwobject.get(
            "can_destroy", default_value=cwitem.can_destroy
        )
        cwitem.cultural_names = cwobject.get(
            "cultural_names", default_value=cwitem.cultural_names
        )

        # Nested Titles
        for value in cwobject.values:
            if value.token and value.token.token[:2] in cls.RANKS:
                cls.handle_object(value, cwitem)


class CWBuilding(CWItem):
    PATH = CWItem.PATH.joinpath("common/buildings")
    PATH_LOC = CWItem.PATH.joinpath("localization/english/buildings_l_english.yml")
    ALL: dict[str, "CWBuilding"] = {}

    def __init__(self):
        self.raw: CWObject = None
        self.name: str = None
        # self.levy: Token = None
        # self.max_garrison: Token = None
        # self.garrison_reinforcement_factor: Token = None
        # self.construction_time: Token = None
        # self.type: Token = None
        # self.asset: list[CWObject] = []
        # self.is_enabled: CWObject = None
        # self.can_construct_potential: CWObject = {}
        # self.can_construct_showing_failures_only: CWObject = {}
        # self.can_construct: CWObject = {}
        # self.show_disabled: Token = None
        # self.cost: CWObject = None
        self.next_building: CWBuilding = None
        self.building_line: list[CWBuilding] = []
        # self.effect_desc: Token = None
        # self.character_modifier: CWObject = None
        # self.character_culture_modifier: CWObject = None
        # self.character_faith_modifier: CWObject = None
        # self.characer_dynasty_modifier: CWObject = None
        # self.province_modifier: CWObject = None
        # self.province_culture_modifier: CWObject = None
        # self.province_faith_modifier: CWObject = None
        # self.province_terrain_modifier: CWObject = None
        # self.province_dynasty_modifier: CWObject = None
        # self.county_modifier: CWObject = None
        # self.county_culture_modifier: CWObject = None
        # self.county_faith_modifier: CWObject = None
        # self.duchy_capital_county_modifier: CWObject = None
        # self.duchy_capital_county_culture_modifier: CWObject = None
        # self.duchy_capital_county_faith_modifier: CWObject = None
        # self.county_holding_modifier: CWObject = None
        # self.county_dynasty_modifier: CWObject = None
        # self.county_holder_character_modifier: CWObject = None
        # self.flag: Token = None
        # self.on_complete: CWObject = None
        # self.ai_value: CWObject = None
        # self.is_graphical_background: Token = None
        # self.on_start: CWObject = None
        # self.on_cancelled: CWObject = None
        # self.on_complete: CWObject = None

    @classmethod
    def handle_object(cls, cwobject: CWObject):
        if cwobject.token.type == Token.LOCAL:
            CWLocal.handle_object(cwobject)
            return
        elif cwobject.token.type != Token.IDENTIFIER:
            cls.error(f"Token not Identifier: {repr(cwobject.token)}")

        cwitem = cls()
        cwitem.raw = cwobject
        cwitem.name = cwobject.token.token
        if cwitem.name in cls.ALL:
            cls.error(f"Duplicate Building: {cwitem.name}")
        cls.ALL[cwitem.name] = cwitem

        next_buildings = cwobject.get(
            "next_building", allow_multiple=True, default_value=[]
        )
        next_buildings = list(
            set([building.values.token for building in next_buildings])
        )
        if len(next_buildings) == 0:
            cwitem.next_building = None
        elif len(next_buildings) != 1:
            cls.error(f"multiple next buildings: {next_buildings}")
        else:
            cwitem.next_building = next_buildings[0]

    @classmethod
    def after_load(cls):
        # Resolve Next Building
        for building in cls.ALL.values():
            building.next_building = CWBuilding.ALL[building.name]


class CWTradition(CWItem):
    PATH = CWItem.PATH.joinpath("common/culture/traditions")
    ALL: dict[str, "CWTradition"] = {}

    def __init__(self):
        self.raw: CWObject = None
        self.name: str = None
        self.category: Token = None
        self.layers: list[CWObject] = []
        self.is_shown: CWObject = None
        self.can_pick: CWObject = None
        self.parameters: list[CWObject] = []
        self.character_modifier: list[CWObject] = []
        self.province_modifier: list[CWObject] = []
        self.county_modifier: list[CWObject] = []
        self.doctrine_character_modifier: list[CWObject] = []
        self.culture_modifier: list[CWObject] = []
        self.cost: CWObject = None
        self.ai_will_do: CWObject = None

    @classmethod
    def handle_object(cls, cwobject: CWObject):
        if cwobject.token.type == Token.LOCAL:
            CWLocal.handle_object(cwobject)
            return
        elif cwobject.token.type != Token.IDENTIFIER:
            cls.error(f"Token not Identifier: {repr(cwobject.token)}")

        cwitem = cls()
        cwitem.raw = cwobject
        cwitem.name = cwobject.token.token

        if cwitem.name in cls.ALL:
            cls.error(f"Duplicate Title: {cwitem.name}")
        cls.ALL[cwitem.name] = cwitem

        cwitem.category = cwobject.get("category")
        if cwitem.category is None:
            cls.error("null category")

        cwitem.layers = cwobject.get("category")
        if cwitem.layers is None:
            cls.error("null layers")

        cwitem.is_shown = cwobject.get("is_shown")
        cwitem.can_pick = cwobject.get("can_pick")

        cwitem.parameters = cwobject.get("parameters", default_value=[])
        cwitem.character_modifier = cwobject.get("character_modifier", default_value=[])
        cwitem.province_modifier = cwobject.get("province_modifier", default_value=[])
        cwitem.county_modifier = cwobject.get("county_modifier", default_value=[])
        cwitem.doctrine_character_modifier = cwobject.get(
            "doctrine_character_modifier", allow_multiple=True, default_value=[]
        )
        cwitem.culture_modifier = cwobject.get("culture_modifier", default_value=[])

        cwitem.cost = cwobject.get("cost")
        cwitem.ai_will_do = cwobject.get("ai_will_do")


class CWCulture(CWItem):
    PATH = CWItem.PATH.joinpath("common/culture/cultures")
    PATH_LOC = CWItem.PATH.joinpath(
        "localization/english/culture/cultures_l_english.yml"
    )
    ALL: dict[str, "CWCulture"] = {}

    def __init__(self):
        self.raw: CWObject = None
        self.name: str = None
        self.color: CWColor = None
        self.created: Token = None
        self.history_loc_override: Token = None
        self.traditions: list[CWTradition] = []
        self.ethos: Token = None
        self.heritage: Token = None
        self.language: Token = None
        self.name_list: Token = None
        self.dlc_tradition: list[CWObject] = []
        self.ethnicities: list[CWObject] = []

    @classmethod
    def handle_object(cls, cwobject: CWObject):
        if cwobject.token.type == Token.LOCAL:
            CWLocal.handle_object(cwobject)
            return
        elif cwobject.token.type != Token.IDENTIFIER:
            cls.error(f"Token not Identifier: {repr(cwobject.token)}")

        cwitem = cls()
        cwitem.raw = cwobject
        cwitem.name = cwobject.token.token

        if cwitem.name in cls.ALL:
            cls.error(f"Duplicate Title: {cwitem.name}")
        cls.ALL[cwitem.name] = cwitem

        cwitem.color = CWColor.get_color(cwobject)

        cwitem.created = cwobject.get("created")
        cwitem.history_loc_override = cwobject.get("history_loc_override")
        cwitem.traditions = cwobject.get("traditions", default_value=[])
        cwitem.ethos = cwobject.get("ethos")
        cwitem.heritage = cwobject.get("heritage")
        cwitem.language = cwobject.get("language")
        cwitem.name_list = cwobject.get("name_list")
        cwitem.dlc_tradition = cwobject.get(
            "traditions", allow_multiple=True, default_value=[]
        )
        cwitem.ethnicities = cwobject.get("ethnicities", default_value=[])


class CWReligionFamily(CWItem):
    PATH = CWItem.PATH.joinpath("common/religion/religion_families")
    ALL: dict[str, "CWReligionFamily"] = {}

    def __init__(self):
        self.raw: CWObject = None
        self.name: str = None
        self.is_pagan: Token = None

    def __repr__(self):
        return self.name

    @classmethod
    def handle_object(cls, cwobject: CWObject):
        if cwobject.token.type == Token.LOCAL:
            CWLocal.handle_object(cwobject)
            return
        elif cwobject.token.type != Token.IDENTIFIER:
            cls.error(f"Token not Identifier: {repr(cwobject.token)}")

        cwitem = cls()
        cwitem.raw = cwobject
        cwitem.name = cwobject.token.token

        if cwitem.name in cls.ALL:
            cls.error(f"Duplicate Title: {cwitem.name}")
        cls.ALL[cwitem.name] = cwitem
        cwitem.is_pagan = cwobject.get("is_pagan", default_value=Token("no"))

    @classmethod
    def after_load(cls):
        CWFaith.load_localization()


class CWHolySite(CWItem):
    PATH = CWItem.PATH.joinpath("common/religion/holy_sites/00_holy_sites.txt")
    ALL: dict[str, "CWHolySite"] = {}

    def __init__(self):
        self.raw: CWObject = None
        self.name: str = None
        self.county: CWTitle = None
        self.barony: CWTitle = None
        self.character_modifier: str = None

    @classmethod
    def handle_object(cls, cwobject: CWObject) -> "CWFaith":
        if cwobject.token.type == Token.LOCAL:
            CWLocal.handle_object(cwobject)
            return
        elif cwobject.token.type != Token.IDENTIFIER:
            cls.error(f"Token not Identifier: {repr(cwobject.token)}")

        cwitem = cls()
        cwitem.raw = cwobject
        cwitem.name = cwobject.token.token

        if cwitem.name in cls.ALL:
            cls.error(f"Duplicate Holy Site: {cwitem.name}")
        cls.ALL[cwitem.name] = cwitem

        cwitem.county = CWTitle.ALL[cwobject.get("county").token]
        cwitem.barony = cwobject.get("barony")
        if cwitem.barony is not None:
            cwitem.barony = CWTitle.ALL[cwitem.barony.token]
        else:
            cwitem.barony = cwitem.county.capital

        cwitem.character_modifier = cwobject.get("character_modifier")
        return cwitem


class CWFaith(CWItem):
    ALL: dict[str, "CWFaith"] = {}
    PATH_LOC = CWItem.PATH.joinpath("localization/english/religion")

    def __init__(self):
        self.raw: CWObject = None
        self.name: str = None
        self.religion: CWReligion = None
        self.family: CWReligionFamily = None
        self.color: CWColor = None
        self.religious_head: CWTitle = None
        self.holy_site: list[CWObject] = []
        self.doctrine: list[Token] = []

    @classmethod
    def handle_object(cls, cwobject: CWObject, parent: "CWReligion") -> "CWFaith":
        if cwobject.token.type == Token.LOCAL:
            CWLocal.handle_object(cwobject)
            return
        elif cwobject.token.type != Token.IDENTIFIER:
            cls.error(f"Token not Identifier: {repr(cwobject.token)}")

        cwitem = cls()
        cwitem.raw = cwobject
        cwitem.name = cwobject.token.token

        if cwitem.name in cls.ALL:
            cls.error(f"Duplicate Title: {cwitem.name}")
        cls.ALL[cwitem.name] = cwitem

        cwitem.religion = parent
        cwitem.family = parent.family
        cwitem.color = CWColor.get_color(cwobject)

        cwitem.religious_head = cwobject.get("religious_head")
        if cwitem.religious_head is not None:
            cwitem.religious_head = CWTitle.ALL[cwitem.religious_head.token]

        cwitem.holy_site = cwobject.get(
            "holy_site", allow_multiple=True, default_value=[]
        )
        cwitem.holy_site = [
            CWHolySite.ALL[site.values.token] for site in cwitem.holy_site
        ]

        cwitem.doctrine = cwobject.get(
            "doctrine", allow_multiple=True, default_value=[]
        )
        cwitem.doctrine = [doctrine.values for doctrine in cwitem.doctrine]

        return cwitem


class CWReligion(CWItem):
    PATH = CWItem.PATH.joinpath("common/religion/religions")
    ALL: dict[str, "CWReligion"] = {}

    def __init__(self):
        self.raw: CWObject = None
        self.name: str = None
        self.family: CWReligionFamily = None
        self.pagan_roots: Token = None
        self.doctrine: list[Token] = []
        self.traits: CWObject = None
        self.faiths: list = []

    @classmethod
    def handle_object(cls, cwobject: CWObject):
        if cwobject.token.type == Token.LOCAL:
            CWLocal.handle_object(cwobject)
            return
        elif cwobject.token.type != Token.IDENTIFIER:
            cls.error(f"Token not Identifier: {repr(cwobject.token)}")

        cwitem = cls()
        cwitem.raw = cwobject
        cwitem.name = cwobject.token.token

        if cwitem.name in cls.ALL:
            cls.error(f"Duplicate Title: {cwitem.name}")
        cls.ALL[cwitem.name] = cwitem

        cwitem.family = CWReligionFamily.ALL[cwobject.get("family").token]

        cwitem.pagan_roots = cwobject.get("pagan_roots", default_value=Token("no"))
        cwitem.doctrine = cwobject.get(
            "doctrine", allow_multiple=True, default_value=[]
        )
        cwitem.traits = cwobject.get("traits")

        # Faiths
        faiths = cwobject.get("faiths")
        for value in faiths:
            cwitem.faiths.append(CWFaith.handle_object(value, cwitem))


class CWHistoryDate:

    def __init__(self):
        # On conflicting dates, latter defined takes priority
        self.date: Token = None
        self.datenum: int = None
        self.index: int = None  # for priority
        self.from_map: bool = False  # data copied has higher priority
        # Generic
        self.effect: CWObject | Token = None
        # Province
        self.culture: CWCulture = None
        self.religion: CWFaith = None
        self.terrain: Token = None
        self.holding: Token = None
        self.buildings: list[Token] = []
        self.duchy_capital_building: Token = None
        self.special_building: CWBuilding = None
        self.special_building_slot: CWBuilding = None
        # Title
        self.holder: Token = None
        self.de_jure_liege: CWTitle = None
        self.government: Token = None
        self.effect: CWObject = None
        self.name: Token = None
        self.liege: CWTitle = None
        self.change_development_level: Token = None
        self.insert_title_history: Token = None
        self.reset_name: Token = None
        self.succession_laws: CWObject = None
        self.holder_ignore_head_of_faith_requirement: Token = None
        self.remove_succession_laws: Token = None

    def __repr__(self):
        return self.date.token

    def __gt__(self, other):
        if type(other) == type(self):
            return self.datenum > other.datenum
        else:
            return self.datenum > other

    def __ge__(self, other):
        if type(other) == type(self):
            return self.datenum >= other.datenum
        else:
            return self.datenum >= other

    def __lt__(self, other):
        if type(other) == type(self):
            return self.datenum < other.datenum
        else:
            return self.datenum < other

    def __le__(self, other):
        if type(other) == type(self):
            return self.datenum <= other.datenum
        else:
            return self.datenum <= other

    @classmethod
    def handle_object(
        cls, cwobject: CWObject, override_date: Token = None
    ) -> "CWHistoryDate":
        cwitem = cls()
        if override_date is not None:
            if override_date.type != Token.DATE:
                raise Exception(f"override not a date {override_date}")
            cwitem.date = override_date
        else:
            if cwobject.token.type != Token.DATE:
                raise Exception(f"cwobject not a date {repr(cwobject)}")
            cwitem.date = cwobject.token
        splitdate = [int(date) for date in cwitem.date.token.split(".")]
        cwitem.datenum = 10000 * splitdate[0] + 100 * splitdate[1] + splitdate[2]

        # Generic
        cwitem.effect = cwobject.get("effect", allow_multiple=True)

        # Province
        cwitem.culture = cwobject.get("culture", allow_multiple=True)
        if type(cwitem.culture) is list:
            cwitem.culture = CWCulture.ALL[cwitem.culture[-1].values.token]

        cwitem.religion = cwobject.get("religion", allow_multiple=True)
        if type(cwitem.religion) is list:
            cwitem.religion = CWFaith.ALL[cwitem.religion[-1].values.token]

        cwitem.terrain = cwobject.get("terrain", allow_multiple=True)
        if type(cwitem.terrain) is list:
            cwitem.terrain = cwitem.terrain[-1].values.token

        cwitem.holding = cwobject.get("holding", allow_multiple=True)
        if type(cwitem.holding) is list:
            cwitem.holding = cwitem.holding[-1].values.token

        cwitem.buildings = cwobject.get("buildings", allow_multiple=True)
        if type(cwitem.buildings) is list:
            cwitem.buildings = cwitem.buildings[-1].values[0]

        cwitem.duchy_capital_building = cwobject.get(
            "duchy_capital_building", allow_multiple=True
        )
        if type(cwitem.duchy_capital_building) is list:
            cwitem.duchy_capital_building = cwitem.duchy_capital_building[
                -1
            ].values.token

        cwitem.special_building = cwobject.get("special_building", allow_multiple=True)
        if type(cwitem.special_building) is list:
            cwitem.special_building = CWBuilding.ALL[
                cwitem.special_building[-1].values.token
            ]

        cwitem.special_building_slot = cwobject.get(
            "special_building_slot", allow_multiple=True
        )
        if type(cwitem.special_building_slot) is list:
            cwitem.special_building_slot = CWBuilding.ALL[
                cwitem.special_building_slot[-1].values.token
            ]

        # Title
        cwitem.holder = cwobject.get("holder")
        cwitem.de_jure_liege = cwobject.get("de_jure_liege")
        if cwitem.de_jure_liege is not None:
            # de_jure_liege = 0
            if cwitem.de_jure_liege.type in (Token.IDENTIFIER, Token.STRING):
                cwitem.de_jure_liege = CWTitle.ALL[cwitem.de_jure_liege.token]

        cwitem.government = cwobject.get("government")
        cwitem.effect = cwobject.get("effect")
        cwitem.name = cwobject.get("name")
        cwitem.liege = cwobject.get("liege")
        cwitem.change_development_level = cwobject.get("change_development_level")
        cwitem.insert_title_history = cwobject.get("insert_title_history")
        cwitem.reset_name = cwobject.get("reset_name")
        cwitem.succession_laws = cwobject.get("succession_laws")
        cwitem.holder_ignore_head_of_faith_requirement = cwobject.get(
            "holder_ignore_head_of_faith_requirement"
        )
        cwitem.remove_succession_laws = cwobject.get("remove_succession_laws")

        return cwitem


class CWHistoryProvince(CWItem):
    PATH = CWItem.PATH.joinpath("history/provinces")
    ALL: dict[int, "CWHistoryProvince"] = {}
    INDEX = 0

    def __init__(self):
        # First load provinces (low index = lower priority)
        # then load the mapped provinces (higher index = higher priority)
        # for conflict resolution
        self.raw: CWObject = None
        self.index = CWHistoryProvince.INDEX  # matches define order, not number
        self.name: int = None
        self.barony: CWTitle = None
        self.dates: list[CWHistoryDate] = []
        CWHistoryProvince.INDEX += 1

    def __repr__(self):
        return str(self.name)

    @classmethod
    def after_load(cls):
        PATH = CWItem.PATH.joinpath("history/province_mapping")
        files = PATH.glob("*.txt")
        for file in files:
            print(f"<{cls.__name__}> Reading: {file.relative_to(BASEPATH)}")
            tokens = tokenize(read_file(file), file)
            cwobjects = parse_group(tokens)
            for cwobject in cwobjects:
                if cwobject.token.type != Token.NUMBER:
                    cls.error("invalid mapping token type")
                if cwobject.values.type != Token.NUMBER:
                    cls.error("invalid mapping token value")

                cwitem = cls()
                cwitem.raw = cwobject
                cwitem.name = cwobject.token.token
                if cwitem.name not in CWTitle.PROVINCES:
                    continue  # not baronies
                if cwitem.name not in cls.ALL:
                    # duplicates can exist ( province 4345 )
                    # add to existing one
                    cls.ALL[cwitem.name] = cwitem

                cwitem.barony = CWTitle.PROVINCES[cwobject.token.token]
                for date in cls.ALL[cwobject.values.token].dates:
                    newdate = copy.copy(date)
                    newdate.from_map = True
                    cwitem.dates.append(newdate)

    @classmethod
    def handle_object(cls, cwobject: CWObject):
        if cwobject.token.type == Token.LOCAL:
            CWLocal.handle_object(cwobject)
            return
        elif cwobject.token.type != Token.NUMBER:
            cls.error(f"Token not Number: {repr(cwobject.token)}")

        cwitem = cls()
        cwitem.raw = cwobject
        cwitem.name = cwobject.token.token

        if cwitem.name in cls.ALL:
            # duplicates can exist ( province 4345 )
            # first one defined wins
            return
        cls.ALL[cwitem.name] = cwitem

        cwitem.barony = CWTitle.PROVINCES[cwobject.token.token]

        newdate = CWHistoryDate.handle_object(cwobject, Token("1.1.1"))
        newdate.index = cwitem.index
        cwitem.dates.append(newdate)

        for value in cwobject.values:
            if value.token.type not in (Token.NUMBER, Token.DATE):
                continue
            elif value.token.type == Token.NUMBER:
                value.token.transform_into_date()
            newdate = CWHistoryDate.handle_object(value)
            newdate.index = cwitem.index
            cwitem.dates.append(newdate)


class CWHistoryTitle(CWItem):
    PATH = CWItem.PATH.joinpath("history/titles")
    ALL: dict[str, "CWHistoryTitle"] = {}

    def __init__(self):
        self.raw: CWObject = None
        self.name: str = None
        self.title: CWTitle = None
        self.dates: list[CWHistoryDate] = []

    @classmethod
    def handle_object(cls, cwobject: CWObject):
        if cwobject.token.type == Token.LOCAL:
            CWLocal.handle_object(cwobject)
            return
        elif cwobject.token.type != Token.IDENTIFIER:
            cls.error(f"Token not Number: {repr(cwobject.token)}")

        cwitem = cls()
        cwitem.raw = cwobject
        cwitem.name = cwobject.token.token

        if cwitem.name in cls.ALL:
            # append dates
            cwitem = cls.ALL[cwitem.name]
        else:
            cls.ALL[cwitem.name] = cwitem
            cwitem.title = CWTitle.ALL[cwobject.token.token]

        cwitem.dates.append(CWHistoryDate.handle_object(cwobject, Token("1.1.1")))

        for value in cwobject.values:
            if value.token.type not in (Token.NUMBER, Token.DATE):
                continue
            elif value.token.type == Token.NUMBER:
                value.token.transform_into_date()
            cwitem.dates.append(CWHistoryDate.handle_object(value))


class CWCulturalNames(CWItem):
    LOC_FILES = [
        BASEPATH.joinpath(
            "localization/english/culture/culture_name_lists_l_english.yml"
        ),
        BASEPATH.joinpath("localization/english/titles_cultural_names_l_english.yml"),
    ]
    LOC: dict[str, "CWCulturalNames"] = {}

    @classmethod
    def load_files(cls):
        cls.load_localization()

    @classmethod
    def load_localization(cls):
        for file in cls.LOC_FILES:
            print(f"<{cls.__name__}> Reading: {file.relative_to(BASEPATH)}")
            cwlocs = parse_file_yml(read_file(file))
            for cwloc in cwlocs:
                if cwloc.name in cls.LOC:
                    cls.error(f"Duplicate Loc: {cwloc.name}")
                cls.LOC[cwloc.name] = cwloc


def load_items():
    pass


CWColor.load_files()
CWTitle.load_files()
CWBuilding.load_files()
CWTradition.load_files()
CWCulture.load_files()
CWHolySite.load_files()
CWReligionFamily.load_files()
CWReligion.load_files()
CWHistoryProvince.load_files()
CWHistoryTitle.load_files()
CWCulturalNames.load_files()
pass
