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
EXTRA_SPECIAL = {
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
}

# this = religion:
# this = religion:
# this = religion:
# this = religion:
# this = religion:


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
        self.parent: list[tuple[CWHistoryDate, CWTitle]] = []
        self.development: list[tuple[CWHistoryDate, int]] = []
        self.children: list[list[CWTitle]] = []
        self.title_history: list[CWHistoryDate] = []
        self.culture: list[tuple[CWHistoryDate, CWCulture]] = []
        self.faith: list[tuple[CWHistoryDate, CWFaith]] = []
        self.special: list[tuple[CWHistoryDate, str]] = []
        self.special_slot: list[tuple[CWHistoryDate, str]] = []
        self.province_history: list[CWHistoryDate] = []

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
            title.children.append(cwtitle.children)
            for _ in STARTING_DATES:
                title.children.append([])
            title.development.append((stubdate, 0))
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
                title.altnames[value].append(namelist)

            if title.name in CWHistoryTitle.ALL:
                title.title_history = CWHistoryTitle.ALL[title.name].dates
            if title.province in CWHistoryProvince.ALL:
                title.province_history = CWHistoryProvince.ALL[title.province].dates

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
                                (comparision_date, comparision_date.de_jure_liege)
                            )
                    else:
                        title.parent.append(title.parent[-1])

        print("Resolving children")
        # Resolve children, bigger to smaller pool
        for rank in range(len(cls.RANKS)):
            if cls.RANKS[rank] == CWTitle.EMPIRE:
                continue  # empire is children of none
            for child_title in cls.RANK[cls.RANKS[rank]]:
                for index in range(len(STARTING_DATES)):
                    parent_title = child_title.parent[index + 1][1]  # CWTitle
                    if parent_title is None:
                        continue  # de_jure_liege = 0
                    parent_title = cls.ALL[parent_title.name]  # Title
                    parent_title.children[index + 1].append(child_title)

        print("Resolving capital")
        for rank in range(len(cls.RANKS)):
            if cls.RANKS[rank] == CWTitle.EMPIRE:
                continue  # barony has no capital
            for title in cls.RANK[cls.RANKS[rank]]:
                if title.capital is not None:
                    title.capital = cls.ALL[title.capital.name]

        print("Resolving development")
        # Resolve development, top to bottom

        for rank in range(len(cls.RANKS)):
            if cls.RANKS[rank] == CWTitle.BARONY:
                continue  # barony has no development
            for title in cls.RANK[cls.RANKS[rank]]:
                for starting_date in STARTING_DATES:
                    # Development
                    comparision_date = compare_history(
                        "change_development_level",
                        title,
                        title.development[-1][0],
                        starting_date,
                        False,
                    )
                    if comparision_date.change_development_level is not None:
                        title.development.append(
                            (
                                comparision_date,
                                comparision_date.change_development_level.token,
                            )
                        )
                    else:
                        title.development.append(title.development[-1])

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

            # Check if county capital
            county = cls.ALL[title.parent[0][1].name]
            if title.name == county.capital.name:
                county.culture = title.culture
                county.faith = title.faith

            # Add extra special buildings
            for extra in EXTRA_SPECIAL:
                if len(title.special) != 1 or len(title.special_slot) != 1:
                    continue  # baronies with a special building are skipped
                if extra[0] == "religion":
                    if extra[1] == "any":
                        faiths = list(CWFaith.ALL.values())
                    else:
                        faiths = CWReligion.ALL[extra[1]].faiths
                    pass
                elif extra[0] == "family":
                    pass
                else:
                    raise Exception(f"unhandled category in extra: {extra[0]}")


Title.initialize()
Title.after_initialize()


def list_of_kingdoms():
    # https://ck3.paradoxwikis.com/List_of_kingdoms

    pass


pass
