# SHACL Validation

## Auto-generate shapes

pyrdm generates a SHACL NodeShape directly from the cardinality metadata
declared in `@rdf_property`:

```python
shacl_graph = mapper.to_shacl(Person)
print(shacl_graph.serialize(format="turtle"))
```

## Validate a graph

```python
conforms, results_graph, report_text = mapper.validate(
    graph, entity_class=Person
)
print("Conforms:", conforms)
print(report_text)
```

## Provide your own SHACL graph

```python
from rdflib import Graph

shacl = Graph()
shacl.parse("my-shapes.ttl", format="turtle")

conforms, _, report = mapper.validate(graph, shacl_graph=shacl)
```

## Cardinality constraints

```python
@mapper.rdf_property(FOAF.name, minCount=1, maxCount=1)
def name(self): pass
# → sh:minCount 1 ; sh:maxCount 1
```
