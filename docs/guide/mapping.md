# Mapping classes

## @rdf_entity

Maps a Python class to an RDF type. The class must have a `uri` attribute that
identifies the RDF subject.

```python
@mapper.rdf_entity(EX.Person)
class Person:
    def __init__(self, uri, name: str):
        self.uri = uri
        self._name = name
```

## @rdf_property

Maps a Python property to an RDF predicate. The property name must match the
private attribute (prefixed with `_`).

```python
@mapper.rdf_property(FOAF.name, minCount=1, maxCount=1)
def name(self): pass
```

| Parameter | Description |
|---|---|
| `predicate_uri` | URI of the RDF predicate |
| `minCount` | Minimum cardinality for SHACL (default: 0) |
| `maxCount` | Maximum cardinality for SHACL (default: 1) |

## Supported Python types

pyrdm automatically converts Python values to RDF Literals with the correct datatype:

| Python type | RDF datatype |
|---|---|
| `bool` | `xsd:boolean` |
| `int` | `xsd:integer` |
| `float` | `xsd:double` |
| `datetime.datetime` | `xsd:dateTime` |
| `datetime.date` | `xsd:date` |
| `str` | `xsd:string` |
