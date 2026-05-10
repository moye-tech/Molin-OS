"""
墨麟OS v2.0 — MQL (Molin Query Language) 语法解析器

对标 Obsidian Dataview DQL，为墨麟OS提供结构化知识查询语言。

语法规范（EBNF）:
  query        := from_clause [where_clause] [sort_clause] [group_clause] [flatten_clause] [limit_clause]
  from_clause  := "FROM" source ("," source)*
  source       := "skills" | "experiences" | "notes" | "memory" | "hermes_sessions" | "all"
  where_clause := "WHERE" condition (("AND" | "OR") condition)*
  condition    := field operator value
  operator     := "=" | "!=" | ">" | "<" | ">=" | "<=" | "CONTAINS" | "IN" | "HAS_TAG" | "MATCHES" | "STARTS_WITH" | "ENDS_WITH"
  sort_clause  := "SORT" "BY" field ["ASC" | "DESC"]
  group_clause := "GROUP" "BY" field
  flatten_clause := "FLATTEN" field
  limit_clause := "LIMIT" number

示例:
  FROM skills WHERE category = 'mlops' SORT BY name ASC LIMIT 10
  FROM experiences WHERE worker_id = 'content_writer' AND quality_score > 80
  FROM notes WHERE tags HAS_TAG 'project' SORT BY date DESC
  FROM all WHERE description CONTAINS 'AI' LIMIT 20
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TokenType(Enum):
    KEYWORD = 1
    IDENTIFIER = 2
    STRING = 3
    NUMBER = 4
    OPERATOR = 5
    COMMA = 6
    EOF = 7


@dataclass
class Token:
    type: TokenType
    value: str
    position: int


# MQL 关键字
KEYWORDS = {
    "FROM", "WHERE", "AND", "OR", "SORT", "BY", "ASC", "DESC",
    "GROUP", "FLATTEN", "LIMIT", "CONTAINS", "IN", "HAS_TAG",
    "MATCHES", "STARTS_WITH", "ENDS_WITH",
}

# 合法的数据源
VALID_SOURCES = {
    "skills", "experiences", "notes", "memory",
    "hermes_sessions", "all",
}

# 比较运算符
COMPARISON_OPS = {"=", "!=", ">", "<", ">=", "<="}

# 特殊运算符
SPECIAL_OPS = {"CONTAINS", "IN", "HAS_TAG", "MATCHES", "STARTS_WITH", "ENDS_WITH"}

ALL_OPS = COMPARISON_OPS | SPECIAL_OPS


# ── AST 节点 ─────────────────────────────────

@dataclass
class Condition:
    field: str
    operator: str
    value: any  # str | int | float | list


@dataclass
class WhereClause:
    conditions: list[Condition]
    connectors: list[str]  # "AND" | "OR", len = len(conditions) - 1


@dataclass
class SortClause:
    field: str
    direction: str = "ASC"  # "ASC" | "DESC"


@dataclass
class GroupClause:
    field: str


@dataclass
class FlattenClause:
    field: str


@dataclass
class MQLQuery:
    sources: list[str]
    where: Optional[WhereClause] = None
    sort: Optional[SortClause] = None
    group: Optional[GroupClause] = None
    flatten: Optional[FlattenClause] = None
    limit: Optional[int] = None


# ── 词法分析器 ──────────────────────────────

class Lexer:
    """MQL 词法分析器"""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def peek(self) -> Optional[str]:
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def advance(self) -> Optional[str]:
        ch = self.peek()
        if ch is not None:
            self.pos += 1
        return ch

    def skip_whitespace(self):
        while self.peek() and self.peek().isspace():
            self.advance()

    def read_string(self) -> Token:
        """读取引号字符串（单引号或双引号）"""
        quote = self.advance()  # consume opening quote
        start = self.pos
        value = ""
        while self.peek() and self.peek() != quote:
            ch = self.advance()
            if ch == "\\" and self.peek():
                value += self.advance()
            else:
                value += ch
        if self.peek() == quote:
            self.advance()  # consume closing quote
        return Token(TokenType.STRING, value, start)

    def read_number(self, first_char: str) -> Token:
        """读取数字"""
        start = self.pos - 1
        value = first_char
        while self.peek() and (self.peek().isdigit() or self.peek() == "."):
            value += self.advance()
        return Token(TokenType.NUMBER, value, start)

    def read_identifier_or_keyword(self, first_char: str) -> Token:
        """读取标识符或关键字"""
        start = self.pos - 1
        value = first_char
        while self.peek() and (self.peek().isalnum() or self.peek() in "_."):
            value += self.advance()

        upper = value.upper()
        if upper in KEYWORDS:
            return Token(TokenType.KEYWORD, upper, start)

        # 检查复合运算符
        if upper in ALL_OPS:
            return Token(TokenType.OPERATOR, upper, start)

        return Token(TokenType.IDENTIFIER, value, start)

    def read_operator(self, first_char: str) -> Token:
        """读取运算符"""
        start = self.pos - 1
        # 双字符运算符
        if first_char in ("!", ">", "<") and self.peek() == "=":
            return Token(TokenType.OPERATOR, first_char + self.advance(), start)
        return Token(TokenType.OPERATOR, first_char, start)

    def tokenize(self) -> list[Token]:
        """词法分析"""
        tokens = []
        while self.peek() is not None:
            ch = self.peek()

            if ch.isspace():
                self.skip_whitespace()
                continue

            if ch == ",":
                tokens.append(Token(TokenType.COMMA, ",", self.pos))
                self.advance()
                continue

            if ch in ("'", '"'):
                tokens.append(self.read_string())
                continue

            if ch.isdigit():
                tokens.append(self.read_number(self.advance()))
                continue

            if ch.isalpha() or ch == "_":
                tokens.append(self.read_identifier_or_keyword(self.advance()))
                continue

            if ch in "=!><":
                tokens.append(self.read_operator(self.advance()))
                continue

            # 跳过未知字符
            self.advance()

        tokens.append(Token(TokenType.EOF, "", self.pos))
        return tokens


# ── 语法分析器 ──────────────────────────────

class Parser:
    """MQL 语法分析器"""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        token = self.current
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def expect(self, token_type: TokenType, value: Optional[str] = None) -> Token:
        token = self.current
        if token.type != token_type:
            raise SyntaxError(
                f"期望 {token_type.name}，但得到 {token.type.name} ('{token.value}') 位置 {token.position}"
            )
        if value is not None and token.value.upper() != value.upper():
            raise SyntaxError(
                f"期望 '{value}'，但得到 '{token.value}' 位置 {token.position}"
            )
        return self.advance()

    def match(self, token_type: TokenType, value: Optional[str] = None) -> bool:
        if self.current.type != token_type:
            return False
        if value is not None and self.current.value.upper() != value.upper():
            return False
        return True

    def parse_value(self) -> any:
        """解析值：字符串、数字、或标识符列表（用于 IN）"""
        token = self.current

        if token.type == TokenType.STRING:
            self.advance()
            return token.value

        if token.type == TokenType.NUMBER:
            self.advance()
            if "." in token.value:
                return float(token.value)
            return int(token.value)

        if token.type == TokenType.IDENTIFIER:
            # 可能是字段引用或布尔值
            val = token.value
            self.advance()
            if val.lower() == "true":
                return True
            if val.lower() == "false":
                return False
            if val.lower() == "null" or val.lower() == "none":
                return None
            return val

        raise SyntaxError(f"期望值，但得到 {token.type.name} 位置 {token.position}")

    def parse_condition(self) -> Condition:
        """解析单个条件：field operator value"""
        field_token = self.expect(TokenType.IDENTIFIER)
        field = field_token.value

        op_token = self.current
        if op_token.type not in (TokenType.OPERATOR, TokenType.KEYWORD):
            raise SyntaxError(f"期望运算符，但得到 {op_token.type.name} 位置 {op_token.position}")
        operator = op_token.value.upper()
        if operator not in ALL_OPS:
            raise SyntaxError(f"不支持的运算符: {operator}")
        self.advance()

        # 特殊处理 IN 运算符（后面跟括号列表）
        if operator == "IN":
            value = self.parse_list_value()
        else:
            value = self.parse_value()

        return Condition(field=field, operator=operator, value=value)

    def parse_list_value(self) -> list:
        """解析 IN 后面的值列表：(val1, val2, ...)"""
        self.expect(TokenType.IDENTIFIER, "(") if self.current.type == TokenType.IDENTIFIER else None

        # 简化：IN 后面可以跟逗号分隔的字符串
        values = []
        if self.current.type == TokenType.IDENTIFIER and self.current.value == "(":
            self.advance()
            while not (self.current.type == TokenType.IDENTIFIER and self.current.value == ")"):
                if self.current.type == TokenType.COMMA:
                    self.advance()
                    continue
                values.append(self.parse_value())
            self.advance()  # consume )
        else:
            # 单个值
            values.append(self.parse_value())
            while self.match(TokenType.COMMA):
                self.advance()
                values.append(self.parse_value())

        return values

    def parse_where(self) -> WhereClause:
        """解析 WHERE 子句"""
        self.expect(TokenType.KEYWORD, "WHERE")

        conditions = []
        connectors = []

        conditions.append(self.parse_condition())

        while self.current.type == TokenType.KEYWORD and self.current.value in ("AND", "OR"):
            connectors.append(self.advance().value)
            conditions.append(self.parse_condition())

        return WhereClause(conditions=conditions, connectors=connectors)

    def parse_sort(self) -> SortClause:
        """解析 SORT BY 子句"""
        self.expect(TokenType.KEYWORD, "SORT")
        self.expect(TokenType.KEYWORD, "BY")

        field_token = self.expect(TokenType.IDENTIFIER)
        direction = "ASC"

        if self.match(TokenType.KEYWORD, "ASC"):
            self.advance()
        elif self.match(TokenType.KEYWORD, "DESC"):
            direction = "DESC"
            self.advance()

        return SortClause(field=field_token.value, direction=direction)

    def parse_group(self) -> GroupClause:
        """解析 GROUP BY 子句"""
        self.expect(TokenType.KEYWORD, "GROUP")
        self.expect(TokenType.KEYWORD, "BY")
        field_token = self.expect(TokenType.IDENTIFIER)
        return GroupClause(field=field_token.value)

    def parse_flatten(self) -> FlattenClause:
        """解析 FLATTEN 子句"""
        self.expect(TokenType.KEYWORD, "FLATTEN")
        field_token = self.expect(TokenType.IDENTIFIER)
        return FlattenClause(field=field_token.value)

    def parse_limit(self) -> int:
        """解析 LIMIT 子句"""
        self.expect(TokenType.KEYWORD, "LIMIT")
        token = self.expect(TokenType.NUMBER)
        return int(token.value)

    def parse(self) -> MQLQuery:
        """解析完整查询"""
        query = MQLQuery(sources=[])

        # FROM 子句（必需）
        self.expect(TokenType.KEYWORD, "FROM")

        token = self.current
        if token.type != TokenType.IDENTIFIER:
            raise SyntaxError(f"期望数据源名称，但得到 {token.type.name} 位置 {token.position}")

        source = token.value.lower()
        if source not in VALID_SOURCES:
            raise SyntaxError(
                f"不支持的数据源: '{source}'。可用: {', '.join(sorted(VALID_SOURCES))}"
            )
        query.sources.append(source)
        self.advance()

        # 逗号分隔的多个数据源
        while self.match(TokenType.COMMA):
            self.advance()
            token = self.expect(TokenType.IDENTIFIER)
            source = token.value.lower()
            if source not in VALID_SOURCES:
                raise SyntaxError(f"不支持的数据源: '{source}'")
            query.sources.append(source)

        # 可选子句
        while self.current.type != TokenType.EOF:
            if self.match(TokenType.KEYWORD, "WHERE"):
                query.where = self.parse_where()
            elif self.match(TokenType.KEYWORD, "SORT"):
                query.sort = self.parse_sort()
            elif self.match(TokenType.KEYWORD, "GROUP"):
                query.group = self.parse_group()
            elif self.match(TokenType.KEYWORD, "FLATTEN"):
                query.flatten = self.parse_flatten()
            elif self.match(TokenType.KEYWORD, "LIMIT"):
                query.limit = self.parse_limit()
            else:
                raise SyntaxError(
                    f"意外的 token: {self.current.type.name} ('{self.current.value}') 位置 {self.current.position}"
                )

        return query


# ── 公开 API ─────────────────────────────────

def parse_query(text: str) -> MQLQuery:
    """解析 MQL 查询字符串，返回 AST。

    Raises SyntaxError 如果查询语法错误。
    """
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def parse_query_safe(text: str) -> Optional[MQLQuery]:
    """安全解析，不抛异常。"""
    try:
        return parse_query(text)
    except SyntaxError as e:
        return None
    except Exception:
        return None
