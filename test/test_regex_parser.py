from __future__ import annotations

import string
from typing import Any

import pytest

from pysm import Event, State, StateMachine
from pysm.builder import StateMachineBuilder


class RegexSyntaxError(Exception):
    pass


class States:
    Pattern = "Pattern"
    Escape = "Escape"
    CharacterClass = "CharacterClass"
    CharacterClassEscape = "CharacterClassEscape"


class RegexParser(object):
    METACHARS = set("\\.[]*+?")
    ALL_CHARS = set(string.printable)
    LITERAL_CHARS = tuple(sorted(ALL_CHARS - METACHARS))
    ESCAPED_CHARS = tuple(sorted(ALL_CHARS))
    CLASS_CHARS = tuple(sorted(ALL_CHARS - set("\\]")))

    def __init__(self):
        self.tokens: list[tuple[str, Any, str]] = []
        self._class_buffer: list[str] = []
        self.sm = self._get_state_machine()

    def _get_state_machine(self) -> StateMachine:
        sm = (
            StateMachineBuilder("regex")
            .state(States.Pattern, initial=True)
            .state(States.Escape)
            .state(States.CharacterClass)
            .state(States.CharacterClassEscape)
            .transition(
                States.Pattern,
                None,
                events=["parse"],
                input=self.LITERAL_CHARS,
                action=self.add_literal,
            )
            .transition(States.Pattern, States.Escape, events=["parse"], input=["\\"])
            .transition(
                States.Pattern, None, events=["parse"], input=["."], action=self.add_any
            )
            .transition(
                States.Pattern,
                States.CharacterClass,
                events=["parse"],
                input=["["],
                action=self.start_character_class,
            )
            .transition(
                States.Pattern,
                None,
                events=["parse"],
                input=["*", "+", "?"],
                action=self.apply_quantifier,
            )
            .transition(
                States.Escape,
                States.Pattern,
                events=["parse"],
                input=self.ESCAPED_CHARS,
                action=self.add_literal,
            )
            .transition(
                States.CharacterClass,
                None,
                events=["parse"],
                input=self.CLASS_CHARS,
                action=self.add_character_class_char,
            )
            .transition(
                States.CharacterClass,
                States.CharacterClassEscape,
                events=["parse"],
                input=["\\"],
            )
            .transition(
                States.CharacterClass,
                States.Pattern,
                events=["parse"],
                input=["]"],
                action=self.end_character_class,
            )
            .transition(
                States.CharacterClassEscape,
                States.CharacterClass,
                events=["parse"],
                input=self.ESCAPED_CHARS,
                action=self.add_character_class_char,
            )
            .build()
        )
        self.pattern = self._state(sm, States.Pattern)
        self.escape = self._state(sm, States.Escape)
        self.character_class = self._state(sm, States.CharacterClass)
        self.character_class_escape = self._state(sm, States.CharacterClassEscape)
        return sm

    def _state(self, sm: StateMachine, name: str) -> State:
        for state in sm.states:
            if state.name == name:
                return state
        raise AssertionError("Missing parser state: {0}".format(name))

    def parse(self, pattern: str) -> list[tuple[str, Any, str]]:
        for char in pattern:
            if char not in self.ALL_CHARS:
                raise RegexSyntaxError("Unsupported character: {0}".format(repr(char)))
            self.sm.dispatch(Event("parse", input=char))

        if self.sm.state is self.escape:
            raise RegexSyntaxError("Dangling escape")
        if self.sm.state in (self.character_class, self.character_class_escape):
            raise RegexSyntaxError("Unclosed character class")
        return self.tokens

    def _char(self, event: Event) -> str:
        value = event.input
        assert isinstance(value, str)
        return value

    def add_literal(self, state: State, event: Event):
        del state
        self.tokens.append(("literal", self._char(event), ""))

    def add_any(self, state: State, event: Event):
        del state
        del event
        self.tokens.append(("any", None, ""))

    def start_character_class(self, state: State, event: Event):
        del state
        del event
        self._class_buffer = []

    def add_character_class_char(self, state: State, event: Event):
        del state
        self._class_buffer.append(self._char(event))

    def end_character_class(self, state: State, event: Event):
        del state
        del event
        if not self._class_buffer:
            raise RegexSyntaxError("Empty character class")
        self.tokens.append(("class", frozenset(self._class_buffer), ""))
        self._class_buffer = []

    def apply_quantifier(self, state: State, event: Event):
        del state
        if not self.tokens:
            raise RegexSyntaxError("Quantifier has no target")
        kind, value, repeat = self.tokens[-1]
        if repeat:
            raise RegexSyntaxError("Repeated quantifier")
        self.tokens[-1] = (kind, value, self._char(event))


