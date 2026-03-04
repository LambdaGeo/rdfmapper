# Background and Lineage

pyrdm is the result of a line of research on Object-RDF Mapping at the
[LambdaGeo Research Group](https://github.com/LambdaGeo), Federal University of
Maranhão (UFMA), Brazil. Understanding where it came from helps explain its design
decisions.

---

## The lineage

```
simpot (2022)
    └── RDFMapper TCC (2025)
            └── pyrdm (2025)

dbacademic-etl ──── used simpot in practice
                    and revealed its limitations
```

---

## simpot — the first step

**[simpot](https://github.com/LambdaGeo/simpot)** (Simple Object-Triple Mapping)
was the first tool developed at LambdaGeo to address Object-RDF mapping in Python.
It introduced the idea of using Python class attributes and decorators to describe
RDF mappings:

```python
from simpot import RdfsClass, BNamespace, graph
from rdflib.namespace import FOAF

class Person:
    nick = FOAF.nick
    name = FOAF.name

    @RdfsClass(FOAF.Person, None)
    @BNamespace("foaf", FOAF)
    def __init__(self, name, nick):
        self.nick = Literal(nick)
        self.name = Literal(name)

p = Person("Felipe", "felipeg")
print(graph(p).serialize())
```

simpot was simple by design — it mapped flat class attributes to RDF triples and
was published on PyPI. However, it lacked support for relationships between entities,
type-aware literal conversion, deserialization back to Python objects, and validation.

---

## dbacademic-etl — simpot in practice

**[dbacademic-etl](https://github.com/LambdaGeo/dbacademic-etl)** used simpot to
build an ETL pipeline over academic data, transforming institutional datasets into
RDF knowledge graphs. The practical experience of using simpot in this project made
its limitations clear: there was no way to express relationships between entities,
no deserialization, and no validation support.

This real-world use case motivated the need for a more expressive mapping framework.

---

## RDFMapper — the Bachelor's thesis

**[RDFMapper](https://github.com/felipestgoiabeira/RDFMapper)** was developed by
Felipe dos Santos Goiabeira as his Bachelor's thesis (TCC) at UFMA in 2025, advised
by Prof. Dr. Sergio Souza Costa.

Building on the ideas of simpot, RDFMapper introduced a significantly richer API:

- `@rdf_entity` and `@rdf_property` decorators with cardinality metadata
- `@rdf_one_to_one` and `@rdf_one_to_many` for entity relationships
- Bidirectional serialization (`to_rdf` / `from_rdf`) with circular reference safety
- A dynamic `RDFRepository` with `find_by_*`, `count_by_*`, and `group_by_count`
- Automatic SHACL shape generation and validation via `pyshacl`

RDFMapper was validated against two real datasets: a UFMA thesis registry (200+
records) and ANP fuel price data (millions of records), demonstrating its
applicability to both small and large-scale semantic data workflows.

The thesis is titled:

> *Mapeamento Declarativo para a Web Semântica: Desenvolvimento e Avaliação do
> Framework RDFMapper para Integração Objeto-RDF em Python*
> — Felipe dos Santos Goiabeira, UFMA, 2025.

---

## pyrdm — the packaged library

**pyrdm** takes RDFMapper's proven design and restructures it for open-source
distribution and long-term maintenance:

- `src` layout following Python packaging best practices
- `pyproject.toml` with declared dependencies and metadata
- Type annotations and NumPy-style docstrings on all public APIs
- Full pytest suite (46 tests)
- CI/CD with GitHub Actions
- JOSS-ready paper and `CITATION.cff`

The goal is to make the research contribution accessible and reusable by the
broader Python and Semantic Web communities.

---

## Comparison

| Feature | simpot | RDFMapper | pyrdm |
|---|:---:|:---:|:---:|
| Decorator-based mapping | ✅ | ✅ | ✅ |
| Relationships (1:1, 1:N) | ❌ | ✅ | ✅ |
| Deserialization (RDF → Python) | ❌ | ✅ | ✅ |
| Dynamic query repository | ❌ | ✅ | ✅ |
| SHACL validation | ❌ | ✅ | ✅ |
| Type annotations | ❌ | ❌ | ✅ |
| Test suite | partial | partial | ✅ (46 tests) |
| PyPI packaging | ✅ | ❌ | ✅ |
| CI/CD | ❌ | ❌ | ✅ |
