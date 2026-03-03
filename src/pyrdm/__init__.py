"""
pyrdm -- A declarative Object-RDF Mapper for Python.

Maps Python classes to RDF graphs using decorators, inspired by ORM
frameworks such as JPA and SQLAlchemy.

Basic usage
-----------
>>> from pyrdm import PyRDM, RDFRepository
>>> from rdflib import Namespace
>>>
>>> EX = Namespace("http://example.org/")
>>> mapper = PyRDM()
>>>
>>> @mapper.rdf_entity(EX.Person)
... class Person:
...     def __init__(self, uri, name):
...         self.uri = uri
...         self._name = name
...
...     @mapper.rdf_property(EX.name)
...     def name(self): pass
>>>
>>> person = Person(EX["person/1"], "Ana Maria")
>>> graph = mapper.to_rdf(person)
>>> repo = RDFRepository(mapper, graph, Person)
>>> repo.find_by_name(name="Ana Maria")
"""

from pyrdm.mapper import PyRDM
from pyrdm.repository import RDFRepository

__all__ = ["PyRDM", "RDFRepository"]
__version__ = "0.1.0"
__author__ = "Felipe dos Santos Goiabeira, Sergio Costa"
