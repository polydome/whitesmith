from operator import attrgetter
from typing import Callable

from readchar import key

from inventory import Inventory
from item_display import item_to_string
from list_view import ListView
from metal import Metal
from product import Product
from view import View, KeyListener


class ItemInspectView:
    def render(self, item) -> str:
        if isinstance(item, Metal):
            return "%s:\n\tTrudność: %d\n\tRzadkość: %d" % (item_to_string(item, type_tag=True), item.difficulty, item.rarity)
        elif isinstance(item, Product):
            return "%s:\n\tOcena: %d" % (item_to_string(item, type_tag=True), item.rating)
        else:
            return ""


class InventoryView(View, KeyListener):
    items_list_view: ListView
    on_change: Callable
    inventory: Inventory
    item_inspect_view: ItemInspectView = ItemInspectView()

    def __init__(self, on_change, inventory: Inventory):
        self.on_change = on_change
        self.inventory = inventory
        self.items_list_view = ListView([])

    def render(self) -> str:
        records = sorted(list(self.inventory.get_records().values()), key=attrgetter("count"), reverse=True)
        self.items_list_view.items = ["%dx %s" % (record.count, item_to_string(record.item, type_tag=True)) for record in records]
        pos = self.items_list_view.pos
        if pos < len(self.items_list_view.items):
            item = records[pos].item
        else:
            item = None
        return self.items_list_view.render() + "\n\n" + self.item_inspect_view.render(item)

    def on_key(self, k: key):
        if k == key.UP:
            self.items_list_view.up()
        elif k == key.DOWN:
            self.items_list_view.down()
        self.on_change()
