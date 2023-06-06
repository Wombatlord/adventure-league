from __future__ import annotations
import random
from typing import Callable, Generator, NamedTuple

import colorama
from src.world.node import Node


class Tile:
    char: str
    def __init__(self, char) -> None:
        self.char = char
        self.level = None
    
    def accept(self, visitor):
        visitor.visit(self)
        
    def is_empty(self) -> bool:
        return self.char == " "
    
    def is_boundary(self) -> bool:
        return self.char in ["│","┘", "┌", "└", "┐", "─"]
            
    def __str__(self) -> str:
        return self.char

tiles = [
    [Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" ")],
    [Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" ")],
    [Tile("┌"), Tile("─"), Tile("┘"), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile("└"), Tile("─"), Tile("┐"), Tile(" "), Tile("┌"), Tile("─"), Tile("─"), Tile("┐"), Tile(" "), Tile(" ")],
    [Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile(" ")],
    [Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile(" ")],
    [Tile("└"), Tile("─"), Tile("┐"), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile("┌"), Tile("┘"), Tile(" "), Tile("└"), Tile("─"), Tile("─"), Tile("┘"), Tile(" "), Tile(" ")],
    [Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" ")],
    [Tile(" "), Tile(" "), Tile("└"), Tile("┐"), Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" ")],
    [Tile(" "), Tile(" "), Tile(" "), Tile("│"), Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile("│"), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" "), Tile(" ")],
]



class Voxel:
    tile: Tile
    location: Node
    grid: VoxelGrid | None
    
    def __init__(self, tile: Tile, loc: Node):
        self.tile = tile
        self.location = loc
        self.grid = None
        
    def set_grid(self, grid: VoxelGrid) -> Voxel:
        self.grid = grid
        return self
        
    def move_to(self, node: Node):
        self.location = node
        
    def get_adj(self) -> list[Voxel]:
        adj = self.location.get_adjacent()
        
        return [self.grid[n] for n in adj if self.grid[n] is not None]
    
    def get_adj_maybe(self, can_visit: VoxelPredicate) -> list[Voxel]:
        adj = self.location.get_adjacent()
        
        return [self.grid[n] for n in adj if can_visit(self.grid[n])]
        

VoxelPredicate = Callable[[Voxel], bool]
        
        
class VoxelGrid:
    def __init__(self, tile_grid: list[list[Tile]]):
        self.width, self.height = (len(tile_grid[0]), len(tile_grid))
        self._tiles = [
            [Voxel(tile, Node(x, y)).set_grid(self) for x, tile in enumerate(row)] 
            for y, row in enumerate(tile_grid)
        ]
        
    def __getitem__(self, index: Node) -> Node | None:
        if index in self:
            return self._tiles[index.y][index.x]
        return None
    
    def __contains__(self, node: Node) -> bool:
        if node.x < 0 or node.y < 0:
            return False
        
        if node.x >= self.width or node.y >= self.height:
            return False
        
        return True
    
    def __str__(self):
        lines = []
        for row in self._tiles:
            str_row = "".join([str(vox.tile) for vox in row])
            lines.append(str_row)
        
        return "\n".join(lines)
    
    def next_maybe(self, start: Node, can_visit: Callable[[Voxel], bool]) -> Generator[Voxel, None, None]:
        to_visit: set[Node] = set()
        visited: set[Node] = set()
        
        to_visit.add(start)
        
        while to_visit:
            current_node = to_visit.pop()
            current_voxel: Voxel | None = self[current_node]
            if current_voxel is None:
                return
            yield current_voxel
            visited.add(current_voxel.location)
            neighbours: list[Voxel] = current_voxel.get_adj()
            
            # valid destinations satisfy the condition, and have not been visited
            valid_destinations = {vox.location for vox in neighbours if can_visit(vox)}
            
            # add the valid next places to to_visit
            to_visit = (to_visit | valid_destinations) - visited
            # print(f"{len(visited)=}\t{len(to_visit)=}")

    def accept_conditionally(self, visitor: Visitor, start: Node):
        for vox in self.next_maybe(start, visitor.can_visit):
            visitor.visit(vox)
            
    def choose_start(self, start_condition: VoxelPredicate) -> Node | None:
        for row in self._tiles:
            for vox in row:
                if start_condition(vox):
                    return vox.location
                
        return None
    
    def accept(self, visitor: Visitor):
        while start := self.choose_start(visitor.can_start):
            visitor.start()
            self.accept_conditionally(visitor, start)
            visitor.stop()
            
        visitor.end()

    
