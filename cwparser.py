import pathlib
import re
from typing import Generator

CHAR_BOUNDARY = (" ", "\t", "\n", "\r")
CHAR_OBJ = {"{": "OBJ_START", "}": "OBJ_END"}
CHAR_OPERATOR = {
    "=": "OP_EQUAL",
    "==": "OP_EQUALEQUAL",
    "!": "OP_INVALID",  # For !=
    "!=": "OP_DIFFERENT",
    "?": "OP_INVALID",  # For ?=
    "?=": "OP_NULLEQUAL",
    ">": "OP_BIGGERTHAN",
    ">=": "OP_BIGGEREQUAL",
    "<": "OP_SMALLERTHAN",
    "<=": "OP_SMALLEREQUAL",
}


class Token:
    IDENTIFIER = "IDENTIFIER"
    LOCAL = "LOCAL"
    EXPRESSION = "EXPRESSION"
    STRING = "STRING"
    NUMBER = "NUMBER"
    DATE = "DATE"
    BOOL = "BOOL"
    OBJOPEN = "OPEN"
    OBJCLOSE = "CLOSE"

    def __init__(self, token: str, filename: pathlib.Path = None, line: int = 0):
        self.token = token
        self.type = None
        self.filename = filename
        self.line = line
        if not self.token.strip():
            self.error("Empty Token")

        if token.lower() in ("yes", "no"):
            self.type = Token.BOOL
        elif token in CHAR_OPERATOR:
            self.type = CHAR_OPERATOR[token]
            if self.type == "OP_INVALID":
                self.error("Invalid Token")
        elif token == "{":
            self.type = Token.OBJOPEN
        elif token == "}":
            self.type = Token.OBJCLOSE
        elif re.match(r'".+"$', token):
            self.token = self.token[1:-1]
            self.type = Token.STRING
        elif re.match(r"@\[.+\]$", token):
            self.type = Token.EXPRESSION
        elif re.match(r"@.+$", token):
            self.type = Token.LOCAL
        elif re.match(r"\d+\.\d+\.$", token) or re.match(r"\d+\.\d+\.\d+\.?$", token):
            # Can be both date or decimal depending on context
            self.transform_into_date()
        elif re.match(r"-?\d+\.\d{0,}$", token):
            if not self.token.split(".")[1]:
                self.token += "0"
            self.token = float(self.token)
            self.type = Token.NUMBER
        elif re.match(r"-?\d+$", token):
            self.token = int(self.token)
            self.type = Token.NUMBER
        else:
            self.type = Token.IDENTIFIER

    def __repr__(self):
        return f"{self.type}:{self.token}"

    def error(self, message: str):
        raise Exception(f"{message} | {self.filename}:{self.line} - {self.token}")

    def transform_into_date(self):
        self.type = Token.DATE
        # Try to transform value into date
        # A     - A.1.1 | A.     - A.1.1 (possible number)
        # A.B   - A.B.1 | A.B.   - A.1.1 (possible float)
        # A.B.C - A.B.C | A.B.C. - A.B.C (guaranteed date)
        # Normalize date
        values = str(self.token).split(".")
        # Missing date values default to one
        values += [1] * (3 - len(values))
        values[0] = int(values[0]) if values[0] else 1
        values[1] = int(values[1]) if values[1] else 1
        values[2] = int(values[2]) if values[2] else 1
        self.token = ".".join([str(value) for value in values[:3]])


def read_file(filename: pathlib.Path) -> str:
    # CK3 files are split between UTF-8 with BOM (UTF-8-SIG)
    # and Windows CP-1252 (Windows-1252) for some godforsaken reason
    # Try one, if it fails use the other
    try:
        with filename.open("r", encoding="utf-8-sig") as f:
            return f.read()
    except UnicodeDecodeError:
        with filename.open("r", encoding="windows-1252") as f:
            return f.read()


