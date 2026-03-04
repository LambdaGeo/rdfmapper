"""
Relationships example: one-to-one and one-to-many mappings.

Demonstrates:
  - @rdf_one_to_one  : Person -> Address
  - @rdf_one_to_many : Person -> Phone
  - Serialization and deserialization roundtrip
  - Querying with RDFRepository

Run from the repository root:
    python examples/relationships/person_address.py
"""

from rdflib import Namespace

from pyrdm import PyRDM, RDFRepository

EX = Namespace("http://example.org/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

mapper = PyRDM()


# ------------------------------------------------------------------
# Entity definitions
# ------------------------------------------------------------------

@mapper.rdf_entity(EX.Address)
class Address:
    def __init__(self, uri, street: str, city: str):
        self.uri = uri
        self._street = street
        self._city = city

    @mapper.rdf_property(EX.street, minCount=1)
    def street(self): pass

    @mapper.rdf_property(EX.city, minCount=1)
    def city(self): pass


@mapper.rdf_entity(EX.Phone)
class Phone:
    def __init__(self, uri, number: str, phone_type: str = "mobile"):
        self.uri = uri
        self._number = number
        self._phone_type = phone_type

    @mapper.rdf_property(EX.number, minCount=1)
    def number(self): pass

    @mapper.rdf_property(EX.phoneType)
    def phone_type(self): pass


@mapper.rdf_entity(EX.Person)
class Person:
    def __init__(self, uri, name: str, address=None, phones=None):
        self.uri = uri
        self._name = name
        self._address = address
        self._phones = phones or []

    @mapper.rdf_property(FOAF.name, minCount=1)
    def name(self): pass

    @mapper.rdf_one_to_one(EX.address, target_class=lambda: Address)
    def address(self): pass

    @mapper.rdf_one_to_many(EX.phone, target_class=lambda: Phone)
    def phones(self): pass


# ------------------------------------------------------------------
# 1. Build object graph
# ------------------------------------------------------------------

address = Address(
    uri=EX["address/1"],
    street="Rua Central, 123",
    city="Sao Luis",
)

phones = [
    Phone(uri=EX["phone/1"], number="+55 98 91234-5678", phone_type="mobile"),
    Phone(uri=EX["phone/2"], number="+55 98 3212-3456", phone_type="home"),
]

person = Person(
    uri=EX["person/1"],
    name="Felipe",
    address=address,
    phones=phones,
)

# ------------------------------------------------------------------
# 2. Serialize to RDF
# ------------------------------------------------------------------

graph = mapper.to_rdf(person)
print("=== Turtle serialization ===")
print(graph.serialize(format="turtle"))

# ------------------------------------------------------------------
# 3. Deserialize back to Python objects
# ------------------------------------------------------------------

restored = mapper.from_rdf(graph, Person, str(EX["person/1"]))
print("=== Deserialized object ===")
print("Name   :", restored.name)
print("Street :", restored.address.street)
print("City   :", restored.address.city)
print("Phones :", [(p.number, p.phone_type) for p in restored.phones])

# ------------------------------------------------------------------
# 4. Query with RDFRepository
# ------------------------------------------------------------------

people = [
    Person(
        uri=EX["person/2"],
        name="Ana",
        address=Address(EX["address/2"], "Av. Brasil, 50", "Sao Luis"),
    ),
    Person(
        uri=EX["person/3"],
        name="Bob",
        address=Address(EX["address/3"], "Rua das Flores, 10", "Imperatriz"),
    ),
    Person(
        uri=EX["person/4"],
        name="Ana",
        address=Address(EX["address/4"], "Rua Nova, 77", "Imperatriz"),
    ),
]
graph += mapper.to_rdf_many(people)

repo = RDFRepository(mapper, graph, Person)

print("\n=== find_by_name(name='Ana') ===")
for p in repo.find_by_name(name="Ana"):
    city = p.address.city if p.address else "no address"
    print(f"  - {p.name} | {city}")

print("\n=== group_by_count: addresses per city ===")
repo_addr = RDFRepository(mapper, graph, Address)
for row in repo_addr.group_by_count(Address, "city", order="DESC"):
    print(f"  {row['city']}: {row['count']}")