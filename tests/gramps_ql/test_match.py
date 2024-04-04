from gramps_ql import match
from gramps_ql.gql import GQLQuery


def test_match_single_string():
    q = GQLQuery("test")
    assert q._match_single({"one": "rhs"}, "one", "=", "rhs")
    assert not q._match_single({"one": "x"}, "one", "=", "rhs")
    assert q._match_single({"one": {"two": "rhs"}}, "one.two", "=", "rhs")
    assert not q._match_single({"one": {"x": "rhs"}}, "one.two", "=", "rhs")
    assert q._match_single({"one": {"two": ["rhs"]}}, "one.two[0]", "=", "rhs")
    assert not q._match_single({"one": {"two": ["rhs"]}}, "one.two[1]", "=", "rhs")
    assert q._match_single(
        {"one": {"two": [{"three": "rhs"}]}}, "one.two[0].three", "=", "rhs"
    )


def test_match_single_number():
    q = GQLQuery("test")
    assert q._match_single({"one": -1}, "one", "<", 0)
    assert not q._match_single({"one": "x"}, "one", "<", 0)
    assert q._match_single({"one": {"two": -1}}, "one.two", "<", 0)
    assert not q._match_single({"one": {"x": -1}}, "one.two", "<", 0)
    assert q._match_single({"one": {"two": [-1]}}, "one.two[0]", "<", 0)
    assert not q._match_single({"one": {"two": [-1]}}, "one.two[1]", "<", 0)
    assert q._match_single(
        {"one": {"two": [{"three": -1}]}}, "one.two[0].three", "<", 0
    )


def test_match():
    query = "one.two = x"
    q = GQLQuery(query)
    obj = {"one": {"two": "x"}, "three": {"four": ["y"]}}
    assert q.match(obj)
    assert match(query, obj)


def test_match_noop():
    q = GQLQuery("one.two")
    assert q.match({"one": {"two": 1}, "three": {"four": ["y"]}})


def test_match_and():
    q = GQLQuery("one.two = x and three.four[0] = y")
    assert q.match({"one": {"two": "x"}, "three": {"four": ["y"]}})


def test_match_and_or():
    q = GQLQuery("one.two = x and three.four[0] = y or five")
    assert q.match({"one": {"two": "x"}, "three": {"four": ["y"]}, "five": 1})


def test_length():
    q = GQLQuery("array.length = 1")
    assert not q.match({"array": []})
    assert not q.match({"array": [1, 1]})
    assert q.match({"array": [1]})