class Visitor:
    def visit(self, vox: Voxel):
        raise NotImplementedError()
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def end(self):
        pass
    
    def can_start(self, vox: Voxel) -> bool:
        raise NotImplementedError()
    
    def can_visit(self, vox: Voxel) -> bool:
        raise NotImplementedError()
    
    
class Regionaire(Visitor):
    regions: list[list[Voxel]]
    _current_region: list[Voxel]
    _label = ord("a")
    region_map: dict[str, list[Voxel]]
    
    def __init__(self):
        self.regions = []
        self._current_region = []
        self.region_map = {}
        
    def start(self):
        self._current_region = []
        
    def stop(self):
        self.regions.append(self._current_region)
        # print(f"{len(self.regions)}")
        
    def visit(self, vox: Voxel):
        self._current_region.append(vox)
        vox.tile.char = chr(self._label + len(self.regions))
        
    def can_start(self, vox: Voxel) -> bool:
        return vox.tile.is_empty()
    
    def can_visit(self, vox: Voxel) -> bool:
        return vox.tile.is_empty()
    
    def end(self):
        for region in self.regions:
            if len(region):
                self.region_map[region[0].tile.char] = region
    
class Contour(NamedTuple):
    nodes: set[Node]
    heights: tuple[int, int]
    labels: tuple[str, str]
    
    @classmethod
    def from_start(cls, start: Node, labels: set[str]) -> Contour:
        nodes = {start}
        if len(labels) <= 1:
            raise ValueError("no labels adjacent")
            
        first = labels.pop()
        second = labels.pop()
        
        if start.y == 3 and start.x == 0:
            breakpoint()
        
        match first.isnumeric(), second.isnumeric():
            case (True, True):
                heights = (int(first), int(second))
            case (True, False):
                heights = (int(first), int(first) + 1)
            case (False, True):
                heights = (int(second) + 1, int(second))
            case _:
                heights = (1, 0)

        return cls(nodes=nodes, heights=heights, labels=(first, second))
    
    def other_height(self, height: int) -> int:
        if self.heights[0] == height:
            return self.heights[1]
        return self.heights[0]
    
    def include(self, node: Node):
        self.nodes.add(node)
        
    def has_traversed(self, node: Node) -> bool:
        return node in self.nodes
    
    def __eq__(self, other: Contour) -> bool:
        return bool(self.nodes & other.nodes)
    
    def __contains__(self, node: Node) -> bool:
        return node in self.nodes
    
class JonnyCash(Visitor):
    contours: list[Contour]
    _current_contour: Contour
    todo_list: dict[str, list[Voxel]]
    
    def __init__(self, regionnaire: Regionaire):
        self.contours = []
        self._current_contour = None
        self.todo_list = regionnaire.region_map
    
    def __contains__(self, node: Node) -> bool:
        for contour in self.contours:
            if node in contour:
                return True
        return False
        
    def start(self):
        self._current_contour = None
        
    def stop(self):
        self.contours.append(self._current_contour)
        
    def visit(self, vox: Voxel):
        if self._current_contour is None:
            labels: set[str] = {v.tile.char for v in vox.get_adj_maybe(lambda v: v and not v.tile.is_boundary())}
            try:
                self._current_contour = Contour.from_start(vox.location, labels)
            except ValueError:
                return
            
        self._set_both_sides()
        
            
    def _set_one_side(self, idx: int, label: str):        
        if region := self.todo_list.pop(label, None):
             for vox in region:
                vox.tile.char = f"{self._current_contour.heights[idx]}"
    
    def _set_both_sides(self):
        for idx, label in enumerate(self._current_contour.labels):
            if not label.isalpha():
                continue
            self._set_one_side(idx, label)
    
    def _resolve_the_line(self, grid):
        for contour in self.contours:
            if contour is None:
                continue
            for node in contour.nodes:
                contile = grid[node]
                contile.tile.char = "!"



    def can_start(self, vox: Voxel) -> bool:
        return self.can_visit(vox)
    
    def can_visit(self, vox: Voxel) -> bool:
        if not vox.tile.is_boundary():
            return False
        
        return vox.location not in self


def main():
    grid = VoxelGrid(tiles)
    print(grid)
    print()
    regionaire = Regionaire()

    grid.accept(regionaire)
    print(grid)
    print()
    jonny = JonnyCash(regionaire)
    
    try:
        grid.accept(jonny)

    except Exception as e:
        pass
    
    finally:
        jonny._resolve_the_line(grid)
        print(f"{grid}")

main()