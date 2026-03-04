# Getting Started

## Installation

```bash
pip install rdfmapper-py
```

To install from source with development dependencies:

```bash
git clone https://github.com/lambdageo/rdfmapper.git
cd rdfmapper
pip install -e ".[dev]"
```

**Requirements:** Python >= 3.10

---

## Your first mapping

### 1. Define a mapped class

```python
from rdflib import Namespace
from rdfmapper import RDFMapper

EX = Namespace("http://example.org/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

mapper = RDFMapper()

@mapper.rdf_entity(EX.Person)
class Person:
    def __init__(self, uri, name: str, age: int = None):
        self.uri = uri      # required: the RDF subject URI
        self._name = name
        self._age = age

    @mapper.rdf_property(FOAF.name, minCount=1)
    def name(self): pass

    @mapper.rdf_property(FOAF.age)
    def age(self): pass
```

### 2. Serialize to RDF

```python
person = Person(uri=EX["person/1"], name="Felipe", age=25)
graph = mapper.to_rdf(person)
print(graph.serialize(format="turtle"))
```

Output:

```turtle
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://example.org/person/1>
    a <http://example.org/Person> ;
    foaf:age 25 ;
    foaf:name "Felipe" .
```

### 3. Deserialize back to Python

```python
restored = mapper.from_rdf(graph, Person, str(EX["person/1"]))
print(restored.name)  # Felipe
print(restored.age)   # 25
```

### 4. Query with the repository

```python
from rdfmapper import RDFRepository

repo = RDFRepository(mapper, graph, Person)

# exact match
repo.find_by_name(name="Felipe")

# count
repo.count_by_name(name="Felipe")
```

### 5. Validate with SHACL

```python
conforms, _, report = mapper.validate(graph, entity_class=Person)
print("Conforms:", conforms)
```

---

## Next steps

- [Mapping classes in depth](guide/mapping.md)
- [Defining relationships](guide/relationships.md)
- [Querying with RDFRepository](guide/querying.md)
- [SHACL validation](guide/shacl.md)
