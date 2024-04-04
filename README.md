# GQL &ndash; the Gramps Query Language

This Python library provides GQL, a query language to a [Gramps](https://github.com/gramps-project/gramps) database. The syntax is inspired by JQL, the Jira Query Language.

## Installation

```
python -m pip install gramps-ql
```

## Usage

```python
from gramps_ql import iter_objects

db = ... # A Gramps DbReadBase instance

# iterate over private people
query = 'type=person AND private'

for obj in iter_objects(query, db):
    f(obj) # do something with the Gramps object obj