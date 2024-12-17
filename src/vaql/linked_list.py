from typing import Protocol, Self, Callable


class LinkedLLNode(Protocol):
    def link_to_node(self, node) -> None: ...


class Node[T: LinkedLLNode]:
    def __init__(self, value: T | None, prev_node: Self | None = None, next_node: Self | None = None):
        self.value = value
        self.prev: Self | None = prev_node
        self.next: Self | None = next_node
        if value is not None:
            value.link_to_node(self)

    def append_inserting(self, value: T) -> Self:
        new_node = Node(value, prev_node = self, next_node = self.next)

        if self.next is not None:
            self.next.prev = new_node
        self.next = new_node
        return new_node

    def delete(self) -> None:
        if self.prev is not None:
            self.prev.next = self.next
        if self.next is not None:
            self.next.prev = self.prev

    def for_each_value(self, f: Callable[[T], None]) -> None:
        node = self
        while node is not None:
            f(node.value)
            node = node.next


class LinkedList[T]:
    def __init__(self):
        self.marker_node = Node[T](value = None, prev_node = None, next_node = None)
