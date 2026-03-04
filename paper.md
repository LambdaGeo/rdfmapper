---
title: 'rdfmapper: A Declarative Object-RDF Mapper for Python'
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
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Sergio Souza Costa
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: Federal University of Maranhão (UFMA), Brazil
    index: 1
date: 2025-01-01
bibliography: paper.bib
---

# Summary

`rdfmapper` is a Python library that provides declarative Object-RDF Mapping (ORM),
enabling developers to map Python classes to RDF graphs [@w3c_rdf11_concepts] using
a decorator-based API without writing SPARQL [@w3c_sparql] queries or manipulating
triples directly. The library is inspired by established ORM frameworks such as
JPA [@jpa_spec] and SQLAlchemy [@sqlalchemy], adapted to the requirements of the
Semantic Web [@heath2011linked].

Built on top of `rdflib` [@rdflib] and `pyshacl` [@pyshacl], `rdfmapper` bridges the
gap between object-oriented programming and RDF-based knowledge representation.
It handles serialization and deserialization of Python objects to and from RDF
graphs, generates SHACL shapes [@w3c_shacl] automatically from class metadata,
and provides a dynamic repository API for querying entities by field values
without writing SPARQL.

# Statement of Need

The Semantic Web ecosystem provides powerful standards — RDF, RDFS, OWL, SPARQL,
and SHACL — for representing and querying structured knowledge. However, integrating
these technologies into Python applications typically requires developers to work
directly with low-level graph APIs such as `rdflib` [@rdflib], managing URIs,
triples, and SPARQL queries explicitly. This creates a significant productivity
barrier, especially for researchers and developers who are domain experts but not
Semantic Web specialists.

The idea of bridging object-oriented models and graph data is not new. Fowler's
patterns of enterprise application architecture [@fowler2002patterns] established
the ORM as a foundational design pattern for relational databases, later
formalized in Java through the JPA specification [@jpa_spec] and in Python through
SQLAlchemy [@sqlalchemy]. In the RDF world, Empire [@bischof2011empire] brought a
JPA-style annotation API to Java, and RDFAlchemy [@rdfalchemy] and SuRF [@surf]
provided early attempts at ORM-style access to RDF stores in Python. However,
both have been unmaintained since 2012 and 2016 respectively, and neither supports
modern Python packaging, type annotations, or SHACL validation.

`rdfmapper` fills this gap for the Python ecosystem by providing:

- A decorator API (`@rdf_entity`, `@rdf_property`, `@rdf_one_to_one`,
  `@rdf_one_to_many`) that keeps the mapping co-located with the class definition,
  reducing boilerplate and improving readability.
- Automatic serialization and deserialization between Python objects and RDF graphs,
  including circular reference detection.
- A dynamic query repository that generates SPARQL queries at runtime from method
  names, supporting exact match, regex match, compound filters, pagination, count,
  and aggregation.
- Automatic SHACL shape generation from class metadata and validation via `pyshacl`.

`rdfmapper` grew directly from research at the LambdaGeo Group at UFMA. Its predecessor,
`simpot` [@simpot], introduced a basic decorator approach to RDF mapping in Python.
The practical experience of using `simpot` in the `dbacademic-etl` project
[@costa2020dbacademic] — a pipeline connecting open academic data from Brazilian
institutions into RDF knowledge graphs — revealed the need for a richer mapping
framework supporting relationships, deserialization, and validation. This motivated
the development of RDFMapper as a Bachelor's thesis [@goiabeira2025rdfmapper], of
which `rdfmapper` is the packaged and maintained evolution.

# Design and API

The central class is `RDFMapper`, which acts both as a decorator factory and as the
serialization engine. A typical mapping looks as follows:

```python
from rdflib import Namespace
from rdfmapper import RDFMapper, RDFRepository

EX = Namespace("http://example.org/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

mapper = RDFMapper()

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
in `@rdf_property` and validated via `pyshacl` [@pyshacl]:

```python
conforms, _, report = mapper.validate(graph, entity_class=Person)
```

# Acknowledgements

This work was developed as part of a Bachelor's thesis at the Federal University of
Maranhão (UFMA), Brazil, within the LambdaGeo Research Group. The authors thank
the UFMA Department of Computer Science for institutional support.

# References