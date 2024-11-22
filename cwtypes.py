import pathlib
from cwparser import *

BASEPATH = pathlib.Path(
    r"C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game"
)


class CWItem:
    PATH = BASEPATH.joinpath("")
    ALL: dict[str, "CWItem"] = {}

    def __init__(self):
        # Default Values Here
        self.error("__init__ called")

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
            # files = [pathlib.Path("00_landed_titles.txt")]
        for file in files:
            print(f"<{cls.__name__}> Reading: {file.relative_to(BASEPATH)}")
            tokens = tokenize(file.read_text(encoding="utf-8-sig"), file)
            cwobjects = parse_group(tokens)
            for cwobject in cwobjects:
                cls.handle_object(cwobject)
        cls.after_load()

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
    ALL: dict[str, "CWTitle"] = {}

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

    def __repr__(self):
        return self.name

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


class CWFaith(CWItem):
    ALL: dict[str, "CWFaith"] = {}

    def __init__(self):
        self.raw: CWObject = None
        self.name: str = None
        self.religion: CWReligion = None
        self.color: CWColor = None
        self.religious_head: CWTitle = None
        self.holy_site: list[CWObject] = []
        self.doctrine: list[Token] = []

    def __repr__(self):
        return self.name

    @classmethod
    def load(cls):
        raise Exception(f"<{cls.__name__}> load called")

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
        cwitem.color = CWColor.get_color(cwobject)

        cwitem.religious_head = cwobject.get("religious_head")
        if cwitem.religious_head is not None:
            cwitem.religious_head = CWTitle.ALL[cwitem.religious_head.token]

        cwitem.holy_site = cwobject.get(
            "holy_site", allow_multiple=True, default_value=[]
        )
        cwitem.holy_site = [site.values for site in cwitem.holy_site]

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

    def __repr__(self):
        return self.name

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

        if cwitem.name in cls.ALL:
            cls.error(f"Duplicate Title: {cwitem.name}")
        cls.ALL[cwitem.name] = cwitem

        cwitem.family = cwobject.get("family")
        if cwitem.family is None:
            cls.error(f"{cwitem.name} has family")

        cwitem.pagan_roots = cwobject.get("pagan_roots", default_value=Token("no"))
        cwitem.doctrine = cwobject.get(
            "doctrine", allow_multiple=True, default_value=[]
        )
        cwitem.traits = cwobject.get("traits")

        # Faiths
        faiths = cwobject.get("faiths")
        for value in faiths:
            cwitem.faiths.append(CWFaith.handle_object(value, cwitem))


def load_items():
    pass


CWColor.load_files()
CWTitle.load_files()
CWTradition.load_files()
CWCulture.load_files()
CWReligionFamily.load_files()
CWReligion.load_files()
pass
