from gramps_ql import parse


def test_single():
    assert parse("class=person").as_list() == ["class", "=", "person"]


def test_two():
    assert parse("class=person or date.year > 2021").as_list() == [
        [
            "class",
            "=",
            "person",
            "or",
            "date.year",
            ">",
            "2021",
        ]
    ]


def test_three():
    assert parse("class=person or name='John Doe' and date.year > 2021").as_list() == [
        [
            "class",
            "=",
            "person",
            "or",
            ["name", "=", "'John Doe'", "and", "date.year", ">", "2021"],
        ]
    ]
    assert parse("class=person and name='John Doe' or date.year > 2021").as_list() == [
        [
            ["class", "=", "person", "and", "name", "=", "'John Doe'"],
            "or",
            "date.year",
            ">",
            "2021",
        ]
    ]
    assert parse("class=person and name='John Doe' or only_id").as_list() == [
        [
            ["class", "=", "person", "and", "name", "=", "'John Doe'"],
            "or",
            "only_id",
        ]
    ]


def test_brackets():
    assert parse(
        "(class=person or name='John Doe') and date.year > 2021"
    ).as_list() == [
        [
            ["class", "=", "person", "or", "name", "=", "'John Doe'"],
            "and",
            "date.year",
            ">",
            "2021",
        ]
    ]
    assert parse(
        "(((((((((((class=person or name='John Doe')))) and date.year > 2021)))))))"
    ).as_list() == [
        [
            ["class", "=", "person", "or", "name", "=", "'John Doe'"],
            "and",
            "date.year",
            ">",
            "2021",
        ]
    ]