# Clausewitz Tokenizer
def tokenize(text: str, filename: pathlib.Path) -> Generator[Token, any, any]:
    current_line = 1
    start = index = 0

    while True:
        character = text[index] if index < len(text) else " "
        if character in CHAR_BOUNDARY:
            word = "".join(text[start:index]).strip()
            if word:
                yield Token(word, filename, current_line)
            index += 1
            start = index
            if character == "\n":
                current_line += 1
            if index > len(text):
                break
        elif character in CHAR_OBJ:
            word = "".join(text[start:index]).strip()
            if word:
                yield Token(word, filename, current_line)
            yield Token(character, filename, current_line)
            index += 1
            start = index
        elif character == "#":
            word = "".join(text[start:index]).strip()
            start = index
            if word:
                yield Token(word, filename, current_line)
            while (index < len(text)) and (text[index] != "\n"):
                index += 1
                start = index  # ignore until newline
            current_line += 1
            continue
        elif character == '"':
            word = "".join(text[start:index]).strip()
            start = index
            if word:
                yield Token(word, filename, current_line)
            index += 1
            while text[index] != '"':  # triggers exception on purpose
                index += 1
            index += 1
            word = "".join(text[start:index])
            start = index
            yield Token(word, filename, current_line)
        elif character in CHAR_OPERATOR:
            word = "".join(text[start:index]).strip()
            start = index
            if word:
                yield Token(word, filename, current_line)
            while index < len(text):
                word = "".join(text[start : index + 1])
                if word not in CHAR_OPERATOR:  # multi-len operator
                    word = "".join(text[start:index])
                    start = index
                    yield Token(word, filename, current_line)
                    break
                index += 1
        elif character == "@":
            word = "".join(text[start:index]).strip()
            start = index
            if word:
                yield Token(word, filename, current_line)
            if index == len(text) or text[index + 1] != "[":
                index += 1
                continue
            while text[index] != "]":  # triggers exception on purpose
                index += 1
            index += 1
            word = "".join(text[start:index])
            start = index
            yield Token(word, filename, current_line)
        else:
            index += 1


class CWObject:
    ALL = []
    INDEX = 0

    def __init__(self, token: Token = None, operator: Token = None):
        self.token = token
        self.index = CWObject.INDEX
        self.name = token.token if token else f"OBJ{self.index}"
        self.operator = operator
        self.values: Token | list[Token | CWObject] = []
        CWObject.INDEX += 1
        CWObject.ALL.append(self)

    def find(self, name: str) -> list[int]:
        if type(self.values) is Token:
            raise Exception(f"{repr(self)} is single value but find was called")
        ret = []
        for index, cwobject in enumerate(self.values):
            if cwobject.token is None:
                continue
            if cwobject.token.token == name:
                ret.append(index)
        return ret

    def get(
        self, name: str, allow_multiple=False, default_value=None, return_value=True
    ) -> "CWObject":
        indexes = self.find(name)
        if len(indexes) == 0:
            return default_value
        if len(indexes) > 1 and not allow_multiple:
            raise Exception(
                f"Duplicate '{name}' Values: {'\n'.join([repr(self.values[index]) for index in indexes])}"
            )
        if allow_multiple:
            # sometimes values are duplicated, even though they should not be!!!
            # ex: b_yalachi duplicated province = 5505
            return [self.values[index] for index in indexes]
        else:
            if return_value:
                return self.values[indexes[0]].values
            else:
                return self.values[indexes[0]]

    def __repr__(self):
        name = self.name if not self.token else self.token.token
        if self.operator is not None:
            if type(self.values) is Token:
                return f"{name}{self.operator.token}{self.values.token}"
            else:
                return f"{name}{self.operator.token}{{OBJ}}"
        else:
            return name

    def __len__(self):
        return len(self.values)

    def __getitem__(self, i):
        return self.values[i]

    def describe(self, indent: int = 0) -> str:
        retstr = ""
        if self.token:
            retstr += f"{self.token.token}"
            if self.operator:
                retstr += f" {self.operator.token} "
            else:
                retstr += " = "
        if type(self.values) is Token:
            retstr += f"{self.values.token}"
        else:
            retstr += "{ "
            for value in self.values:
                if type(value) is Token:
                    retstr += f"{str(value.token)} "
                else:
                    retstr += f"{value.describe(indent + 4)} "
            retstr += "}"
        return retstr

    def append(self, token: Token):
        self.values.append(token)


