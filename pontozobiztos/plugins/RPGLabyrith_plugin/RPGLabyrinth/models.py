from __future__ import annotations
from typing import Dict, Tuple


import os
from mongoengine import connect, StringField, IntField, BooleanField,\
    ListField, ReferenceField, Document, ValidationError, EmbeddedDocument,\
    EmbeddedDocumentField, DictField

import google_api_helper

import dotenv
dotenv.load_dotenv()

connect('labyrinth',
        host=os.getenv('MONGO_HOST'),
        port=int(os.getenv('MONGO_PORT')))


# DIRECTIONS = {(-1, -1): 'northwest',
#               (-1,  0): 'north',
#               (-1,  1): 'northeast',
#               (0, -1):  'west',
#               (0,  0):  'center',
#               (0,  1):  'east',
#               (1, -1):  'southwest',
#               (1,  0):  'south',
#               (1,  1):  'southeast'}
#
# INVERSE_DIRECTIONS = {v: k for k, v in DIRECTIONS.items()}


class Item(Document):
    name = StringField(default='')
    description = StringField(default='')


class Door(Document):
    connects_to_room = ReferenceField('Room', default=None)
    connects_to_door = ReferenceField('self', default=None)
    requires_item = ReferenceField(Item)

    render_color = DictField()

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self) -> Dict:
        dct = {}
        if self.connects_to_room is not None:
            dct['connects_to_room'] = (self.connects_to_room.row,
                                       self.connects_to_room.column)
        else:
            dct['connects_to_room'] = None

        if self.connects_to_door is not None:
            dct['connects_to_door'] = (self.connects_to_door.connects_to_room.row,
                                       self.connects_to_door.connects_to_room.column,
                                       self.connects_to_door.connects_to_room.get_door_location(self.connects_to_door))
        else:
            dct['connects_to_door'] = None
        return dct

    @property
    def is_blocked(self) -> bool:
        return self.connects_to_door is None

    def go_through(self, player: Player):
        player.move(self.connects_to_door.connects_to_room)
        player.save()


class Room(Document):
    row: int = IntField()
    column: int = IntField()
    is_lit: bool = BooleanField(default=False)
    is_start: bool = BooleanField(default=False)
    is_finish: bool = BooleanField(default=False)
    inventory = ListField(ReferenceField(Item), default=[])

    class DoorsField(EmbeddedDocument):
        north: Door = ReferenceField(Door)
        east: Door = ReferenceField(Door)
        south: Door = ReferenceField(Door)
        west: Door = ReferenceField(Door)

    doors = EmbeddedDocumentField(DoorsField)

    def __repr__(self):
        return str(self.to_dict())

    @classmethod
    def create(cls, *args, **kwargs):
        room = cls(*args, **kwargs)
        room.save()

        room.doors = room.DoorsField()
        for key in room.doors:
            room.doors[key] = Door(connects_to_room=room)
            room.doors[key].save()
        room.save()
        return room

    def to_dict(self) -> Dict:
        return {'_cls': 'Room',
                'row': self.row,
                'column': self.column,
                'is_lit': self.is_lit,
                'is_start': self.is_start,
                'is_finish': self.is_finish,
                'inventory': [item.to_dict() for item in self.inventory],
                'doors': {k: self.doors[k].to_dict() for k in self.doors}}

    def get_door_location(self, door: Door) -> str:
        try:
            return [key for key in self.doors if self.doors[key] == door][0]
        except IndexError:
            raise ValueError(f'Door {door.to_dict} is not found in room {self.to_dict()}')


