from dataclasses import dataclass
from enum import Enum
from operator import attrgetter
from typing import Callable, Optional

from readchar import key

from chance import calculate_forging_success_chance
from data.recipes import recipes
from forging import forge, get_effective_difficulty, produce, SCRAP
from inventory import Inventory, InventoryRecord
from item_display import item_to_string
from item_inspect_view import ItemInspectView
from list_view import ListView
from metal import Metal
from player import Player
from product import Product
from recipe import Recipe
from resources import Resources
from util import float_as_percent
from view import View, KeyListener


@dataclass
class ForgingChoice:
    recipe: Optional[Recipe]
    metal: Optional[InventoryRecord]


class ForgingStage(Enum):
    CHOOSING_RECIPE = 1
    CHOOSING_METAL = 2
    FORGING = 3


class ForgeView(View, KeyListener):
    loaded_recipes = recipes
    player: Player
    recipes_list_view = ListView([item_to_string(recipe) for recipe in loaded_recipes])
    metals_list_view = ListView([])
    on_change: Callable
    current_choice = ForgingChoice(None, None)
    current_stage = ForgingStage.CHOOSING_RECIPE
    last_product: Optional[Product] = None
    resources: Resources
    inspect_view = ItemInspectView()

    def __init__(self, on_change: Callable, player: Player, resources: Resources):
        self.player = player
        self.on_change = on_change
        self.resources = resources

    def can_forge(self) -> bool:
        return self.current_choice.metal and self.current_choice.recipe and self.current_choice.recipe.size <= self.current_choice.metal.count

    def render(self) -> str:
        stage_render = ""
        if self.current_stage == ForgingStage.CHOOSING_RECIPE:
            stage_render = self.render_choosing_recipe()
        elif self.current_stage == ForgingStage.CHOOSING_METAL:
            stage_render = self.render_choosing_metal()
        elif self.current_stage == ForgingStage.FORGING:
            stage_render = self.render_forging()
        return self.render_choice() + "\n\n" + stage_render

    def render_choosing_recipe(self) -> str:
        selected_item = self.loaded_recipes[self.recipes_list_view.pos]
        return "Wybierz przepis: \n\n" + self.recipes_list_view.render() + "\n\n" + self.inspect_view.render(selected_item)

    def render_choosing_metal(self) -> str:
        records = self.player.inventory.find_metals()
        selected_item = records[self.metals_list_view.pos].item if len(records) > 0 else None
        metal_records = self.player.inventory.find_metals()
        self.metals_list_view.items = ["%dx %s" % (record.count, item_to_string(record.item)) for record in metal_records]
        return "Wybierz metal: \n\n" + self.metals_list_view.render() + "\n\n" + self.inspect_view.render(selected_item)

    def render_forging(self):
        product_info = ""
        chance_info = "Wybierz przepis i metal..."

        if self.current_choice.metal and self.current_choice.recipe:
            difficulty = get_effective_difficulty(self.current_choice.metal.item, self.current_choice.recipe)
            chance = calculate_forging_success_chance(self.player.get_forging_level(), difficulty)
            chance_info = "Szansa na sukces: %s" % float_as_percent(chance)

        if self.last_product:
            product_info = "\n\n\tWytworzyłeś: %s!" % (item_to_string(self.last_product, embedded=True, verbose=True))

        return chance_info + product_info

    def render_choice(self) -> str:
        r = ""
        m = ""
        w = ""
        o = ""
        if self.current_choice.recipe:
            r = "Przepis: %s" % item_to_string(self.current_choice.recipe, embedded=True)
        if self.current_choice.metal:
            m = " + %s" % item_to_string(self.current_choice.metal.item, embedded=True)
        if self.current_choice.recipe and self.current_choice.metal:
            w = "\n\tMateriały: %d / %d" % (self.current_choice.metal.count, self.current_choice.recipe.size)
        if self.can_forge():
            o = "  OK!"
        return r + m + w + o

    def handle_confirm(self):
        if self.current_stage == ForgingStage.CHOOSING_RECIPE:
            self.current_choice.recipe = self.loaded_recipes[self.recipes_list_view.pos]
        elif self.current_stage == ForgingStage.CHOOSING_METAL:
            records = self.player.inventory.find_metals()
            if len(records) > 0:
                self.current_choice.metal = records[self.metals_list_view.pos]
        elif self.current_stage == ForgingStage.FORGING:
            self.attempt_forging()

    def attempt_forging(self):
        if self.can_forge():
            self.last_product = produce(self.player, self.resources, self.current_choice.recipe, self.current_choice.metal.item)
            difficulty = get_effective_difficulty(self.current_choice.metal.item, self.current_choice.recipe)
            if self.last_product is not SCRAP:
                self.player.on_forging_successful(difficulty)
            else:
                self.player.on_forging_failure(difficulty)

    def handle_up(self):
        if self.current_stage == ForgingStage.CHOOSING_RECIPE:
            self.recipes_list_view.up()
        elif self.current_stage == ForgingStage.CHOOSING_METAL:
            self.metals_list_view.up()

    def handle_down(self):
        if self.current_stage == ForgingStage.CHOOSING_RECIPE:
            self.recipes_list_view.down()
        elif self.current_stage == ForgingStage.CHOOSING_METAL:
            self.metals_list_view.down()

    def next_stage(self):
        if self.current_stage != ForgingStage.FORGING:
            self.current_stage = ForgingStage(self.current_stage.value + 1)

    def prev_stage(self):
        if self.current_stage != ForgingStage.CHOOSING_RECIPE:
            self.current_stage = ForgingStage(self.current_stage.value - 1)

    def on_key(self, k: key):
        if k == key.UP:
            self.handle_up()
        elif k == key.DOWN:
            self.handle_down()
        elif k == key.ENTER:
            self.handle_confirm()
        elif k == key.LEFT:
            self.prev_stage()
        elif k == key.RIGHT:
            self.next_stage()
        self.on_change()
