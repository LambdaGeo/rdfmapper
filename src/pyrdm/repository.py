from __future__ import annotations

import re
from typing import Any, cast

from rdflib import Graph


class RDFRepository:
    """
    A dynamic query repository for RDF graphs, inspired by Spring Data JPA.

    Provides a fluent API for querying mapped entities using SPARQL under the
    hood, without requiring the caller to write SPARQL manually.

    Parameters
    ----------
    mapper : PyRDM
        The PyRDM instance used for deserialization.
    graph : Graph
        The RDF graph to query against.
    entity_class : type
        The mapped entity class to query.

    Examples
    --------
    >>> repo = RDFRepository(mapper, graph, Person)
    >>> repo.find_by_name(name="Ana")
    >>> repo.count_by_name(name="Ana")
    >>> repo.group_by_count(Person, "city", order="DESC")
    """

    def __init__(self, mapper, graph: Graph, entity_class: type) -> None:
        self.mapper = mapper
        self.graph = graph
        self.entity_class = entity_class

    # ------------------------------------------------------------------
    # Dynamic method resolution
    # ------------------------------------------------------------------

    def __getattr__(self, name: str):
        """
        Intercept attribute access to resolve dynamic query methods.

        Supports the following naming conventions:

        - ``find_by_<field>(**kwargs)``
        - ``find_by_<field>_like(**kwargs)``
        - ``find_by_<field>_and_<field>(**kwargs)``
        - ``count_by_<field>(**kwargs)``

        Parameters
        ----------
        name : str
            The method name to resolve.

        Raises
        ------
        AttributeError
            If the name does not match any supported convention.
        """
        if name.startswith("count_by_"):
            fields = name[len("count_by_"):].split("_and_")

            def counter(**kwargs: Any) -> int:
                return self._count_by(fields, kwargs)

            return counter

        match = re.match(r"^find_by_(.+)$", name)
        if match:
            fields = match.group(1).split("_and_")

            def finder(**kwargs: Any) -> list[Any]:
                limit = kwargs.pop("limit", None)
                offset = kwargs.pop("offset", None)
                return self._find_by(
                    fields,
                    kwargs,
                    like="_like" in name,
                    limit=limit,
                    offset=offset,
                )

            return finder

        raise AttributeError(
            f"'{self.__class__.__name__}' has no attribute '{name}'"
        )

    # ------------------------------------------------------------------
    # Internal query builders
    # ------------------------------------------------------------------

    def _find_by(
        self,
        fields: list[str],
        values: dict[str, Any],
        like: bool = False,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Any]:
        """
        Execute a SPARQL SELECT query filtering by one or more fields.

        Parameters
        ----------
        fields : list of str
            Field names to filter on.
        values : dict
            Mapping of field name to filter value.
        like : bool, optional
            If True, use regex matching instead of exact match, by default False.
        limit : int, optional
            Maximum number of results to return.
        offset : int, optional
            Number of results to skip.

        Returns
        -------
        list
            Deserialized entity instances matching the query.

        Raises
        ------
        ValueError
            If a required field value is missing.
        """
        cls: Any = self.entity_class
        conditions: list[str] = []

        for field in fields:
            field_name = field.replace("_like", "")
            if field_name not in values:
                raise ValueError(f"Missing value for field '{field_name}'")
            value = values[field_name]
            prop = getattr(cls, field_name)
            fget: Any = prop.fget
            pred = fget._rdf_predicate

            if getattr(fget, "_is_relationship", False):
                conditions.append(f"?s <{pred}> <{value}> .")
            else:
                value_var = f"?v_{field_name}"
                conditions.append(f"?s <{pred}> {value_var} .")
                if "_like" in field:
                    conditions.append(
                        f'FILTER regex({value_var}, "{value}", "i")'
                    )
                else:
                    conditions.append(f'FILTER ({value_var} = "{value}")')

        rdf_type = cls._rdf_type_uri
        where_clause = "\n            ".join(conditions)
        query = (
            "SELECT ?s WHERE {\n"
            f"    ?s a <{rdf_type}> .\n"
            f"    {where_clause}\n"
            "}"
        )
        if limit is not None:
            query += f"\nLIMIT {limit}"
        if offset is not None:
            query += f"\nOFFSET {offset}"

        return [
            self.mapper.from_rdf(self.graph, cls, str(cast(Any, row).s))
            for row in self.graph.query(query)
        ]

    def _count_by(self, fields: list[str], values: dict[str, Any]) -> int:
        """
        Execute a SPARQL COUNT query filtering by one or more fields.

        Parameters
        ----------
        fields : list of str
            Field names to filter on.
        values : dict
            Mapping of field name to filter value.

        Returns
        -------
        int
            Number of matching entities.

        Raises
        ------
        ValueError
            If a required field value is missing.
        """
        cls: Any = self.entity_class
        conditions: list[str] = []

        for field in fields:
            if field not in values:
                raise ValueError(f"Missing value for field '{field}'")
            value = values[field]
            prop = getattr(cls, field)
            fget: Any = prop.fget
            pred = fget._rdf_predicate
            if getattr(fget, "_is_relationship", False):
                conditions.append(f"?s <{pred}> <{value}> .")
            else:
                conditions.append(f'?s <{pred}> "{value}" .')

        rdf_type = cls._rdf_type_uri
        where_clause = "\n            ".join(conditions)
        query = (
            "SELECT (COUNT(?s) as ?count) WHERE {\n"
            f"    ?s a <{rdf_type}> .\n"
            f"    {where_clause}\n"
            "}"
        )
        for row in self.graph.query(query):
            return int(cast(Any, row)[0].toPython())
        return 0

    def group_by_count(
        self,
        cls: type,
        field: str,
        order: str = "DESC",
    ) -> list[dict[str, Any]]:
        """
        Execute a SPARQL GROUP BY query counting entities by a given field.

        Parameters
        ----------
        cls : type
            The mapped entity class to query.
        field : str
            The field name to group by.
        order : str, optional
            Sort order: ``"ASC"`` or ``"DESC"``, by default ``"DESC"``.

        Returns
        -------
        list of dict
            Each dict has the shape ``{"<field>": value, "count": int}``.

        Raises
        ------
        ValueError
            If ``field`` is not a valid ``rdf_property`` or ``order`` is invalid.

        Examples
        --------
        >>> repo.group_by_count(Person, "city", order="DESC")
        [{"city": "Sao Luis", "count": 42}, ...]
        """
        order = order.strip().upper()
        if order not in ("ASC", "DESC"):
            raise ValueError("order must be 'ASC' or 'DESC'")

        cls_any: Any = cls
        prop = getattr(cls_any, field, None)
        fget: Any = getattr(prop, "fget", None)
        if fget is None or not hasattr(fget, "_rdf_predicate"):
            raise ValueError(f"'{field}' is not a valid rdf_property")

        class_uri = cls_any._rdf_type_uri
        predicate = fget._rdf_predicate

        query = (
            f"SELECT ?{field} (COUNT(?s) AS ?count)\n"
            "WHERE {\n"
            f"    ?s a <{class_uri}> ;\n"
            f"       <{predicate}> ?{field} .\n"
            "}\n"
            f"GROUP BY ?{field}\n"
            f"ORDER BY {order}(?count)"
        )

        return [
            {field: str(cast(Any, row)[0]), "count": int(cast(Any, row)[1])}
            for row in self.graph.query(query)
        ]