class SimpleRegex(object):
    def __init__(self, pattern: str):
        self.tokens = RegexParser().parse(pattern)

    def matches(self, text: str) -> bool:
        return self._match_from(0, 0, text, {})

    def _match_from(
        self,
        token_index: int,
        text_index: int,
        text: str,
        memo: dict[tuple[int, int], bool],
    ) -> bool:
        key = (token_index, text_index)
        if key in memo:
            return memo[key]

        if token_index == len(self.tokens):
            return text_index == len(text)

        token = self.tokens[token_index]
        repeat = token[2]

        if repeat == "":
            result = (
                text_index < len(text)
                and self._atom_matches(token, text[text_index])
                and self._match_from(token_index + 1, text_index + 1, text, memo)
            )
        elif repeat == "?":
            result = self._match_optional(token, token_index, text_index, text, memo)
        elif repeat == "*":
            result = self._match_repeated(
                token, token_index, text_index, text, memo, minimum=0
            )
        else:
            result = self._match_repeated(
                token, token_index, text_index, text, memo, minimum=1
            )

        memo[key] = result
        return result

    def _match_optional(
        self,
        token: tuple[str, Any, str],
        token_index: int,
        text_index: int,
        text: str,
        memo: dict[tuple[int, int], bool],
    ) -> bool:
        if (
            text_index < len(text)
            and self._atom_matches(token, text[text_index])
            and self._match_from(token_index + 1, text_index + 1, text, memo)
        ):
            return True
        return self._match_from(token_index + 1, text_index, text, memo)

    def _match_repeated(
        self,
        token: tuple[str, Any, str],
        token_index: int,
        text_index: int,
        text: str,
        memo: dict[tuple[int, int], bool],
        minimum: int,
    ) -> bool:
        positions: list[int] = []
        position = text_index
        while position < len(text) and self._atom_matches(token, text[position]):
            position += 1
            positions.append(position)

        if len(positions) < minimum:
            return False
        if minimum == 0:
            positions.append(text_index)

        for position in reversed(positions):
            if self._match_from(token_index + 1, position, text, memo):
                return True
        return False

    def _atom_matches(self, token: tuple[str, Any, str], char: str) -> bool:
        kind, value, repeat = token
        del repeat
        if kind == "literal":
            return char == value
        if kind == "any":
            return True
        return char in value


def assert_matches(pattern: str, matching: list[str], rejected: list[str]) -> None:
    regex = SimpleRegex(pattern)
    for text in matching:
        assert regex.matches(text), "{0!r} should match {1!r}".format(pattern, text)
    for text in rejected:
        assert not regex.matches(text), "{0!r} should reject {1!r}".format(
            pattern, text
        )


def test_regex_parser_builds_tokens_with_escapes_and_quantifiers():
    parser = RegexParser()

    assert parser.parse(r"a\.\[b*\][xyz]?") == [
        ("literal", "a", ""),
        ("literal", ".", ""),
        ("literal", "[", ""),
        ("literal", "b", "*"),
        ("literal", "]", ""),
        ("class", frozenset("xyz"), "?"),
    ]


def test_regex_parser_matches_zero_or_more_literals():
    assert_matches(
        "ab*c",
        matching=["ac", "abc", "abbbc"],
        rejected=["abbx", "abbbcc", "a"],
    )


def test_regex_parser_matches_wildcards_classes_and_optional_suffixes():
    assert_matches(
        "h.llo[!?]?",
        matching=["hello", "hallo!", "hxllo?"],
        rejected=["hillo!!", "hllo", "heeeo"],
    )


def test_regex_parser_matches_escaped_metacharacters_and_plus():
    assert_matches(
        r"file\.[ch]+",
        matching=["file.c", "file.h", "file.chch"],
        rejected=["file", "filexc", "file."],
    )


@pytest.mark.parametrize("pattern", ["*abc", "a**", "abc\\", "[abc", "[]"])
def test_regex_parser_rejects_invalid_patterns(pattern: str) -> None:
    with pytest.raises(RegexSyntaxError):
        RegexParser().parse(pattern)