class Map(Document):
    name = StringField(primary_key=True)
    row_count = IntField(required=True)
    column_count = IntField(required=True)
    rooms = ListField(ListField(ReferenceField(Room)))

    def validate_data(self):
        return True

    @classmethod
    def load_map(cls, name: str) -> Map:
        try:
            map_ = cls.objects(pk=name)[0]
        except IndexError:
            raise KeyError('No items found with primary key: ' + name)

        if map_.validate_data():
            return map_
        else:
            raise ValidationError('Map data is corrupted: ' + name)

    # @classmethod
    # def from_dict(cls, dct):
    #     name = dct['name']
    #     row_count = dct['row_count']
    #     column_count = dct['column_count']
    #     tiles = []
    #     for row in dct['tiles']:
    #         tiles.append(obj_row := [])
    #         for cell in row:
    #             obj_row.append(Tile.create_tile(cell))
    #     return cls(name=name, row_count=row_count, column_count=column_count,
    #                tiles=tiles)

    @classmethod
    def generate_map(cls, name, n, m):
        map_ = cls(name=name, row_count=n, column_count=m)
        map_.rooms = [[Room.create(row=i, column=j) for j in range(m)] for i in range(n)]
        for r in range(n):
            for c in range(m):
                try:
                    map_.rooms[r][c].doors.east.connects_to_door = map_.rooms[r][c+1].doors.west
                    map_.rooms[r][c+1].doors.west.connects_to_door = map_.rooms[r][c].doors.east
                    map_.rooms[r][c].doors.east.save()
                    map_.rooms[r][c+1].doors.west.save()
                except IndexError:
                    pass

                try:
                    map_.rooms[r][c].doors.south.connects_to_door = map_.rooms[r+1][c].doors.north
                    map_.rooms[r+1][c].doors.north.connects_to_door = map_.rooms[r][c].doors.south
                    map_.rooms[r][c].doors.south.save()
                    map_.rooms[r+1][c].doors.north.save()
                except IndexError:
                    pass
        map_.save()
        return map_

    # def to_dict(self):
    #     dct = {
    #         '_cls': 'Map',
    #         'name': self.name,
    #         'row_count': self.row_count,
    #         'column_count': self.column_count,
    #         'tiles': [[t.to_dict() for t in row] for row in self.tiles]
    #     }
    #     return dct

    def iter_rooms(self):
        for row in self.rooms:
            yield from row

    def get_start_room(self) -> Room:
        try:
            start_room = [t for t in self.iter_rooms() if t.is_start][0]
        except IndexError:
            return self.rooms[0][0]
        return start_room

    # def get_surronding_walls(self, room: Room) -> Dict[str, WallBase]:
    #     surrounding_walls = {}
    #     for i in range(-1, 2):
    #         for j in range(-1, 2):
    #             try:
    #                 wall = self.tiles[room.row + i][room.column + j]
    #             except IndexError:
    #                 continue
    #             surrounding_walls.update(
    #                 {DIRECTIONS.get((i, j)): wall})
    #     del surrounding_walls['center']
    #     return surrounding_walls

    # def get_intact_walls(self, room: Room):
    #     surrounding_walls = self.get_surronding_walls(room)
    #     return {k: w for k, w in surrounding_walls.items() if not w.is_intact}
    #
    # def get_reachable_rooms(self, room: Room) -> Dict[str, Room]:
    #     intact_walls = self.get_intact_walls(room)
    #     reachable_rooms = {}
    #     for direction in intact_walls.keys():
    #         direction_coord = INVERSE_DIRECTIONS.get(direction)
    #         neighbour_room_r = room.row + 2 * direction_coord[0]
    #         neighbour_room_c = room.column + 2 * direction_coord[1]
    #         try:
    #             neighbour = self.tiles[neighbour_room_r][neighbour_room_c]
    #             reachable_rooms[direction] = neighbour
    #         except IndexError:
    #             pass
    #     return reachable_rooms

    # def light_room(self, room):
    #     room.is_lit = True
    #     for wall in self.get_surronding_walls(room).values():
    #         wall.is_lit = True
    #
    # def draw_ascii(self):
    #     ascii_chars = ''
    #     for i, tile in enumerate(self.iter_tiles()):
    #         ascii_chars += tile.get_ascii()
    #         if i % self.column_count == self.column_count-1:
    #             ascii_chars += '\n'
    #     return ascii_chars


class Character(Document):
    name = StringField(required=True)
    current_room: Room = ReferenceField(Room)

    meta = {'allow_inheritance': True}

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self) -> Dict:
        return {'_cls': 'Character',
                'name': self.name,
                'current_room': self.current_room.to_dict()}

    def move(self, new_room):
        self.current_room = new_room
        self.current_room.is_lit = True
        self.current_room.save()


class Player(Character):
    inventory = ListField(ReferenceField(Item))


class NPC(Character):
    pass


class QuestBase(Document):
    meta = {'allow_inheritance': True}


class FetchQuest(QuestBase):
    pass


if __name__ == '__main__':
    map_ = Map.generate_map('test', 10, 10)
    map_.save()
