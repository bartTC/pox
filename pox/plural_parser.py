from collections.abc import Generator
from typing import Any, NoReturn, TypedDict, cast

OP_TYPES: dict[str, str] = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "(": "LPAREN",
    ")": "RPAREN",
    "%": "MOD",
    "^": "POW",
}


class GroupDict(TypedDict):
    group: int
    values: list[int]
    has_more: bool


class Token:
    """
    Token for the plural formula language.
    """

    __slots__ = ("type", "value")

    def __init__(self, type_: str, value: Any | None = None) -> None:
        self.type = type_
        self.value = value

    def __repr__(self) -> str:
        return f"Token({self.type!r}, {self.value!r})"


class Lexer:
    """
    Lexer for the plural formula language.
    """

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None

    def error(self) -> NoReturn:
        raise ValueError(f"Invalid character: {self.current_char!r}")

    def advance(self) -> None:
        self.pos += 1
        if self.pos >= len(self.text):
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def get_integer(self) -> int:
        num_str = ""
        while self.current_char is not None and self.current_char.isdigit():
            num_str += self.current_char
            self.advance()
        return int(num_str)

    def get_variable(self) -> str:
        """
        Returns the variable name, which must be "n".
        """
        var_str = ""
        while self.current_char is not None and self.current_char.isalpha():
            var_str += self.current_char
            self.advance()
        if var_str != "n":
            self.error()
        return var_str

    def get_cmp(self) -> Token:
        cmp_str = self.current_char
        self.advance()
        if cmp_str == "=" and self.current_char == "=":
            self.advance()
            return Token("CMP_EQ")
        elif cmp_str == "!":
            if self.current_char == "=":
                self.advance()
                return Token("CMP_NEQ")
            return Token("OP_NOT")
        elif cmp_str in ("<", ">"):
            type_ = "CMP_LT" if cmp_str == "<" else "CMP_GT"
            if self.current_char == "=":
                self.advance()
                type_ += "E"
            return Token(type_)
        elif cmp_str == "?":
            return Token("TERN")
        elif cmp_str == ":":
            return Token("TERN_ELSE")
        else:
            if self.current_char != cmp_str:
                self.error()
            self.advance()
            type_ = "OP_AND" if cmp_str == "&" else "OP_OR"
            return Token(type_)

    def get_token(self) -> Token:
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

        if self.current_char is None:
            return Token("EOF")

        if self.current_char.isdigit():
            return Token("INTEGER", self.get_integer())

        if self.current_char.isalpha():
            return Token("VARIABLE", self.get_variable())

        if self.current_char in OP_TYPES:
            token = Token(OP_TYPES[self.current_char])
            self.advance()
            return token

        if self.current_char in ("<", ">", "=", "!", "?", ":", "&", "|"):
            return self.get_cmp()

        return self.error()


class Parser:
    """
    Parser for the plural formula language.
    """

    def __init__(self, _lexer: Lexer, **variables: int) -> None:
        self.lexer = _lexer
        self.variables = variables
        self.current_token = self.lexer.get_token()

    def error(self) -> NoReturn:
        raise ValueError("Invalid syntax", self.current_token)

    def eat(self, token_type: str | None = None) -> None:
        if token_type and self.current_token.type != token_type:
            self.error()
        self.current_token = self.lexer.get_token()

    def factor(self) -> bool | int:
        token = self.current_token

        if token.type == "LPAREN":
            self.eat("LPAREN")
            result = self.parse_expression()
            self.eat("RPAREN")
            return result
        elif token.type == "INTEGER":
            self.eat("INTEGER")
            return cast(int, token.value)
        elif token.type == "VARIABLE":
            self.eat("VARIABLE")
            value = cast(str, token.value)
            if value not in self.variables:
                raise ValueError(f"Variable '{value}' not defined")
            return self.variables[value]
        self.error()

    def term(self) -> bool | int:
        result = self.factor()

        while self.current_token.type in ("MUL", "DIV", "MOD", "POW"):
            token = self.current_token
            self.eat(token.type)
            rhs = self.factor()
            if not isinstance(result, int) or not isinstance(rhs, int):
                raise TypeError("Invalid operand type for {token.type}")
            if token.type == "MUL":
                result *= rhs
            elif token.type == "DIV":
                result //= rhs
            elif token.type == "MOD":
                result %= rhs
            elif token.type == "POW":
                result **= rhs

        return result

    def parse_expression(self) -> bool | int:
        result: bool | int

        token = self.current_token
        if token.type == "OP_NOT":
            self.eat("OP_NOT")
            return not self.parse_expression()

        result = self.term()

        while self.current_token.type in ("ADD", "SUB"):
            token = self.current_token

            if token.type == "ADD":
                self.eat("ADD")
                result += self.term()
            elif token.type == "SUB":
                self.eat("SUB")
                result -= self.term()

        token = self.current_token
        if token.type == "CMP_EQ":
            self.eat("CMP_EQ")
            result = result == self.term()
        elif token.type == "CMP_NEQ":
            self.eat("CMP_NEQ")
            result = result != self.term()
        elif token.type == "CMP_LTE":
            self.eat("CMP_LTE")
            result = result <= self.term()
        elif token.type == "CMP_GTE":
            self.eat("CMP_GTE")
            result = result >= self.term()
        elif token.type == "CMP_LT":
            self.eat("CMP_LT")
            result = result < self.term()
        elif token.type == "CMP_GT":
            self.eat("CMP_GT")
            result = result > self.term()

        while self.current_token.type in ("OP_AND", "OP_OR"):
            self.eat()
            token = self.current_token
            next_result = self.parse_expression()
            if token.type == "OP_AND":
                result = result and next_result
            elif token.type == "OP_OR":
                return result or next_result

        token = self.current_token
        if token.type == "TERN":
            result = self.parse_conditional(result)

        return result

    def parse_conditional(self, condition: bool | int) -> bool | int:
        self.eat("TERN")
        if_true = self.parse_expression()
        self.eat("TERN_ELSE")
        if_false = self.parse_expression()
        return if_true if condition else if_false


def parse_line(line: str) -> tuple[int, str]:
    """
    Parse a plural line from a po file.

    :param line: The line to parse.
    :return: Number of plural groups and the exxpression.

    For example, the following line::

        Plural-Forms: nplurals=3; plural=n==1 ? 0 : n==2 ? 1 : 2;

    will return::

        (3, "n==1 ? 0 : n==2 ? 1 : 2")
    """
    nplurals_str, expr = line.split(";")[:2]
    nplurals = int(nplurals_str.split("=")[1].strip())
    expr = expr.split("=", 1)[1].strip()
    return nplurals, expr


def parse(_expr: str, **variables: int) -> bool | int:
    """
    Parse a plural formula and return the result.

    :param _expr: The formula to parse.
    """
    lexer = Lexer(_expr)
    parser = Parser(lexer, **variables)
    return parser.parse_expression()


def group(
    plural_line: str,
    max: int = 999,
    per_group=5,
) -> Generator[GroupDict, None, None]:
    """
    Group numbers based on a plural line from a po file.
    """
    nplurals, expr = parse_line(plural_line)
    groups: dict[int, list[int]] = {}
    for i in range(0, nplurals):
        groups[i] = []
    for i in range(0, max + 1):
        groups[parse(expr, n=i)].append(i)
    for i, group in sorted(groups.items()):
        yield {
            "group": i,
            "values": group[:per_group],
            "has_more": len(group) > per_group,
        }
