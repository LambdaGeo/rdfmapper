# pyrdm

**pyrdm** is a declarative Object-RDF Mapper for Python. It lets you map Python
classes to RDF graphs using decorators — no SPARQL, no manual triple manipulation.

```python
from pyrdm import PyRDM

mapper = PyRDM()

@mapper.rdf_entity("http://xmlns.com/foaf/0.1/Person")
class Person:
    def __init__(self, uri, name: str):
        self.uri = uri
        self._name = name

    @mapper.rdf_property("http://xmlns.com/foaf/0.1/name", minCount=1)
    def name(self): pass

person = Person("http://example.org/person/1", "Felipe")
graph = mapper.to_rdf(person)
print(graph.serialize(format="turtle"))
```

## Features

- Declarative class-to-RDF mapping via decorators
- One-to-one and one-to-many relationships
- Automatic serialization and deserialization
- Dynamic query repository (`find_by_*`, `count_by_*`, `group_by_count`)
- Automatic SHACL shape generation and validation
- Circular reference safety

## Installation

```bash
pip install pyrdm
```

## Origin

pyrdm grew out of research at the [LambdaGeo Group](https://github.com/LambdaGeo),
Federal University of Maranhão (UFMA). See the [Background](background.md) page for
the full story.