class UnexpectedToken(Exception):
    def __init__(self, token: Token):
        super().__init__(
            f"UNEXPECTED TOKEN> {token.type}:{token.token} ({token.filename}:{token.line})"
        )


class QueueNotEmpty(Exception):
    def __init__(self, queue: list[Token]):
        super().__init__(
            f"QUEUE NOT EMPTY> {queue} ({queue[0].filename}:{queue[0].line})"
        )


class CWLoc:
    ALL = []
    INDEX = 0

    def __init__(self, token: Token = None, operator: Token = None):
        self.token = token
        self.index = CWObject.INDEX
        self.name = token.token if token else f"OBJ{self.index}"
        self.operator = operator
        self.values: Token | list[Token | CWObject] = []
        CWObject.INDEX += 1
        CWObject.ALL.append(self)

    def find(self, name: str) -> list[int]:
        if type(self.values) is Token:
            raise Exception(f"{repr(self)} is single value but find was called")
        ret = []
        for index, cwobject in enumerate(self.values):
            if cwobject.token is None:
                continue
            if cwobject.token.token == name:
                ret.append(index)
        return ret

    def get(
        self, name: str, allow_multiple=False, default_value=None, return_value=True
    ) -> "CWObject":
        indexes = self.find(name)
        if len(indexes) == 0:
            return default_value
        if len(indexes) > 1 and not allow_multiple:
            raise Exception(
                f"Duplicate '{name}' Values: {'\n'.join([repr(self.values[index]) for index in indexes])}"
            )
        if allow_multiple:
            # sometimes values are duplicated, even though they should not be!!!
            # ex: b_yalachi duplicated province = 5505
            return [self.values[index] for index in indexes]
        else:
            if return_value:
                return self.values[indexes[0]].values
            else:
                return self.values[indexes[0]]

    def __repr__(self):
        name = self.name if not self.token else self.token.token
        if self.operator is not None:
            if type(self.values) is Token:
                return f"{name}{self.operator.token}{self.values.token}"
            else:
                return f"{name}{self.operator.token}{{OBJ}}"
        else:
            return name

    def __len__(self):
        return len(self.values)

    def __getitem__(self, i):
        return self.values[i]

    def describe(self, indent: int = 0) -> str:
        retstr = ""
        if self.token:
            retstr += f"{self.token.token}"
            if self.operator:
                retstr += f" {self.operator.token} "
            else:
                retstr += " = "
        if type(self.values) is Token:
            retstr += f"{self.values.token}"
        else:
            retstr += "{ "
            for value in self.values:
                if type(value) is Token:
                    retstr += f"{str(value.token)} "
                else:
                    retstr += f"{value.describe(indent + 4)} "
            retstr += "}"
        return retstr

    def append(self, token: Token):
        self.values.append(token)


