"""
A Dict and Set implementation which always iterate in order.

`SortedDict` and `SortedSet` are red-black tree-based collections, which store
their keys according to their native Python sort order. This means iteration
(i.e. `for key in dictionary:`, or `for value in set:`) always produces the
keys in order.
"""

import collections

from crbtree._rbtree import ffi, lib

__all__ = ['SortedDict']


Item = collections.namedtuple('Item', ('key', 'value'))


class SortedDict(collections.MutableMapping):

    "A sorted dictionary, backed by a red-black tree."

    def __init__(self, *args, **kwargs):
        self._rbtree = lib.rb_tree_create(lib.rb_tree_node_compare)
        # This allows us to get the SortedDict Python object from a node
        # removal/dealloc callback.
        self._self_handle = ffi.new_handle(self)
        self._rbtree.info = self._self_handle
        # Track the FFI pointers to Items so they don't get garbage collected.
        self._handles = set()
        for key, value in kwargs.items():
            self[key] = value
        
        if args:
            try:
                if isinstance(args[0], list):
                    for item in args[0]:
                        self[item[0]] = item[1]
                elif isinstance(args[0], dict):
                    for key, value in args[0].items():
                        self[key] = value
                else:
                    raise ValueError
            except Exception:
                raise TypeError(f'Can\'t insert type {type(args[0])}')
            

    def __del__(self):
        lib.rb_tree_dealloc(self._rbtree, ffi.addressof(
            lib, 'rb_tree_node_dealloc_cb'))

    def __len__(self):
        return lib.rb_tree_size(self._rbtree)

    def _get(self, key):
        item = Item(key, None)  # Create item
        item_p = ffi.new_handle(item)  # Get its pointer
        result_p = lib.rb_tree_find(
            self._rbtree, item_p)  # Send to command to c
        if result_p == ffi.NULL:  # Compare to C NULL
            return (False, None)
        return (True, ffi.from_handle(result_p).value)

    def __contains__(self, key):
        return self._get(key)[0]

    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        item = Item(key, value)
        item_p = ffi.new_handle(item)
        self._handles.add(item_p)
        if not lib.rb_tree_insert(self._rbtree, item_p):
            raise RuntimeError(
                "Unexpected error inserting key {!r}".format(key))

    def __getitem__(self, key):
        found, item = self._get(key)
        if found:
            return item
        raise KeyError(key)

    def __delitem__(self, key):
        if key not in self:
            raise KeyError(key)
        item = Item(key, None)
        item_p = ffi.new_handle(item)
        removed = lib.rb_tree_remove_with_cb(
            self._rbtree, item_p, lib.rb_tree_node_was_removed)
        if not removed:
            raise RuntimeError(
                "Unexpected error removing key {!r}".format(key))

    def __iter__(self):
        for key, _ in self._iter():
            yield key

    def __eq__(self, other):
        return len(self) == len(other) and sorted_mapping_eq(self, other)

    def keys(self):
        for key, _ in self.items():
            yield key

    def values(self):
        for _, value in self.items():
            yield value

    def _iter(self):
        rb_iter = lib.rb_iter_create()
        try:
            item_p = lib.rb_iter_first(rb_iter, self._rbtree)
            while item_p != ffi.NULL:
                item = ffi.from_handle(item_p)
                yield (item.key, item.value)
                item_p = lib.rb_iter_next(rb_iter)
        finally:
            lib.rb_iter_dealloc(rb_iter)

    def items(self):
        return self._iter()

    def __repr__(self) -> str:
        st = '{'
        for key, value in self.items():
            st += f"'{key}': {value}, "
        st = st.strip(', ') + '}'
        return st


@ffi.def_extern()
def rb_tree_node_compare(rb_tree_p, rb_node_a, rb_node_b):
    a, b = ffi.from_handle(rb_node_a.value), ffi.from_handle(rb_node_b.value)
    if a.key == b.key:
        return 0
    if a.key < b.key:
        return -1
    return 1


@ffi.def_extern()
def rb_tree_node_was_removed(rb_tree_p, rb_node_p):
    ffi.from_handle(rb_tree_p.info)._handles.discard(rb_node_p.value)
    lib.rb_tree_node_dealloc_cb(rb_tree_p, rb_node_p)


def sorted_mapping_eq(map1, map2):
    return all(
        k1 == k2 and v1 == v2
        for (k1, v1), (k2, v2)
        in zip(map1.items(), map2.items()))
