"""A small JSON Schema validator, standard library only, so the checks run
anywhere Python does.

It covers the keywords this repo's schemas use: type, const, enum, required,
properties, additionalProperties, items, minItems, uniqueItems, minLength,
pattern, allOf, anyOf, not, if/then/else and local $ref ("#/$defs/...").
A schema that uses any other keyword is an error, so nothing is silently
skipped.
"""
import re

KNOWN = {
    "$schema", "$id", "$defs", "$ref", "title", "description",
    "type", "const", "enum", "required", "properties", "additionalProperties",
    "items", "minItems", "uniqueItems", "minLength", "pattern",
    "allOf", "anyOf", "not", "if", "then", "else",
}

TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


SUBSCHEMA = {"items", "additionalProperties", "not", "if", "then", "else"}
SUBSCHEMA_LISTS = {"allOf", "anyOf"}
SUBSCHEMA_MAPS = {"properties", "$defs"}


def unknown_keywords(schema):
    """Every keyword anywhere in schema that errors() doesn't support."""
    if not isinstance(schema, dict):
        return []
    found = sorted(set(schema) - KNOWN)
    for k, v in schema.items():
        if k in SUBSCHEMA:
            found += unknown_keywords(v)
        elif k in SUBSCHEMA_LISTS:
            for s in v:
                found += unknown_keywords(s)
        elif k in SUBSCHEMA_MAPS:
            for s in v.values():
                found += unknown_keywords(s)
    return sorted(set(found))


def _where(path):
    return "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in path) or "(top level)"


def _resolve(ref, root):
    if not ref.startswith("#/"):
        raise ValueError(f"only local $ref is supported, not {ref!r}")
    node = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def errors(value, schema, root=None, path=()):
    """Every way value breaks schema, as 'where: what' strings."""
    root = schema if root is None else root
    if schema is True or schema == {}:
        return []
    if schema is False:
        return [f"{_where(path)}: not allowed"]
    unknown = set(schema) - KNOWN
    if unknown:
        raise ValueError(f"schema keyword(s) not supported: {sorted(unknown)}")
    if "$ref" in schema:
        return errors(value, _resolve(schema["$ref"], root), root, path)
    out = []
    at = _where(path)
    t = schema.get("type")
    if t is not None:
        names = t if isinstance(t, list) else [t]
        if not any(TYPES[n](value) for n in names):
            return [f"{at}: should be {' or '.join(names)}"]
    if "const" in schema and value != schema["const"]:
        out.append(f"{at}: should be {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        out.append(f"{at}: should be one of {schema['enum']}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            out.append(f"{at}: too short")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            out.append(f"{at}: {value!r} doesn't match {schema['pattern']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            out.append(f"{at}: needs at least {schema['minItems']} item(s)")
        if schema.get("uniqueItems"):
            seen = []
            for v in value:
                if v in seen:
                    out.append(f"{at}: {v!r} is listed twice")
                seen.append(v)
        if "items" in schema:
            for i, v in enumerate(value):
                out += errors(v, schema["items"], root, path + (i,))
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for k in schema.get("required", []):
            if k not in value:
                out.append(f"{at}: missing {k!r}")
        for k, v in value.items():
            if k in props:
                out += errors(v, props[k], root, path + (k,))
            elif "additionalProperties" in schema:
                extra = schema["additionalProperties"]
                if extra is False:
                    out.append(f"{at}: unknown field {k!r}")
                else:
                    out += errors(v, extra, root, path + (k,))
    for sub in schema.get("allOf", []):
        out += errors(value, sub, root, path)
    if "anyOf" in schema and not any(not errors(value, s, root, path) for s in schema["anyOf"]):
        out.append(f"{at}: matches none of the allowed shapes")
    if "not" in schema and not errors(value, schema["not"], root, path):
        out.append(f"{at}: has a field or value that isn't allowed here")
    if "if" in schema:
        branch = "then" if not errors(value, schema["if"], root, path) else "else"
        if branch in schema:
            out += errors(value, schema[branch], root, path)
    return out
