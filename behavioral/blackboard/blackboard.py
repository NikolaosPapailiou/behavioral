import importlib
import json
import uuid
from typing import Dict, Set, Union

from pydantic import BaseModel, SerializeAsAny, TypeAdapter

SEPARATOR = "/"


class BlackBoardSerializableDict(BaseModel):
    data: Dict[str, Union[SerializeAsAny[BaseModel], int, float, str, bool]]


class KeyMetaData(object):
    """Stores the aggregated metadata for a key on the blackboard."""

    def __init__(self) -> None:
        self.read: Set[uuid.UUID] = set()
        self.write: Set[uuid.UUID] = set()
        self.exclusive: Set[uuid.UUID] = set()


def absolute_name(namespace: str, key: str, separator: str = None) -> str:
    """
    Generate the fully qualified key name from namespace and name arguments.

    **Examples**

    .. code-block:: python

        '/' + 'foo'  = '/foo'
        '/' + '/foo' = '/foo'
        '/foo' + 'bar' = '/foo/bar'
        '/foo/' + 'bar' = '/foo/bar'
        '/foo' + '/foo/bar' = '/foo/bar'
        '/foo' + '/bar' = '/bar'
        '/foo' + 'foo/bar' = '/foo/foo/bar'
    """
    namespace, separator = ensure_namespace_separator(
        namespace=namespace, separator=separator
    )
    if key.startswith(separator):
        return key
    key = key.strip(separator)
    return "{}{}".format(namespace, key)


def ensure_namespace_separator(
    namespace: str, separator: str = None
) -> tuple[str, str]:
    """Ensure the namespace format is correct and the separator is specified.
    The namespace should be a string that starts and ends with the separator.

    Args:
        namespace: The namespace to ensure has a separator.
        separator: The separator to use.

    Returns:
        A tuple of the namespace and separator.
    """
    if separator is None:
        separator = SEPARATOR
    if namespace is None:
        namespace = separator
    if not namespace.startswith(separator):
        namespace = separator + namespace
    if not namespace.endswith(separator):
        namespace = namespace + separator
    return namespace, separator


class BlackBoard(Dict):
    def __init__(self):
        self._bb = BlackBoardSerializableDict(data={})
        self._types: Dict[str, tuple[str, str]] = {}

    def remove_key(self, key: str, namespace: str = None):
        abs_key = absolute_name(
            namespace=namespace,
            key=key,
        )
        self._bb.data.pop(abs_key, None)
        self._types.pop(abs_key, None)

    def set_value(self, key: str, value, namespace: str = None):
        """Set a value in the blackboard.

        Args:
            key: The key to set the value for.
            value: The value to set.
            namespace: The namespace to set the value for.
        """
        if not isinstance(value, (BaseModel, int, float, str, bool)):
            raise ValueError(
                f"Value must be an instance of BaseModel or a primitive type, got {type(value)}"
            )
        abs_key = absolute_name(
            namespace=namespace,
            key=key,
        )
        self._bb.data[abs_key] = value
        if isinstance(value, BaseModel):
            t = type(value)
            self._types[abs_key] = (t.__module__, t.__qualname__)

    def get_value(self, key: str, namespace: str = None) -> BaseModel:
        """Get a value from the blackboard.

        Args:
            key: The key to get the value for.
            namespace: The namespace to get the value for.
        """
        abs_key = absolute_name(
            namespace=namespace,
            key=key,
        )
        return self._bb.data.get(abs_key, None)

    def keys(self, namespace: str = None):
        """Get all keys in the blackboard.

        Args:
            namespace: The namespace to get the keys for.
        """
        namespace, _ = ensure_namespace_separator(namespace=namespace)
        return [
            k.removeprefix(namespace)
            for k in self._bb.data.keys()
            if k.startswith(namespace)
        ]

    def to_dict(self, namespace: str = None) -> Dict:
        """Get a dictionary representation of the blackboard.

        Args:
            namespace: The namespace to get the dictionary for.
        """
        namespace, _ = ensure_namespace_separator(namespace=namespace)
        ret = {}
        for k, v in self._bb.data.items():
            if k.startswith(namespace):
                ret[k.removeprefix(namespace)] = v
        return ret

    def debug_json(self, namespace: str = None) -> Dict:
        def add_val(d: Dict, key_parts, value):
            k = key_parts.pop(0)
            if len(key_parts) == 0:
                d[k] = json.loads(value.model_dump_json())
                return

            new_d = {}
            if k in d:
                new_d = d[k]
            else:
                d[k] = new_d
            add_val(new_d, key_parts, value)

        namespace, separator = ensure_namespace_separator(namespace=namespace)
        ret = {}
        for k, v in self._bb.data.items():
            key = k
            if k.startswith(namespace):
                key = key.removeprefix(namespace)
            add_val(ret, key.split(separator), v)
        return json.dumps(ret)

    def to_json(self) -> tuple[str, str]:
        """Serialize the blackboard data to a JSON string."""
        return json.dumps(self._types), self._bb.model_dump_json()

    def from_json(self, types, data: str) -> "BlackBoard":
        """Deserialize a JSON representation to populate the blackboard."""
        self._types = json.loads(types)
        load_dict = json.loads(data)
        for k, v in load_dict["data"].items():
            if isinstance(v, Dict):
                module, name = self._types[k]
                type_adapter = TypeAdapter(
                    getattr(importlib.import_module(module), name)
                )
                self._bb.data[k] = type_adapter.validate_python(v)
            else:
                self._bb.data[k] = v
        return self
