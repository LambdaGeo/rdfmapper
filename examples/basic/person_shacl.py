"""
Basic example: mapping a Person class to RDF and validating with SHACL.

Run from the repository root:
    python examples/basic/person_shacl.py
"""

from rdflib import Namespace

from rdfmapper import RDFMapper

EX = Namespace("http://example.org/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

mapper = RDFMapper()


@mapper.rdf_entity(EX.Person)
class Person:
    def __init__(self, uri, nome: str, idade: int, email: str):
        self.uri = uri
        self._nome = nome
        self._idade = idade
        self._email = email

    @mapper.rdf_property(FOAF.name, minCount=1)
    def nome(self): pass

    @mapper.rdf_property(FOAF.age)
    def idade(self): pass

    @mapper.rdf_property(FOAF.mbox)
    def email(self): pass


# 1. Serialize to RDF
person = Person(uri="https://example.org/persons/1", nome="Felipe", idade=25, email="felipe@example.com")
graph = mapper.to_rdf(person)
print("=== Turtle serialization ===")
print(graph.serialize(format="turtle"))

# 2. Auto-generate SHACL shape
print("=== Generated SHACL shape ===")
print(mapper.to_shacl(Person).serialize(format="turtle"))

# 3. Validate a valid object
conforms, _, report = mapper.validate(graph, entity_class=Person)
print("=== Validation (valid object) ===")
print("Conforms:", conforms)
print(report)

# 4. Validate invalid object (nome missing)
invalid_person = Person(uri="https://example.org/persons/2", nome=None, idade=30, email="invalid@example.com")
invalid_graph = mapper.to_rdf(invalid_person)
conforms, _, report = mapper.validate(invalid_graph, entity_class=Person)
print("=== Validation (invalid object) ===")
print("Conforms:", conforms)
print(report)