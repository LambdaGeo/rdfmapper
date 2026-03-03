"""
Tests for pyrdm.

Run with:
    pytest tests/
"""

from __future__ import annotations

import pytest
from rdflib import Literal, Namespace, URIRef, Graph
from rdflib.namespace import RDF, XSD

from pyrdm import PyRDM, RDFRepository

EX = Namespace("http://example.org/")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mapper() -> PyRDM:
    return PyRDM()


@pytest.fixture
def person_class(mapper):
    @mapper.rdf_entity(EX.Person)
    class Person:
        def __init__(self, uri, name: str, age: int = None):
            self.uri = uri
            self._name = name
            self._age = age

        @mapper.rdf_property(EX.name, minCount=1)
        def name(self):
            pass

        @mapper.rdf_property(EX.age)
        def age(self):
            pass

    return Person


@pytest.fixture
def address_class(mapper):
    @mapper.rdf_entity(EX.Address)
    class Address:
        def __init__(self, uri, street: str):
            self.uri = uri
            self._street = street

        @mapper.rdf_property(EX.street)
        def street(self):
            pass

    return Address


@pytest.fixture
def person_with_address_class(mapper, address_class):
    Address = address_class

    @mapper.rdf_entity(EX.PersonWithAddress)
    class PersonWithAddress:
        def __init__(self, uri, name: str, address=None):
            self.uri = uri
            self._name = name
            self._address = address

        @mapper.rdf_property(EX.name)
        def name(self):
            pass

        @mapper.rdf_one_to_one(EX.address, target_class=lambda: Address)
        def address(self):
            pass

    return PersonWithAddress


@pytest.fixture
def team_class(mapper, person_class):
    Person = person_class

    @mapper.rdf_entity(EX.Team)
    class Team:
        def __init__(self, uri, team_name: str, members: list = None):
            self.uri = uri
            self._team_name = team_name
            self._members = members or []

        @mapper.rdf_property(EX.teamName)
        def team_name(self):
            pass

        @mapper.rdf_one_to_many(EX.member, target_class=lambda: Person)
        def members(self):
            pass

    return Team


@pytest.fixture
def populated_graph(mapper, person_class):
    people = [
        person_class(EX["person/1"], "Ana"),
        person_class(EX["person/2"], "Bob"),
        person_class(EX["person/3"], "Ana"),
    ]
    return mapper.to_rdf_many(people), person_class


# ---------------------------------------------------------------------------
# 1. Decorator registration
# ---------------------------------------------------------------------------

class TestDecoratorRegistration:

    def test_rdf_entity_sets_type_uri(self, person_class):
        assert person_class._rdf_type_uri == URIRef(EX.Person)

    def test_rdf_entity_registers_class(self, mapper, person_class):
        assert "Person" in mapper._entities

    def test_rdf_property_sets_predicate(self, person_class):
        prop = person_class.name
        assert prop.fget._rdf_predicate == URIRef(EX.name)

    def test_rdf_property_is_not_relationship(self, person_class):
        assert person_class.name.fget._is_relationship is False

    def test_rdf_one_to_one_is_relationship(self, person_with_address_class):
        prop = person_with_address_class.address
        assert prop.fget._is_relationship is True
        assert prop.fget._relationship_type == "one_to_one"

    def test_rdf_one_to_many_is_relationship(self, team_class):
        prop = team_class.members
        assert prop.fget._is_relationship is True
        assert prop.fget._relationship_type == "one_to_many"


# ---------------------------------------------------------------------------
# 2. Serialization
# ---------------------------------------------------------------------------

