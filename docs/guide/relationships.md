# Relationships

## One-to-one

Use `@rdf_one_to_one` to map a property to a single related entity.
Use a `lambda` for the `target_class` to avoid forward reference issues.

```python
@mapper.rdf_one_to_one(EX.address, target_class=lambda: Address)
def address(self): pass
```

## One-to-many

Use `@rdf_one_to_many` to map a property to a list of related entities.

```python
@mapper.rdf_one_to_many(EX.phone, target_class=lambda: Phone)
def phones(self): pass
```

## Full example

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

!!! note "Circular references"
    rdfmapper detects circular references during both serialization and deserialization
    and handles them safely without infinite recursion.