# Clausewitz Parser
def parse_group(
    tokens: Generator[Token, any, any], parent: CWObject = None
) -> list[CWObject]:
    objects: list[CWObject] = []
    queue: list[Token] = []

    while True:
        try:
            token = next(tokens)
            if len(queue) == 0:
                if token.type in CHAR_OPERATOR.values():
                    raise UnexpectedToken(token)
        except StopIteration:
            if queue and queue[-1].type != Token.OBJCLOSE:
                raise QueueNotEmpty(queue)
            return objects

        if token.type in CHAR_OPERATOR.values():
            if len(queue) == 0:
                raise UnexpectedToken(token)
            if len(queue) > 1:
                cwobject = CWObject()
                for item in queue[:-1]:
                    cwobject.append(item)
                objects.append(cwobject)
                queue = queue[-1:]
            queue.append(token)
        elif token.type == Token.OBJOPEN:
            if len(queue) > 0:
                if queue[-1].type in CHAR_OPERATOR.values():
                    # a = {}
                    if queue[-1].type not in (CHAR_OPERATOR["="], CHAR_OPERATOR["?="]):
                        raise UnexpectedToken(token)
                    cwobject = CWObject(queue[-2], queue[-1])
                    cwobject.values = parse_group(tokens, cwobject)
                    objects.append(cwobject)
                    queue = queue[:-2]
                else:
                    # a {}
                    cwobject = CWObject(queue[-1], Token("="))
                    cwobject.values = parse_group(tokens, cwobject)
                    objects.append(cwobject)
                    queue = queue[:-1]
            else:
                if len(queue) > 1:
                    cwobject = CWObject()
                    for item in queue[:-1]:
                        cwobject.append(item)
                    queue = queue[-1:]
                    cwobject = CWObject(queue[-1])
                else:
                    cwobject = CWObject()
                cwobject.values = parse_group(tokens, cwobject)
                objects.append(cwobject)
                queue = queue[:-1]
        elif token.type == Token.OBJCLOSE:
            if parent is None:
                raise UnexpectedToken(token)
            if len(queue):
                cwobject = CWObject()
                for item in queue:
                    cwobject.append(item)
                objects.append(cwobject)
            return objects
        elif token.type == Token.EXPRESSION:
            if len(queue) == 0:
                raise UnexpectedToken(token)
            if queue[-1].type in CHAR_OPERATOR.values():
                cwobject = CWObject(queue[-2])
                cwobject.operator = queue[-1]
                cwobject.values = token
                objects.append(cwobject)
                queue = queue[:-2]
            else:  # list
                queue.append(token)
        elif token.type in (
            Token.IDENTIFIER,
            Token.LOCAL,
            Token.STRING,
            Token.NUMBER,
            Token.DATE,
            Token.BOOL,
        ):
            if len(queue) == 0:
                queue.append(token)
                continue
            if queue[-1].type in CHAR_OPERATOR.values():
                cwobject = CWObject(queue[-2])
                cwobject.operator = queue[-1]
                cwobject.values = token
                objects.append(cwobject)
                queue = queue[:-2]
            else:  # list
                queue.append(token)
        else:
            raise UnexpectedToken(token)


class CWLocalization:
    def __init__(self, name: Token, value: Token):
        if name.type != Token.IDENTIFIER:
            raise UnexpectedToken(name)
        if ":" not in name.token:
            raise UnexpectedToken(name)
        # the optional number after can be ignored
        self.name = name.token[: name.token.index(":")]

        if value.type != Token.STRING:
            if value.token != '""':
                raise UnexpectedToken(value)
        self.value = value.token

    def __repr__(self):
        return f"{self.name}:{self.value}"


# Regular YML parsers don't work on CK3 files
def parse_file_yml(tokens: Generator[Token, any, any]):
    objects: list[CWLocalization] = []
    queue: list[Token] = []

    while True:
        try:
            token = next(tokens)
        except StopIteration:
            if len(queue) > 0:
                raise QueueNotEmpty(queue)
            return objects

        if token.token == "l_english:":
            continue
        elif token.type == Token.IDENTIFIER:
            if len(queue) > 0:
                # blame d_placeholder:0 ""
                if token.token != '""':
                    raise UnexpectedToken(token)
                if len(queue) != 1:
                    raise UnexpectedToken(token)
                objects.append(CWLocalization(queue[0], token))
                queue = []
                continue
            queue.append(token)
        elif token.type == Token.STRING:
            if len(queue) != 1:
                raise UnexpectedToken(token)
            objects.append(CWLocalization(queue[0], token))
            queue = []
        else:
            raise UnexpectedToken(token)


# for row in f.readlines():
## BUILDING_TOOLTIP_TEXT:1 "[Building.GetDescription]\n\n#S Effect:\n#![Building.GetEffectDescription( GetPlayer )]"
# row = row.strip()
# if not row:
# continue  # no empty rows
# name, value = row.split(":", 1)
# number, value = value.split(" ", 1)
# if number:
# number = int(number)  # sanity check
# if value == '""':
# continue  # fuck you d_placeholder
# value = re.match('"(.+)"', value)[1]
# if "$" in value:
# continue  # no references
# if "_desc" in name:
# continue  # no descriptions
# if "building_" not in name:
# continue
# if "building_type_" in name:
# name = name[len("building_type_") :]
# else:
# name = name[len("building_") :]
# buildings[name] = value
# k
