# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from hy.models.expression import HyExpression
from hy.models.integer import HyInteger
from hy.models.lambdalist import HyLambdaListKeyword
from hy.models.float import HyFloat
from hy.models.complex import HyComplex
from hy.models.symbol import HySymbol
from hy.models.string import HyString
from hy.models.dict import HyDict

from hy.lex.states import LexException

from hy.lex import tokenize


def test_lex_exception():
    """ Ensure tokenize throws a fit on a partial input """
    try:
        tokenize("(foo")
        assert True is False
    except LexException:
        pass

    try:
        tokenize("&foo&")
        assert True is False
    except LexException:
        pass


def test_unbalanced_exception():
    """Ensure the tokenization fails on unbalanced expressions"""
    try:
        tokenize("(bar))")
        assert True is False
    except LexException:
        pass

    try:
        tokenize("(baz [quux]])")
        assert True is False
    except LexException:
        pass


def test_lex_expression_symbols():
    """ Make sure that expressions produce symbols """
    objs = tokenize("(foo bar)")
    assert objs == [HyExpression([HySymbol("foo"), HySymbol("bar")])]


def test_lex_expression_strings():
    """ Test that expressions can produce symbols """
    objs = tokenize("(foo \"bar\")")
    assert objs == [HyExpression([HySymbol("foo"), HyString("bar")])]


def test_lex_expression_integer():
    """ Make sure expressions can produce integers """
    objs = tokenize("(foo 2)")
    assert objs == [HyExpression([HySymbol("foo"), HyInteger(2)])]


def test_lex_lambda_list_keyword():
    """ Make sure expressions can produce lambda list keywords """
    objs = tokenize("(x &rest xs)")
    assert objs == [HyExpression([HySymbol("x"),
                                  HyLambdaListKeyword("&rest"),
                                  HySymbol("xs")])]


def test_lex_symbols():
    """ Make sure that symbols are valid expressions"""
    objs = tokenize("foo ")
    assert objs == [HySymbol("foo")]


def test_lex_strings():
    """ Make sure that strings are valid expressions"""
    objs = tokenize("\"foo\" ")
    assert objs == [HyString("foo")]


def test_lex_integers():
    """ Make sure that integers are valid expressions"""
    objs = tokenize("42 ")
    assert objs == [HyInteger(42)]


def test_lex_expression_float():
    """ Make sure expressions can produce floats """
    objs = tokenize("(foo 2.)")
    assert objs == [HyExpression([HySymbol("foo"), HyFloat(2.)])]
    objs = tokenize("(foo -0.5)")
    assert objs == [HyExpression([HySymbol("foo"), HyFloat(-0.5)])]
    objs = tokenize("(foo 1.e7)")
    assert objs == [HyExpression([HySymbol("foo"), HyFloat(1.e7)])]


def test_lex_expression_complex():
    """ Make sure expressions can produce complex """
    objs = tokenize("(foo 2.j)")
    assert objs == [HyExpression([HySymbol("foo"), HyComplex(2.j)])]
    objs = tokenize("(foo -0.5j)")
    assert objs == [HyExpression([HySymbol("foo"), HyComplex(-0.5j)])]
    objs = tokenize("(foo 1.e7j)")
    assert objs == [HyExpression([HySymbol("foo"), HyComplex(1.e7j)])]


def test_lex_line_counting():
    """ Make sure we can count lines / columns """
    entry = tokenize("(foo (one two))")[0]

    assert entry.start_line == 1
    assert entry.start_column == 1

    assert entry.end_line == 1
    assert entry.end_column == 15

    entry = entry[1]
    assert entry.start_line == 1
    assert entry.start_column == 6

    assert entry.end_line == 1
    assert entry.end_column == 14


def test_lex_line_counting_multi():
    """ Make sure we can do multi-line tokenization """
    entries = tokenize("""
(foo (one two))
(foo bar)
""")

    entry = entries[0]

    assert entry.start_line == 2
    assert entry.start_column == 1

    assert entry.end_line == 2
    assert entry.end_column == 15

    entry = entries[1]
    assert entry.start_line == 3
    assert entry.start_column == 1

    assert entry.end_line == 3
    assert entry.end_column == 9


def test_lex_line_counting_multi_inner():
    """ Make sure we can do multi-line tokenization (inner) """
    entry = tokenize("""(foo
    bar)""")[0]
    inner = entry[0]

    assert inner.start_line == 1
    assert inner.start_column == 2

    inner = entry[1]

    assert inner.start_line == 2
    assert inner.start_column == 5


def test_dicts():
    """ Ensure that we can tokenize a dict. """
    objs = tokenize("{foo bar bar baz}")
    assert objs == [HyDict(["foo", "bar", "bar", "baz"])]

    objs = tokenize("(bar {foo bar bar baz})")
    assert objs == [HyExpression([HySymbol("bar"),
                                  HyDict(["foo", "bar",
                                          "bar", "baz"])])]

    objs = tokenize("{(foo bar) (baz quux)}")
    assert objs == [HyDict([
        HyExpression([HySymbol("foo"), HySymbol("bar")]),
        HyExpression([HySymbol("baz"), HySymbol("quux")])
    ])]


def test_nospace():
    """ Ensure we can tokenize without spaces if we have to """
    entry = tokenize("(foo(one two))")[0]

    assert entry.start_line == 1
    assert entry.start_column == 1

    assert entry.end_line == 1
    assert entry.end_column == 14

    entry = entry[1]
    assert entry.start_line == 1
    assert entry.start_column == 5

    assert entry.end_line == 1
    assert entry.end_column == 13


def test_escapes():
    """ Ensure we can escape things """
    entry = tokenize("(foo \"foo\\n\")")[0]
    assert entry[1] == "foo\n"

    try:
        entry = tokenize("(foo \"foo\s\")")[0]
        assert True is False
    except LexException:
        pass


def test_hashbang():
    """ Ensure we can escape things """
    entry = tokenize("#!this is a comment\n")
    assert entry == []


def test_complex():
    """Ensure we tokenize complex numbers properly"""
    # This is a regression test for #143
    entry = tokenize("(1j)")[0][0]
    assert entry == HyComplex("1.0j")
    entry = tokenize("(j)")[0][0]
    assert entry == HySymbol("j")
