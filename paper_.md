---
title: 'pyrdm: A Declarative Object-RDF Mapper for Python'
tags:
  - Python
  - Semantic Web
  - RDF
  - Linked Data
  - ORM
  - SHACL
  - SPARQL
authors:
  - name: Felipe dos Santos Goiabeira
    affiliation: "1"
  - name: Sergio Souza Costa
    orcid: 0000-0002-0232-4549
    affiliation: "1"
affiliations:
  - name: Federal University of Maranhão (UFMA), Brazil
    index: 1
date: 2025-01-01
bibliography: paper.bib
---

# Summary

`pyrdm` is a Python library that provides declarative Object-RDF Mapping (ORM),
enabling developers to map Python classes to RDF graphs using a decorator-based API
without writing SPARQL queries or manipulating triples directly. The library is
inspired by established ORM frameworks such as JPA [@jpa] and SQLAlchemy
[@sqlalchemy], adapted to the requirements of the Semantic Web.

Built on top of `rdflib` [@rdflib] and `pyshacl` [@pyshacl], `pyrdm` bridges the
gap between object-oriented programming and RDF-based knowledge representation.
It handles serialization and deserialization of Python objects to and from RDF
graphs, generates SHACL shapes automatically from class metadata, and provides a
dynamic repository API for querying entities by field values without writing SPARQL.

# Statement of Need

The Semantic Web ecosystem provides powerful standards — RDF, RDFS, OWL, SPARQL,
and SHACL — for representing and querying structured knowledge. However, integrating
these technologies into Python applications typically requires developers to work
directly with low-level graph APIs such as `rdflib`, managing URIs, triples, and
SPARQL queries explicitly. This creates a significant productivity barrier, especially
for researchers and developers who are domain experts but not Semantic Web specialists.

Existing tools such as `rdflib` [@rdflib] provide excellent low-level primitives,
and `pyshacl` [@pyshacl] enables SHACL validation, but neither offers a high-level,
ORM-style abstraction for mapping Python objects to RDF graphs declaratively.
Mapping languages such as RML and R2RML address the problem of mapping tabular or
semi-structured data to RDF, but are not designed for use with Python class hierarchies
and require external configuration files.

`pyrdm` fills this gap by providing:

- A decorator API (`@rdf_entity`, `@rdf_property`, `@rdf_one_to_one`,
  `@rdf_one_to_many`) that keeps the mapping co-located with the class definition,
  reducing boilerplate and improving readability.
- Automatic serialization and deserialization between Python objects and RDF graphs,
  including circular reference detection.
- A dynamic query repository that generates SPARQL queries at runtime from
  method names, supporting exact match, regex match, compound filters, pagination,
  count, and aggregation.
- Automatic SHACL shape generation from class metadata and validation via `pyshacl`.

This makes `pyrdm` particularly suited for research projects that combine
object-oriented Python workflows with Semantic Web data publishing, such as
producing Linked Data from scientific datasets.

# Design and API

The central class is `PyRDM`, which acts both as a decorator factory and as the
serialization engine. A typical mapping looks as follows:

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
```

Serialization and deserialization are performed via `mapper.to_rdf(obj)` and
`mapper.from_rdf(graph, cls, uri)`. The `RDFRepository` class provides a
dynamic query API:

```python
repo = RDFRepository(mapper, graph, Person)
repo.find_by_name(name="Felipe")
repo.find_by_name_like(name="Fel")
repo.count_by_name(name="Felipe")
repo.group_by_count(Person, "name", order="DESC")
```

SHACL shapes are generated automatically from the cardinality constraints declared
in `@rdf_property` and validated via `pyshacl`:

```python
conforms, _, report = mapper.validate(graph, entity_class=Person)
```

# Acknowledgements

This work was developed as part of a Bachelor's thesis at the Federal University of
Maranhão (UFMA), Brazil, within the LambdaGeo Research Group. The authors thank
the UFMA Department of Computer Science for institutional support.

# References
