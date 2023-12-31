from typing import Any, Iterable, List
from abc import ABC, abstractmethod

class View(ABC):
    def __init__(self, min_cell_width: int = 5):
        self._min_cell_width: int = min_cell_width
        self._cell_widths: List[int] = []

    def _adjust_cell_size_at(self, at: int, content: Any):
        """ Adjust the cell size at a particular position to fit the length of a content. """
        if len(self._cell_widths) <= at:
            self._cell_widths += [self._min_cell_width] * (at - len(self._cell_widths) + 1)

        self._cell_widths[at] = max(len(str(content)), self._cell_widths[at])

    def _adjust_cell_sizes_to_fit(self, *content: Any):
        """ Adjust the cell sizes to fit according to the length of each stringified content. """
        if len(self._cell_widths) == 0:
            self._cell_widths = [self._min_cell_width] * len(content)

        for col, c in enumerate(content):
            self._cell_widths[col] = max(len(str(c)), self._cell_widths[col])
    
    def _format_row(self, items: List[Any], sep: str = "|"):
        """ 
            Formats a list of items to a row of formatted cells that are contained in a 
            fixed cell width, and are separated by a given separator. 
        """

        row = ""
        row += sep
        row += sep.join("{:>{}}".format(str(item), cell_width) for item, cell_width in zip(items, self._cell_widths)) 
        row += sep

        return row

    def _create_separator_line(self, joint: str = "+", line: str = "-"):
        return joint + joint.join(line * w for w in self._cell_widths) + joint
    
    @staticmethod
    def numbered_list(items_iter: Iterable[Any], start_at: int = 1, is_reversed: bool = False):
        """ 
            Turns a set of items into a string of numbered list. The numbering is sequential,
            but the starting number can be changed by setting a starting number on the second
            argument.

            Example Output
            --------------
            [1] Numbered List Item \n
            [2] Numbered List Item \n
            [3] Numbered List Item
        """
        # + 2 is to account for the char width of the brackets in the bullet
        items = list(items_iter)
        number_bullet_width = len(str(len(items) + 1)) + 2 
        numbered_list = []

        for i, item in enumerate(items):
            number_bullet = "[{}]".format(i + start_at)
            list_item = "{:>{}} {}".format(number_bullet, number_bullet_width, str(item))
            numbered_list.append(list_item)

        if is_reversed:
            numbered_list.reverse()

        return "\n".join(numbered_list)
    
    @abstractmethod
    def add_item(self):
        "Add an item to the view."
        pass

    @abstractmethod
    def render(self):
        """ Render the given view to the console. """
        pass 