class TestToRdf:

    def test_returns_graph(self, mapper, person_class):
        p = person_class(EX["person/1"], "Ana")
        assert isinstance(mapper.to_rdf(p), Graph)

    def test_type_triple_present(self, mapper, person_class):
        p = person_class(EX["person/1"], "Ana")
        graph = mapper.to_rdf(p)
        assert (URIRef(EX["person/1"]), RDF.type, URIRef(EX.Person)) in graph

    def test_property_triple_present(self, mapper, person_class):
        p = person_class(EX["person/1"], "Ana")
        graph = mapper.to_rdf(p)
        triples = list(graph.triples((URIRef(EX["person/1"]), URIRef(EX.name), None)))
        assert len(triples) == 1
        assert str(triples[0][2]) == "Ana"

    def test_none_property_not_serialized(self, mapper, person_class):
        p = person_class(EX["person/1"], "Ana", age=None)
        graph = mapper.to_rdf(p)
        triples = list(graph.triples((URIRef(EX["person/1"]), URIRef(EX.age), None)))
        assert len(triples) == 0

    def test_integer_datatype(self, mapper, person_class):
        p = person_class(EX["person/1"], "Ana", age=30)
        graph = mapper.to_rdf(p)
        triples = list(graph.triples((URIRef(EX["person/1"]), URIRef(EX.age), None)))
        assert triples[0][2].datatype == XSD.integer

    def test_one_to_one_relationship(self, mapper, address_class, person_with_address_class):
        addr = address_class(EX["address/1"], "Rua Central")
        person = person_with_address_class(EX["person/1"], "Ana", address=addr)
        graph = mapper.to_rdf(person)
        assert (URIRef(EX["person/1"]), URIRef(EX.address), URIRef(EX["address/1"])) in graph
        assert (URIRef(EX["address/1"]), RDF.type, URIRef(EX.Address)) in graph

    def test_one_to_many_relationship(self, mapper, person_class, team_class):
        p1 = person_class(EX["person/1"], "Ana")
        p2 = person_class(EX["person/2"], "Bob")
        team = team_class(EX["team/1"], "Alpha", members=[p1, p2])
        graph = mapper.to_rdf(team)
        assert (URIRef(EX["team/1"]), URIRef(EX.member), URIRef(EX["person/1"])) in graph
        assert (URIRef(EX["team/1"]), URIRef(EX.member), URIRef(EX["person/2"])) in graph

    def test_circular_reference_no_infinite_loop(self, mapper, person_with_address_class, address_class):
        addr = address_class(EX["address/1"], "Rua Central")
        person = person_with_address_class(EX["person/1"], "Ana", address=addr)
        graph = mapper.to_rdf(person)
        assert graph is not None

    def test_to_rdf_many(self, mapper, person_class):
        people = [person_class(EX[f"person/{i}"], f"Person {i}") for i in range(5)]
        graph = mapper.to_rdf_many(people)
        subjects = set(graph.subjects(RDF.type, URIRef(EX.Person)))
        assert len(subjects) == 5


# ---------------------------------------------------------------------------
# 3. Deserialization
# ---------------------------------------------------------------------------

class TestFromRdf:

    def test_roundtrip_string(self, mapper, person_class):
        p = person_class(EX["person/1"], "Ana")
        graph = mapper.to_rdf(p)
        restored = mapper.from_rdf(graph, person_class, str(EX["person/1"]))
        assert restored.name == "Ana"

    def test_roundtrip_integer(self, mapper, person_class):
        p = person_class(EX["person/1"], "Ana", age=28)
        graph = mapper.to_rdf(p)
        restored = mapper.from_rdf(graph, person_class, str(EX["person/1"]))
        assert restored.age == 28

    def test_roundtrip_one_to_one(self, mapper, address_class, person_with_address_class):
        addr = address_class(EX["address/1"], "Rua Central")
        person = person_with_address_class(EX["person/1"], "Ana", address=addr)
        graph = mapper.to_rdf(person)
        restored = mapper.from_rdf(graph, person_with_address_class, str(EX["person/1"]))
        assert restored.address.street == "Rua Central"

    def test_circular_cache_reuse(self, mapper, address_class, person_with_address_class):
        addr = address_class(EX["address/1"], "Rua Central")
        person = person_with_address_class(EX["person/1"], "Ana", address=addr)
        graph = mapper.to_rdf(person)
        restored = mapper.from_rdf(graph, person_with_address_class, str(EX["person/1"]))
        assert restored is not None


# ---------------------------------------------------------------------------
# 4. Type conversion
# ---------------------------------------------------------------------------

class TestTypeConversion:

    def test_bool_literal(self, mapper):
        assert mapper._python_to_literal(True).datatype == XSD.boolean

    def test_int_literal(self, mapper):
        assert mapper._python_to_literal(42).datatype == XSD.integer

    def test_float_literal(self, mapper):
        assert mapper._python_to_literal(3.14).datatype == XSD.double

    def test_str_literal(self, mapper):
        assert str(mapper._python_to_literal("hello")) == "hello"

    def test_literal_to_int(self, mapper):
        assert mapper._literal_to_python(Literal(7, datatype=XSD.integer)) == 7

    def test_literal_to_bool_true(self, mapper):
        assert mapper._literal_to_python(Literal("true", datatype=XSD.boolean)) is True

    def test_literal_to_bool_false(self, mapper):
        assert mapper._literal_to_python(Literal("false", datatype=XSD.boolean)) is False

    def test_literal_none_returns_none(self, mapper):
        assert mapper._literal_to_python(None) is None

    def test_datetime_before_date(self, mapper):
        import datetime
        dt = datetime.datetime(2024, 1, 15, 10, 30)
        lit = mapper._python_to_literal(dt)
        assert lit.datatype == XSD.dateTime

    def test_date_literal(self, mapper):
        import datetime
        d = datetime.date(2024, 1, 15)
        lit = mapper._python_to_literal(d)
        assert lit.datatype == XSD.date


