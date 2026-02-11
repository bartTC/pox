"""Safe parser for GNU gettext plural formulas."""

from collections.abc import Generator
from typing import NoReturn, TypedDict, cast

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
    """Result of grouping n-values by their plural form index."""

    group: int
    values: list[int]
    has_more: bool


class Token:
    """Token for the plural formula language."""

    __slots__ = ("type", "value")

    def __init__(self, type_: str, value: str | int | None = None) -> None:
        """Initialize a token with a type and optional value."""
        self.type = type_
        self.value = value

    def __repr__(self) -> str:
        """Return a debug representation of the token."""
        return f"Token({self.type!r}, {self.value!r})"


class Lexer:
    """Lexer for the plural formula language."""

    def __init__(self, text: str) -> None:
        """Initialize the lexer with the input text."""
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None

    def error(self) -> NoReturn:
        """Raise an error for an invalid character."""
        msg = f"Invalid character: {self.current_char!r}"
        raise ValueError(msg)

    def advance(self) -> None:
        """Advance the position by one character."""
        self.pos += 1
        if self.pos >= len(self.text):
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def get_integer(self) -> int:
        """Read and return a multi-digit integer."""
        num_str = ""
        while self.current_char is not None and self.current_char.isdigit():
            num_str += self.current_char
            self.advance()
        return int(num_str)

    def get_variable(self) -> str:
        """Return the variable name, which must be ``n``."""
        var_str = ""
        while self.current_char is not None and self.current_char.isalpha():
            var_str += self.current_char
            self.advance()
        if var_str != "n":
            self.error()
        return var_str

    def get_cmp(self) -> Token:  # noqa: PLR0911
        """Read a comparison, logical, or ternary operator."""
        cmp_str = self.current_char
        self.advance()
        if cmp_str == "=" and self.current_char == "=":
            self.advance()
            return Token("CMP_EQ")
        if cmp_str == "!":
            if self.current_char == "=":
                self.advance()
                return Token("CMP_NEQ")
            return Token("OP_NOT")
        if cmp_str in ("<", ">"):
            type_ = "CMP_LT" if cmp_str == "<" else "CMP_GT"
            if self.current_char == "=":
                self.advance()
                type_ += "E"
            return Token(type_)
        if cmp_str == "?":
            return Token("TERN")
        if cmp_str == ":":
            return Token("TERN_ELSE")
        if self.current_char != cmp_str:
            self.error()
        self.advance()
        type_ = "OP_AND" if cmp_str == "&" else "OP_OR"
        return Token(type_)

    def get_token(self) -> Token:
        """Return the next token from the input."""
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
    """Parser for the plural formula language."""

    def __init__(self, _lexer: Lexer, **variables: int) -> None:
        """Initialize the parser with a lexer and variable bindings."""
        self.lexer = _lexer
        self.variables = variables
        self.current_token = self.lexer.get_token()

    def error(self) -> NoReturn:
        """Raise an error for invalid syntax."""
        msg = "Invalid syntax"
        raise ValueError(msg, self.current_token)

    def eat(self, token_type: str | None = None) -> None:
        """Consume the current token, optionally asserting its type."""
        if token_type and self.current_token.type != token_type:
            self.error()
        self.current_token = self.lexer.get_token()

    def factor(self) -> bool | int:
        """Parse a factor: integer, variable, or parenthesized expression."""
        token = self.current_token

        if token.type == "LPAREN":
            self.eat("LPAREN")
            result = self.parse()
            self.eat("RPAREN")
            return result
        if token.type == "INTEGER":
            self.eat("INTEGER")
            return cast("int", token.value)
        if token.type == "VARIABLE":
            self.eat("VARIABLE")
            value = cast("str", token.value)
            if value not in self.variables:
                msg = f"Variable '{value}' not defined"
                raise ValueError(msg)
            return self.variables[value]
        self.error()

    def term(self) -> bool | int:
        """Parse multiplication, division, modulo, and power operations."""
        result = self.factor()

        while self.current_token.type in ("MUL", "DIV", "MOD", "POW"):
            token = self.current_token
            self.eat(token.type)
            rhs = self.factor()
            if token.type == "MUL":
                result *= rhs
            elif token.type == "DIV":
                result //= rhs
            elif token.type == "MOD":
                result %= rhs
            elif token.type == "POW":
                result **= rhs

        return result

    def parse_expression(self) -> bool | int:  # noqa: C901, PLR0912
        """Parse a full expression with comparisons and logical operators."""
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
            token = self.current_token
            self.eat()
            next_result = self.parse_expression()
            if token.type == "OP_AND":
                result = result and next_result
            elif token.type == "OP_OR":
                return result or next_result

        return result

    def parse(self) -> bool | int:
        """Parse a ternary expression or delegate to parse_expression."""
        result = self.parse_expression()

        if self.current_token.type == "TERN":
            self.eat("TERN")
            if_true = self.parse()
            self.eat("TERN_ELSE")
            if_false = self.parse()
            return if_true if result else if_false

        return result


def parse_line(line: str) -> tuple[int, str]:
    """
    Parse a plural line from a po file.

    :param line: The line to parse.
    :return: Number of plural groups and the expression.

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
    return parser.parse()


def group(
    plural_line: str,
    max_n: int = 999,
    per_group: int = 5,
) -> Generator[GroupDict, None, None]:
    """Group numbers based on a plural line from a po file."""
    nplurals, expr = parse_line(plural_line)
    groups: dict[int, list[int]] = {}
    for i in range(nplurals):
        groups[i] = []
    for i in range(max_n + 1):
        groups[parse(expr, n=i)].append(i)
    for i, grp in sorted(groups.items()):
        yield {
            "group": i,
            "values": grp[:per_group],
            "has_more": len(grp) > per_group,
        }
