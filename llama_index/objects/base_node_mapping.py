"""Base object types."""

import os
import pickle
from abc import abstractmethod
from typing import Any, Dict, Generic, Optional, Sequence, TypeVar

from llama_index.schema import BaseNode, MetadataMode, TextNode
from llama_index.storage.storage_context import DEFAULT_PERSIST_DIR
from llama_index.utils import concat_dirs

DEFAULT_PERSIST_FNAME = "object_node_mapping.pickle"

OT = TypeVar("OT")


class BaseObjectNodeMapping(Generic[OT]):
    """Base object node mapping."""

    @classmethod
    @abstractmethod
    def from_objects(
        cls, objs: Sequence[OT], *args: Any, **kwargs: Any
    ) -> "BaseObjectNodeMapping":
        """Initialize node mapping from a list of objects.

        Only needs to be specified if the node mapping
        needs to be initialized with a list of objects.

        """

    def validate_object(self, obj: OT) -> None:
        """Validate object."""

    def add_object(self, obj: OT) -> None:
        """Add object.

        Only needs to be specified if the node mapping
        needs to be initialized with a list of objects.

        """
        self.validate_object(obj)
        self._add_object(obj)

    @abstractmethod
    def _add_object(self, obj: OT) -> None:
        """Add object.

        Only needs to be specified if the node mapping
        needs to be initialized with a list of objects.

        """

    @abstractmethod
    def to_node(self, obj: OT) -> TextNode:
        """To node."""

    def to_nodes(self, objs: Sequence[OT]) -> Sequence[TextNode]:
        return [self.to_node(obj) for obj in objs]

    def from_node(self, node: BaseNode) -> OT:
        """From node."""
        obj = self._from_node(node)
        self.validate_object(obj)
        return obj

    @abstractmethod
    def _from_node(self, node: BaseNode) -> OT:
        """From node."""

    @abstractmethod
    def persist(
        self,
        persist_dir: str = DEFAULT_PERSIST_DIR,
        obj_node_mapping_fname: str = DEFAULT_PERSIST_FNAME,
    ) -> None:
        """Persist objs."""
        raise NotImplementedError(
            "This object node mapping does not support persist method."
        )

    @classmethod
    @abstractmethod
    def from_persist_dir(
        cls,
        persist_dir: str = DEFAULT_PERSIST_DIR,
        obj_node_mapping_fname: str = DEFAULT_PERSIST_FNAME,
    ) -> "BaseObjectNodeMapping":
        """Load from serialization."""
        raise NotImplementedError(
            "This object node mapping does not support from_persist_dir method."
        )


class SimpleObjectNodeMapping(BaseObjectNodeMapping[Any]):
    """General node mapping that works for any obj.

    More specifically, any object with a meaningful string representation.

    """

    def __init__(self, objs: Optional[Sequence[Any]] = None) -> None:
        objs = objs or []
        for obj in objs:
            self.validate_object(obj)
        self._objs = {hash(str(obj)): obj for obj in objs}

    @classmethod
    def from_objects(
        cls, objs: Sequence[Any], *args: Any, **kwargs: Any
    ) -> "BaseObjectNodeMapping":
        return cls(objs)

    @property
    def obj_node_mapping(self):
        return self._objs

    @obj_node_mapping.setter
    def obj_node_mapping(self, mapping: Dict[int, Any]):
        self._objs = mapping

    def _add_object(self, obj: Any) -> None:
        self._objs[hash(str(obj))] = obj

    def to_node(self, obj: Any) -> TextNode:
        return TextNode(text=str(obj))

    def _from_node(self, node: BaseNode) -> Any:
        return self._objs[hash(node.get_content(metadata_mode=MetadataMode.NONE))]

    def persist(
        self,
        persist_dir: str = DEFAULT_PERSIST_DIR,
        obj_node_mapping_fname: str = DEFAULT_PERSIST_FNAME,
    ) -> None:
        """Persist object node mapping.

        NOTE: This may fail depending on whether the object types are
        pickle-able.
        """
        if not os.path.exists(persist_dir):
            os.makedirs(persist_dir)
        obj_node_mapping_path = concat_dirs(persist_dir, obj_node_mapping_fname)
        try:
            with open(obj_node_mapping_path, "wb") as f:
                pickle.dump(self._objs, f)
        except pickle.PickleError as err:
            raise ValueError("Objs is not pickleable") from err

    @classmethod
    def from_persist_dir(
        cls,
        persist_dir: str = DEFAULT_PERSIST_DIR,
        obj_node_mapping_fname: str = DEFAULT_PERSIST_FNAME,
    ) -> "SimpleObjectNodeMapping":
        obj_node_mapping_path = concat_dirs(persist_dir, obj_node_mapping_fname)
        try:
            with open(obj_node_mapping_path, "rb") as f:
                objs = pickle.load(f)
        except pickle.PickleError as err:
            raise ValueError("Objs cannot be loaded.") from err

        simple_object_node_mapping = cls(None)
        simple_object_node_mapping.obj_node_mapping = objs
        return simple_object_node_mapping