# ---------------------------------------------------------------------------
# 5. RDFRepository
# ---------------------------------------------------------------------------

class TestRDFRepository:

    def test_find_by_exact(self, mapper, populated_graph):
        graph, Person = populated_graph
        repo = RDFRepository(mapper, graph, Person)
        assert len(repo.find_by_name(name="Ana")) == 2

    def test_find_by_like(self, mapper, populated_graph):
        graph, Person = populated_graph
        repo = RDFRepository(mapper, graph, Person)
        assert len(repo.find_by_name_like(name="An")) == 2

    def test_find_by_no_results(self, mapper, populated_graph):
        graph, Person = populated_graph
        repo = RDFRepository(mapper, graph, Person)
        assert repo.find_by_name(name="Zara") == []

    def test_count_by(self, mapper, populated_graph):
        graph, Person = populated_graph
        repo = RDFRepository(mapper, graph, Person)
        assert repo.count_by_name(name="Ana") == 2

    def test_find_by_limit(self, mapper, populated_graph):
        graph, Person = populated_graph
        repo = RDFRepository(mapper, graph, Person)
        assert len(repo.find_by_name(name="Ana", limit=1)) == 1

    def test_find_by_offset(self, mapper, populated_graph):
        graph, Person = populated_graph
        repo = RDFRepository(mapper, graph, Person)
        assert len(repo.find_by_name(name="Ana", limit=10, offset=1)) == 1

    def test_group_by_count_desc(self, mapper, populated_graph):
        graph, Person = populated_graph
        repo = RDFRepository(mapper, graph, Person)
        result = repo.group_by_count(Person, "name", order="DESC")
        counts = {r["name"]: r["count"] for r in result}
        assert counts["Ana"] == 2
        assert counts["Bob"] == 1

    def test_group_by_count_invalid_order(self, mapper, populated_graph):
        graph, Person = populated_graph
        repo = RDFRepository(mapper, graph, Person)
        with pytest.raises(ValueError):
            repo.group_by_count(Person, "name", order="RANDOM")

    def test_group_by_invalid_field(self, mapper, populated_graph):
        graph, Person = populated_graph
        repo = RDFRepository(mapper, graph, Person)
        with pytest.raises(ValueError):
            repo.group_by_count(Person, "nonexistent_field")

    def test_unknown_method_raises(self, mapper, populated_graph):
        graph, Person = populated_graph
        repo = RDFRepository(mapper, graph, Person)
        with pytest.raises(AttributeError):
            repo.unknown_method()

    def test_missing_field_value_raises(self, mapper, populated_graph):
        graph, Person = populated_graph
        repo = RDFRepository(mapper, graph, Person)
        with pytest.raises((ValueError, TypeError)):
            repo.find_by_name()


# ---------------------------------------------------------------------------
# 6. SHACL validation
# ---------------------------------------------------------------------------

class TestShacl:

    def test_valid_object_conforms(self, mapper, person_class):
        p = person_class(EX["person/1"], "Ana")
        graph = mapper.to_rdf(p)
        conforms, _, _ = mapper.validate(graph, entity_class=person_class)
        assert conforms is True

    def test_missing_required_field_fails(self, mapper, person_class):
        p = person_class(EX["person/1"], None)
        graph = mapper.to_rdf(p)
        conforms, _, report = mapper.validate(graph, entity_class=person_class)
        assert conforms is False
        assert "Violation" in report

    def test_validate_without_entity_class_raises(self, mapper, person_class):
        p = person_class(EX["person/1"], "Ana")
        graph = mapper.to_rdf(p)
        with pytest.raises(ValueError):
            mapper.validate(graph)

    def test_to_shacl_returns_graph(self, mapper, person_class):
        shacl = mapper.to_shacl(person_class)
        assert isinstance(shacl, Graph)
        assert len(shacl) > 0

    def test_to_shacl_has_node_shape(self, mapper, person_class):
        SH = Namespace("http://www.w3.org/ns/shacl#")
        shacl = mapper.to_shacl(person_class)
        shapes = list(shacl.subjects(RDF.type, SH.NodeShape))
        assert len(shapes) == 1
