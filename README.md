# pyrdm

**pyrdm** is a declarative Object-RDF Mapper for Python. It lets you map Python classes to RDF graphs using decorators, inspired by ORM frameworks such as JPA and SQLAlchemy, without requiring you to write SPARQL or manipulate triples manually.

[![Tests](https://github.com/lambdageo/pyrdm/actions/workflows/ci.yml/badge.svg)](https://github.com/lambdageo/pyrdm/actions)
[![PyPI](https://img.shields.io/pypi/v/pyrdm)](https://pypi.org/project/pyrdm/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/pyrdm)](https://pypi.org/project/pyrdm/)

---

## Features

- Declarative mapping of Python classes to RDF types and predicates via decorators
- Support for `one-to-one` and `one-to-many` relationships
- Automatic serialization and deserialization between Python objects and RDF graphs
- Dynamic query repository (`find_by_*`, `count_by_*`, `group_by_count`) powered by SPARQL
- Automatic SHACL shape generation and validation from class metadata
- Circular reference detection during serialization and deserialization
- Type-aware literal conversion (int, float, bool, date, datetime)

---

## Installation

```bash
pip install pyrdm
```

Or install from source:

```bash
git clone https://github.com/lambdageo/pyrdm.git
cd pyrdm
pip install -e ".[dev]"
```

---

## Quick start

```python
from rdflib import Namespace
from pyrdm import PyRDM, RDFRepository

EX = Namespace("http://example.org/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

mapper = PyRDM()


@mapper.rdf_entity(EX.Person)
class Person:
    def __init__(self, uri, name: str, age: int = None):
        self.uri = uri
        self._name = name
        self._age = age

    @mapper.rdf_property(FOAF.name, minCount=1)
    def name(self): pass

    @mapper.rdf_property(FOAF.age)
    def age(self): pass


# Serialize to RDF
person = Person(uri=EX["person/1"], name="Felipe", age=25)
graph = mapper.to_rdf(person)
print(graph.serialize(format="turtle"))

# Deserialize back to Python
restored = mapper.from_rdf(graph, Person, str(EX["person/1"]))
print(restored.name)  # Felipe

# Query with repository
repo = RDFRepository(mapper, graph, Person)
results = repo.find_by_name(name="Felipe")
count = repo.count_by_name(name="Felipe")
```

---

## Relationships

```python
@mapper.rdf_entity(EX.Address)
class Address:
    def __init__(self, uri, city: str):
        self.uri = uri
        self._city = city

    @mapper.rdf_property(EX.city)
    def city(self): pass


@mapper.rdf_entity(EX.Person)
class Person:
    def __init__(self, uri, name: str, address=None, phones=None):
        self.uri = uri
        self._name = name
        self._address = address
        self._phones = phones or []

    @mapper.rdf_property(FOAF.name)
    def name(self): pass

    @mapper.rdf_one_to_one(EX.address, target_class=lambda: Address)
    def address(self): pass

    @mapper.rdf_one_to_many(EX.phone, target_class=lambda: Phone)
    def phones(self): pass
```

---

## SHACL validation

```python
# Auto-generate SHACL shape from class metadata
shacl_graph = mapper.to_shacl(Person)

# Validate an RDF graph
conforms, _, report = mapper.validate(graph, entity_class=Person)
print("Conforms:", conforms)
print(report)
```

---

## Dynamic repository queries

```python
repo = RDFRepository(mapper, graph, Person)

# Exact match
repo.find_by_name(name="Felipe")

# Regex match
repo.find_by_name_like(name="Fel")

# Compound filter
repo.find_by_name_and_age(name="Felipe", age=25)

# Pagination
repo.find_by_name(name="Felipe", limit=10, offset=0)

# Count
repo.count_by_name(name="Felipe")

# Aggregation
repo.group_by_count(Person, "name", order="DESC")
```

---

## Examples

See the [`examples/`](examples/) directory for complete runnable scripts:

- [`examples/basic/person_shacl.py`](examples/basic/person_shacl.py) — basic mapping and SHACL validation
- [`examples/relationships/person_address.py`](examples/relationships/person_address.py) — one-to-one and one-to-many relationships

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/
```

---

## Citation

If you use pyrdm in your research, please cite:

```bibtex
@software{goiabeira2025pyrdm,
  author    = {Goiabeira, Felipe dos Santos and Costa, Sergio Souza},
  title     = {pyrdm: A Declarative Object-RDF Mapper for Python},
  year      = {2025},
  publisher = {GitHub},
  url       = {https://github.com/lambdageo/pyrdm}
}
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Acknowledgements

pyrdm was originally developed as part of a Bachelor's thesis at the Federal University of Maranhão (UFMA) by Felipe dos Santos Goiabeira, advised by Prof. Dr. Sergio Souza Costa, LambdaGeo Research Group.
