from __future__ import annotations

import datetime
import inspect
from typing import Any, cast, Optional, Type

from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef, XSD
from pyshacl import validate


class RDFMapper:
    """
    A declarative Object-RDF Mapper for Python.

    Maps Python classes to RDF graphs using decorators, inspired by ORM
    frameworks such as JPA and SQLAlchemy.

    Examples
    --------
    >>> from rdflib import Namespace
    >>> EX = Namespace("http://example.org/")
    >>> mapper = RDFMapper()

    >>> @mapper.rdf_entity(EX.Person)
    ... class Person:
    ...     def __init__(self, uri, name):
    ...         self.uri = uri
    ...         self._name = name
    ...
    ...     @mapper.rdf_property(EX.name)
    ...     def name(self): pass
    """

    def __init__(self) -> None:
        self._entities: dict[str, type] = {}

    # ------------------------------------------------------------------
    # Decorators
    # ------------------------------------------------------------------

    def rdf_entity(self, rdf_type_uri: str):
        """
        Class decorator that maps a Python class to an RDF type.

        Parameters
        ----------
        rdf_type_uri : str
            The URI of the RDF type (e.g. ``EX.Person``).
        """
        def wrapper(cls):
            cls._rdf_type_uri = URIRef(rdf_type_uri)
            cls._rdf_properties = {}
            self._entities[cls.__name__] = cls
            return cls
        return wrapper

    def rdf_property(self, predicate_uri: str, minCount: int = 0, maxCount: int = 1):
        """
        Property decorator that maps a class attribute to an RDF predicate.

        Parameters
        ----------
        predicate_uri : str
            The URI of the RDF predicate.
        minCount : int, optional
            Minimum cardinality for SHACL validation, by default 0.
        maxCount : int, optional
            Maximum cardinality for SHACL validation, by default 1.
        """
        def decorator(func):
            attr_name = func.__name__

            def getter(self):
                return getattr(self, f"_{attr_name}")

            def setter(self, value):
                setattr(self, f"_{attr_name}", value)

            getter._rdf_predicate = URIRef(predicate_uri)
            getter._is_rdf_property = True
            getter._is_relationship = False
            getter._min_count = minCount
            getter._max_count = maxCount

            return property(getter, setter)
        return decorator

    def rdf_one_to_one(self, predicate_uri: str, target_class: Type):
        """
        Property decorator for a 1:1 relationship between two RDF entities.

        Parameters
        ----------
        predicate_uri : str
            The URI of the RDF predicate.
        target_class : Type
            The target entity class (use a lambda for forward references).
        """
        def decorator(func):
            attr_name = func.__name__

            def getter(self):
                return getattr(self, f"_{attr_name}")

            def setter(self, value):
                setattr(self, f"_{attr_name}", value)

            getter._rdf_predicate = URIRef(predicate_uri)
            getter._is_rdf_property = True
            getter._is_relationship = True
            getter._relationship_type = "one_to_one"
            getter._target_class = target_class
            return property(getter, setter)
        return decorator

    def rdf_one_to_many(self, predicate_uri: str, target_class: Type):
        """
        Property decorator for a 1:N relationship between two RDF entities.

        Parameters
        ----------
        predicate_uri : str
            The URI of the RDF predicate.
        target_class : Type
            The target entity class (use a lambda for forward references).
        """
        def decorator(func):
            attr_name = func.__name__

            def getter(self):
                return getattr(self, f"_{attr_name}")

            def setter(self, value):
                setattr(self, f"_{attr_name}", value)

            getter._rdf_predicate = URIRef(predicate_uri)
            getter._is_rdf_property = True
            getter._is_relationship = True
            getter._relationship_type = "one_to_many"
            getter._target_class = target_class
            return property(getter, setter)
        return decorator

    # ------------------------------------------------------------------
    # Type conversion helpers
    # ------------------------------------------------------------------

    def _python_to_literal(self, value: Any) -> Literal:
        """Convert a Python value to an RDF Literal with the appropriate datatype."""
        if isinstance(value, bool):
            return Literal(value, datatype=XSD.boolean)
        elif isinstance(value, int):
            return Literal(value, datatype=XSD.integer)
        elif isinstance(value, float):
            return Literal(value, datatype=XSD.double)
        elif isinstance(value, datetime.datetime):
            return Literal(value.isoformat(), datatype=XSD.dateTime)
        elif isinstance(value, datetime.date):
            return Literal(value.isoformat(), datatype=XSD.date)
        else:
            return Literal(value)

    def _literal_to_python(self, literal: Literal) -> Any:
        """Convert an RDF Literal to the corresponding Python value."""
        if literal is None:
            return None
        dt = literal.datatype
        val = str(literal)
        if dt == XSD.boolean:
            return val.lower() in ("true", "1")
        elif dt == XSD.integer:
            return int(val)
        elif dt == XSD.double:
            return float(val)
        elif dt == XSD.dateTime:
            return datetime.datetime.fromisoformat(val)
        elif dt == XSD.date:
            return datetime.date.fromisoformat(val)
        return val

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_rdf(self, obj: Any, base_uri: Optional[str] = None, visited: Optional[set[Any]] = None) -> Graph:
        """
        Serialize a Python object into an RDF graph.

        Parameters
        ----------
        obj : Any
            The object to serialize. Must have a ``uri`` attribute.
        base_uri : str, optional
            Fallback URI if the object has no ``uri`` attribute.
        visited : set, optional
            Internal set used to prevent infinite recursion on circular references.

        Returns
        -------
        Graph
            An rdflib Graph containing the serialized triples.
        """
        if visited is None:
            visited = set()

        graph = Graph()
        uri_val: str = obj.uri if hasattr(obj, "uri") else cast(str, base_uri)
        subject = URIRef(uri_val)

        if subject in visited:
            graph.add((subject, RDF.type, obj._rdf_type_uri))
            return graph

        visited.add(subject)
        graph.add((subject, RDF.type, obj._rdf_type_uri))

        for attr in dir(obj):
            val = getattr(obj, attr)
            prop = getattr(type(obj), attr, None)
            if not isinstance(prop, property):
                continue
            fget: Any = prop.fget
            if fget is None or not getattr(fget, "_is_rdf_property", False):
                continue
            pred = fget._rdf_predicate
            if getattr(fget, "_is_relationship", False):
                if fget._relationship_type == "one_to_one" and val:
                    graph.add((subject, pred, URIRef(val.uri)))
                    graph += self.to_rdf(val, visited=visited)
                elif fget._relationship_type == "one_to_many" and isinstance(val, list):
                    for item in val:
                        graph.add((subject, pred, URIRef(item.uri)))
                        graph += self.to_rdf(item, visited=visited)
            else:
                if val is not None:
                    graph.add((subject, pred, self._python_to_literal(val)))

        return graph

    def to_rdf_many(self, objs: list) -> Graph:
        """
        Serialize a list of objects into a single RDF graph.

        Parameters
        ----------
        objs : list
            List of objects to serialize.

        Returns
        -------
        Graph
            An rdflib Graph containing all serialized triples.
        """
        graph = Graph()
        visited: set = set()
        for obj in objs:
            graph += self.to_rdf(obj, visited=visited)
        return graph

    def from_rdf(self, graph: Graph, cls: Type[Any], subject_uri: str, visited: Optional[dict[Any, Any]] = None) -> Any:
        """
        Deserialize an RDF graph back into a Python object.

        Parameters
        ----------
        graph : Graph
            The RDF graph containing the data.
        cls : Type
            The target class to instantiate.
        subject_uri : str
            The URI of the subject to deserialize.
        visited : dict, optional
            Internal cache used to handle circular references.

        Returns
        -------
        Any
            An instance of ``cls`` populated with data from the graph.
        """
        if visited is None:
            visited = {}

        subject = URIRef(subject_uri)

        if subject in visited:
            return visited[subject]

        instance: Any = object.__new__(cls)
        instance.uri = subject
        visited[subject] = instance

        for attr in dir(cls):
            prop = getattr(cls, attr, None)
            if not isinstance(prop, property):
                continue
            fget: Any = prop.fget
            if fget is None or not getattr(fget, "_is_rdf_property", False):
                continue
            pred = fget._rdf_predicate
            if getattr(fget, "_is_relationship", False):
                target_cls = fget._target_class()
                if fget._relationship_type == "one_to_one":
                    obj_ref = graph.value(subject, pred)
                    if obj_ref:
                        setattr(instance, attr, self.from_rdf(graph, target_cls, str(obj_ref), visited))
                elif fget._relationship_type == "one_to_many":
                    objs = [
                        self.from_rdf(graph, target_cls, str(obj_ref), visited)
                        for obj_ref in graph.objects(subject, pred)
                    ]
                    setattr(instance, attr, objs)
            else:
                val = graph.value(subject, pred)
                setattr(instance, attr, self._literal_to_python(val))

        return instance

    # ------------------------------------------------------------------
    # SHACL
    # ------------------------------------------------------------------

    def to_shacl(self, cls: Type) -> Graph:
        """
        Generate a SHACL shapes graph from a mapped class.

        Parameters
        ----------
        cls : Type
            A class decorated with ``@rdf_entity``.

        Returns
        -------
        Graph
            An rdflib Graph containing the SHACL NodeShape.
        """
        import inspect as _inspect

        shape_graph = Graph()
        SH = Namespace("http://www.w3.org/ns/shacl#")
        ns_ex = Namespace("http://example.org/shape/")

        shape_uri = ns_ex[f"{cls.__name__}Shape"]
        shape_graph.add((shape_uri, RDF.type, SH.NodeShape))
        shape_graph.add((shape_uri, SH.targetClass, cls._rdf_type_uri))

        init_type_hints: dict[str, Any] = {}
        try:
            init_type_hints = dict(_inspect.signature(cls.__init__).parameters)
        except Exception:
            pass

        for attr in dir(cls):
            prop = getattr(cls, attr, None)
            if not isinstance(prop, property):
                continue
            fget: Any = prop.fget
            if fget is None or not getattr(fget, "_is_rdf_property", False):
                continue
            min_count = getattr(fget, "_min_count", 0)
            max_count = getattr(fget, "_max_count", 1)
            pred = fget._rdf_predicate

            prop_bnode = BNode()
            shape_graph.add((shape_uri, SH.property, prop_bnode))
            shape_graph.add((prop_bnode, SH.path, pred))

            tipo = XSD.string
            if attr in init_type_hints:
                ann = init_type_hints[attr].annotation
                if ann == int:
                    tipo = XSD.integer
                elif ann == float:
                    tipo = XSD.double
                elif ann == bool:
                    tipo = XSD.boolean
                elif ann == datetime.datetime:
                    tipo = XSD.dateTime

            shape_graph.add((prop_bnode, SH.datatype, tipo))
            shape_graph.add((prop_bnode, SH.minCount, Literal(min_count)))
            shape_graph.add((prop_bnode, SH.maxCount, Literal(max_count)))

        return shape_graph

    def validate(
        self,
        data_graph: Graph,
        shacl_graph: Optional[Graph] = None,
        entity_class: Optional[Type[Any]] = None,
        **kwargs: Any,
    ) -> tuple[bool, Graph, str]:
        """
        Validate an RDF graph against SHACL constraints.

        Parameters
        ----------
        data_graph : Graph
            The RDF graph to validate.
        shacl_graph : Graph, optional
            A SHACL shapes graph. If not provided, one is generated from ``entity_class``.
        entity_class : Type, optional
            The mapped class used to auto-generate the SHACL graph.

        Returns
        -------
        tuple
            ``(conforms, results_graph, results_text)``
        """
        if shacl_graph is None:
            if entity_class is None:
                raise ValueError("Provide either shacl_graph or entity_class.")
            shacl_graph = self.to_shacl(entity_class)

        return validate(
            data_graph=data_graph,
            shacl_graph=shacl_graph,
            inference=kwargs.get("inference", "rdfs"),
            abort_on_first=kwargs.get("abort_on_first", False),
            meta_shacl=kwargs.get("meta_shacl", False),
            advanced=kwargs.get("advanced", True),
            debug=kwargs.get("debug", False),
        )
