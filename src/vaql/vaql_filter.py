from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, override

from PySide6.QtCore import Qt, QMargins
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLineEdit

from vaql.linked_list import Node


class Op(Enum):
    AND = auto()
    OR = auto()


@dataclass
class VAQLFilter:
    negating: bool
    op: Op
    text: str


class VAQLFilterLineEdit(QLineEdit):
    COUNTER: int = 1

    def __init__(self, op: Op, negating: bool, filters_changed_callback: Callable[[], None], request_focus: bool):
        super().__init__()
        self.setAutoFillBackground(True)

        self.is_connected: bool = False
        self.handle_incantations = True
        self.handle_magic = False

        self.index = VAQLFilterLineEdit.COUNTER
        VAQLFilterLineEdit.COUNTER += 1

        self.op = op
        self.negating = negating
        self.node: Node | None = None
        self.filters_changed_callback = filters_changed_callback
        self.setContentsMargins(QMargins(0, 0, 0, 0))
        self.request_focus = request_focus

    def to_plain_filter(self) -> VAQLFilter:
        return VAQLFilter(
            negating = self.negating,
            op = self.op,
            text = self.text()
        )

    def link_to_node(self, node: Node) -> None:
        if self.node is None:
            self.node = node
        else:
            raise RuntimeError("No double linking")

    @override
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.setStyleSheet("background-color: pink;")

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.setStyleSheet("background-color: white;")

    def handle_and(self):
        if self.node.value.text().strip() != "":
            # find last node on this line and insert Op.AND LineEdit
            c_node = self.node
            while True:
                if c_node.next is None:
                    break

                if c_node.next.value.op == Op.AND:
                    break

                c_node = c_node.next

            c_node.append_inserting(VAQLFilterLineEdit(
                op = Op.AND, negating = False, filters_changed_callback = self.filters_changed_callback,
                request_focus = True
            ))
            self.filters_changed_callback()

    @override
    def keyPressEvent(self, event: QKeyEvent):
        """
        Clear filter input form when Escape is pressed. Otherwise, propagate
        key press events to the parent class.
        """

        key = event.key()
        match key:
            case Qt.Key.Key_Return:
                self.handle_and()

            case Qt.Key.Key_Up:
                counter = 0
                target_counter = 1
                prev_node = self.node.prev
                while prev_node.value is not None:
                    if prev_node.value.op == Op.AND:
                        counter += 1
                        if self.node.value.op == Op.OR:
                            # count to two
                            target_counter = 2
                        if counter == target_counter:
                            prev_node.value.setFocus()
                            return
                    prev_node = prev_node.prev
                if self.node.prev.value is not None:
                    self.node.prev.value.setFocus()

            case Qt.Key.Key_Down:
                next_node = self.node.next
                while next_node is not None:
                    if next_node.value.op == Op.AND:
                        next_node.value.setFocus()
                        return
                    next_node = next_node.next

            case Qt.Key.Key_Left:
                if self.node.prev is not None and event.modifiers() in [Qt.KeyboardModifier.ControlModifier,
                                                                        Qt.KeyboardModifier.ShiftModifier]:
                    if self.node.prev.value is not None:
                        self.node.prev.value.setFocus()
                else:
                    original_cursor_position = self.cursorPosition()
                    super().keyPressEvent(event)
                    if (original_cursor_position == self.cursorPosition() and self.node.prev is not None and
                            self.node.prev.value is not None):
                        # we came to end of the text; jump over to the next cell
                        self.node.prev.value.setFocus()

            case Qt.Key.Key_Right:
                assert self.node is not None
                if self.node.next is not None and event.modifiers() in [Qt.KeyboardModifier.ControlModifier,
                                                                        Qt.KeyboardModifier.ShiftModifier]:
                    self.node.next.value.setFocus()
                else:
                    original_cursor_position = self.cursorPosition()
                    super().keyPressEvent(event)
                    if original_cursor_position == self.cursorPosition() and self.node.next is not None:
                        # we came to end of the text; jump over to the next cell
                        self.node.next.value.setFocus()

            case Qt.Key.Key_Escape:
                self.clear()
                if self.node.prev.value is not None or self.node.next is not None:
                    if self.node.prev is not None and self.node.prev.value is not None:
                        self.node.prev.value.request_focus = True
                    elif self.node.next is not None and self.node.next.value is not None:
                        self.node.next.value.request_focus = True

                    if self.node.value.op == Op.AND and self.node.next is not None:
                        self.node.next.value.op = Op.AND
                        self.node.next.value.negating = self.node.value.negating

                    if self.node.next is not None:
                        self.node.next.value.request_focus = True
                    else:
                        self.node.prev.value.request_focus = True

                    self.node.delete()
                    self.filters_changed_callback()

            case Qt.Key.Key_Space:
                if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    # find nearest prev AND op and invert negation
                    n = self.node
                    while n is not None:
                        if n.value.op == Op.AND:
                            break
                        n = n.prev
                    if n is not None:
                        n.value.negating = not n.value.negating
                        self.node.value.request_focus = True
                        self.filters_changed_callback()
                    return

                if self.text().strip() != "":
                    if self.handle_magic or event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                        self.node.value.setText(self.node.value.text().strip())
                        self.node.append_inserting(VAQLFilterLineEdit(
                            op = Op.OR, negating = False, filters_changed_callback = self.filters_changed_callback,
                            request_focus = True
                        ))
                        self.filters_changed_callback()
                    else:
                        super().keyPressEvent(event)

            case Qt.Key.Key_Bar | Qt.Key.Key_Backslash:
                if (self.node.value.text().strip() != "" and
                        event.modifiers() == Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
                    self.node.append_inserting(VAQLFilterLineEdit(
                        op = Op.OR, negating = False, filters_changed_callback = self.filters_changed_callback,
                        request_focus = True
                    ))
                    self.filters_changed_callback()

            case _:
                super().keyPressEvent(event)
                # handle magic incantations
                line_lower = self.node.value.text().strip().lower()
                if line_lower.endswith(" and"):
                    self.handle_and()
                    self.node.value.setText(self.node.value.text()[:-4].strip())

                elif line_lower.endswith(" or"):
                    self.node.value.setText(self.node.value.text()[:-3].strip())
                    self.node.append_inserting(VAQLFilterLineEdit(
                        op = Op.OR, negating = False, filters_changed_callback = self.filters_changed_callback,
                        request_focus = True
                    ))
                    self.filters_changed_callback()
