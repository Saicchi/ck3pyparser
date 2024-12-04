from cwparser import *

TESTS = {
    r"A": "IDENTIFIER:A",
    r'A "BC" D': 'IDENTIFIER:A STRING:BC IDENTIFIER:D',
    "A #B\nC": "IDENTIFIER:A IDENTIFIER:C",
    r'A = "ABCD"': "IDENTIFIER:A OP_EQUAL:= STRING:ABCD",
    r"{1}": "OPEN:{ NUMBER:1 CLOSE:}",
    r"{123 123}": "OPEN:{ NUMBER:123 NUMBER:123 CLOSE:}",
    r"color = hsv{123 456 789}": "IDENTIFIER:color OP_EQUAL:= IDENTIFIER:hsv OPEN:{ NUMBER:123 NUMBER:456 NUMBER:789 CLOSE:}",
    r"10": "NUMBER:10",
    r"001": "NUMBER:1",
    r"-001": "NUMBER:-1",
    r"-89": "NUMBER:-89",
    r"123.456": "NUMBER:123.456",
    r"-123.456": "NUMBER:-123.456",
    r"1066.": "NUMBER:1066.0",  # Possible Date
    r"1087.05": "NUMBER:1087.05",  # Possible Date
    r"1087.06.": "DATE:1087.6.1",
    r"1197.4.12": "DATE:1197.4.12",
    r"1197.09.27.": "DATE:1197.9.27",
    r"A = B": "IDENTIFIER:A OP_EQUAL:= IDENTIFIER:B",
    r"effect = yes ": "IDENTIFIER:effect OP_EQUAL:= BOOL:yes",
    r"cost >= 65 ": "IDENTIFIER:cost OP_BIGGEREQUAL:>= NUMBER:65",
    r"@variable = @[val1*3.01] ": "LOCAL:@variable OP_EQUAL:= EXPRESSION:@[val1*3.01]",
}

for text, expected in TESTS.items():
    tokens = list(tokenize(text, "TEST"))
    expected_tokens = expected.split(" ")
    if len(tokens) != len(expected_tokens):
        print(f"Tokens size difference: {len(tokens)} - {len(expected_tokens)}")
        print(text, expected)
        print(tokens, expected_tokens)
        print("----------------------------")
        continue
    has_difference = False
    for token, expected_token in zip(tokens, expected_tokens):
        if repr(token) != expected_token:
            print(f"Token Difference: {repr(token)} - {expected_token}")
            print(text, expected)
            print(tokens, expected_tokens)
            has_difference = True
    if has_difference:
        print("----------------------------")

TESTS = {
    "A": QueueNotEmpty,
    "A=": QueueNotEmpty,
    "A=B": "A = B",
    "color = hsv {268 123 789}": "color = hsv\n{ { 268 123 789 } }",
    "color {267 165 123}": "color = { { 267 165 123 } }"
}

for text, expected in TESTS.items():
    if type(expected) is type and issubclass(expected, Exception):
        try:
            parse_group(tokenize(text, "TEST"))
            print(f"Expception Failed: {expected} {text}")
        except expected:
            pass
        continue
    cwobject = parse_group(tokenize(text, "TEST"))
    described = "\n".join([cwobj.describe() for cwobj in cwobject])
    if described != expected:
        print("DIFFERENCE")
        print(described)
        print("+++")
        print(expected)
        print("----------------------------")

    pass
