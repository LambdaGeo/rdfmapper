# Querying with RDFRepository

`RDFRepository` provides a dynamic query API that generates SPARQL at runtime
from method names, similar to Spring Data JPA.

```python
from pyrdm import RDFRepository

repo = RDFRepository(mapper, graph, Person)
```

## find_by_*

```python
# Exact match
repo.find_by_name(name="Felipe")

# Regex (case-insensitive)
repo.find_by_name_like(name="fel")

# Compound filter
repo.find_by_name_and_age(name="Felipe", age=25)

# With pagination
repo.find_by_name(name="Felipe", limit=10, offset=0)
```

## count_by_*

```python
repo.count_by_name(name="Felipe")
repo.count_by_name_and_age(name="Felipe", age=25)
```

## group_by_count

```python
repo.group_by_count(Person, "name", order="DESC")
# Returns: [{"name": "Felipe", "count": 3}, ...]
```
