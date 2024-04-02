from gramps_ql import parse


def test_single():
    assert parse("type=person").as_list() == ["type", "=", "person"]


def test_two():
    assert parse("type=person or date.year > 2021").as_list() == [
        [
            "type",
            "=",
            "person",
            "or",
            "date.year",
            ">",
            "2021",
        ]
    ]


def test_three():
    assert parse("type=person or name='John Doe' and date.year > 2021").as_list() == [
        [
            "type",
            "=",
            "person",
            "or",
            ["name", "=", "'John Doe'", "and", "date.year", ">", "2021"],
        ]
    ]
    assert parse("type=person and name='John Doe' or date.year > 2021").as_list() == [
        [
            ["type", "=", "person", "and", "name", "=", "'John Doe'"],
            "or",
            "date.year",
            ">",
            "2021",
        ]
    ]
    assert parse("type=person and name='John Doe' or only_id").as_list() == [
        [
            ["type", "=", "person", "and", "name", "=", "'John Doe'"],
            "or",
            "only_id",
        ]
    ]


def test_brackets():
    assert parse("(type=person or name='John Doe') and date.year > 2021").as_list() == [
        [
            ["type", "=", "person", "or", "name", "=", "'John Doe'"],
            "and",
            "date.year",
            ">",
            "2021",
        ]
    ]
    assert parse(
        "(((((((((((type=person or name='John Doe')))) and date.year > 2021)))))))"
    ).as_list() == [
        [
            ["type", "=", "person", "or", "name", "=", "'John Doe'"],
            "and",
            "date.year",
            ">",
            "2021",
        ]
    ]
