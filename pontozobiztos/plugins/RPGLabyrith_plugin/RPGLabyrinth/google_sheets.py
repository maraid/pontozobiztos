from __future__ import print_function
from typing import List
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import models
import re


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

LIGHT_BROWN = {'red': 0.92156863, 'green': 0.827451, 'blue': 0.6745098}
BROWN = {'red': 0.52156863, 'green': 0.427451, 'blue': 0.2745098}
LIGHT_GREEN = {'red': 0.80784315, 'green': 0.99607843, 'blue': 0.69411767}
GREEN = {'red': 0.40784315, 'green': 0.59607843, 'blue': 0.29411767}
PURPLE = {'red': 0.80784315, 'green': 0.29607843, 'blue': 0.69411767}

SPACER_PX = 5
ROOM_PX = 45


DOOR_BORDER = {
    'north': 'top',
    'east': 'right',
    'south': 'bottom',
    'west': 'left',
}

BORDER_DOOR = {value: key for key, value in DOOR_BORDER.items()}


class Sheet:
    def __init__(self, service, spreadsheet_id, sheet_name=None):
        self.service = service
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name

        self.index = None
        self.title = None
        self.sheet_id = None
        self.row_count = None
        self.column_count = None
        # self.row_pixelsizes = None
        # self.column_pixelsizes = None
        self.grid = None
        self.data = None
        self.fetch()

    def fetch(self):
        result = self.service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id,
            ranges=[f'{self.sheet_name}!A:ZZ'],
            includeGridData=True).execute()
        try:
            sheet = result.get('sheets', [])[0]
        except IndexError:
            raise ValueError('No sheet found')
        # print(sheet)
        self.index = sheet['properties']['index']
        self.title = sheet['properties']['title']
        self.sheet_id = sheet['properties']['sheetId']
        self.row_count = sheet['properties']['gridProperties']['rowCount']
        self.column_count = sheet['properties']['gridProperties']['columnCount']
        # self.row_pixelsizes = [x['pixelSize'] for x in sheet['data']['rowMetadata']]
        # self.column_pixelsizes = [x['pixelSize'] for x in sheet['data']['columnMetadata']]
        self.grid = [[{} for _ in range(self.column_count)] for _ in range(self.row_count)]
        self.data = sheet['data'][0]
        for i, row in enumerate(self.data['rowData']):
            if not row:
                continue
            for j, cell in enumerate(row['values']):
                if not cell:
                    continue

                try:
                    self.grid[i][j]['value'] = cell['effectiveValue']['stringValue']
                except KeyError:
                    try:
                        self.grid[i][j]['value'] = int(cell['effectiveValue']['numberValue'])
                    except KeyError:
                        self.grid[i][j]['value'] = None

                self.grid[i][j]['bg_color'] = {'red': 1, 'green': 1, 'blue': 1}
                self.grid[i][j]['borders'] = {}

                try:
                    effective_format = cell['effectiveFormat']
                except KeyError:
                    continue

                try:
                    self.grid[i][j]['bg_color'] = cell['effectiveFormat']['backgroundColor']
                except KeyError:
                    pass

                pairs = [
                    ('north', 'top'),
                    ('east', 'right'),
                    ('south', 'bottom'),
                    ('west', 'left'),
                ]

                for x, y in pairs:
                    try:
                        self.grid[i][j]['borders'][x] = {
                            'color': effective_format['borders'][y]['color'],
                            'width': effective_format['borders'][y]['width']
                        }
                    except KeyError:
                        pass

    def get_cell_data(self, row, column):
        return self.data['rowData'][row]['values'][column]

    def get_map_rules(self):
        row_index = 0
        rule_set = {}
        while cell := self.grid[row_index][0]:
            if self.grid[row_index][1]['value'] is not None:
                rule_set[cell['value']] = self.grid[row_index][1]['value']
            else:
                rule_set[cell['value']] = self.grid[row_index][1]['bg_color']
            row_index += 1
        return rule_set

    def get_cell_by_index(self, x, y):
        pass

    def create_new(self, map_json):
        body = {'requests': [{
            'addSheet': {
                'properties': {
                    'title': map_json['name'],
                    'gridProperties': {
                        'rowCount': map_json['row_count'],
                        'columnCount': map_json['column_count']
                    }
                }
            }
        }]}
        try:
            response = self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body).execute()
            self.sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
        except HttpError:
            self.fetch_id(map_json['name'])

    def set_dimension_width_at_indeces(self, dim: str, indeces: List[int], width: int):
        assert dim in ('COLUMNS', 'ROWS')

        requests = []
        for i in indeces:
            requests.append(
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": self.sheet_id,
                            "dimension": dim,
                            "startIndex": i,
                            "endIndex": i + 1
                        },
                        "properties": {
                            "pixelSize": width
                        },
                        "fields": "pixelSize"
                    }
                })
        body = {'requests': requests}
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=body).execute()

    def color_single_cell(self, row, column, color):
        cell_data = self.get_cell_data(row, column)['userEnteredFormat']
        cell_data['backgroundColor'] = color
        print(cell_data)
        # cell_data['']
        body = {'requests': [
            {
                'updateCells': {
                    'rows': [
                        {'values': [{'userEnteredFormat': cell_data}]}],
                    'fields': 'userEnteredFormat',
                    'start': {
                        'sheetId': self.sheet_id,
                        'rowIndex': row,
                        'columnIndex': column
                    }
                }
            }
        ]}
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=body).execute()

    def draw_player(self, player: models.Player):
        self.color_single_cell(player.current_room.row * 2,
                               player.current_room.column * 2,
                               PURPLE)

    @staticmethod
    def _door_to_border(door: models.Door, blocked_color):
        if not door.is_blocked:
            this_x = door.connects_to_room.row
            this_y = door.connects_to_room.column
            other_x = door.connects_to_door.connects_to_room.row
            other_y = door.connects_to_door.connects_to_room.column
            is_adjecent = (abs(this_x - other_x) + abs(this_y - other_y)) == 1
            if is_adjecent:
                return None
            else:
                door_location = door.connects_to_room.get_door_location(door)
                border_location = DOOR_BORDER.get(door_location)
                return {border_location: {
                    'style': 'DOTTED',
                    'color': door.render_color
                }}
        else:
            door_location = door.connects_to_room.get_door_location(door)
            border_location = DOOR_BORDER.get(door_location)
            return {border_location: {
                'style': 'SOLID_THICK',
                'color': blocked_color
            }}

    def _room_to_borders(self, room, blocked_color):
        ret_dct = {}
        for key in room.doors:
            if (border := self._door_to_border(room.doors[key], blocked_color)) is not None:
                ret_dct.update(border)
        return ret_dct

    def draw_map(self, map_: models.Map, player: models.Player, ruleset: dict, all_lit=False,
                 row_offset: int = 0, column_offset: int = 0):
        self.set_dimension_width_at_indeces(
            'ROWS',
            [x + row_offset for x in range(1, map_.row_count*2-1, 2)],
            SPACER_PX
        )
        self.set_dimension_width_at_indeces(
            'ROWS',
            [x + row_offset for x in range(0, map_.row_count*2-1, 2)],
            ROOM_PX
        )
        self.set_dimension_width_at_indeces(
            'COLUMNS',
            [y + column_offset for y in range(1, map_.column_count*2-1, 2)],
            SPACER_PX
        )
        self.set_dimension_width_at_indeces(
            'COLUMNS',
            [y + column_offset for y in range(0, map_.column_count*2-1, 2)],
            ROOM_PX
        )

        requests = []
        for i, row in enumerate(map_.rooms):
            for j, room in enumerate(row):
                actual_cell_x = row_offset + i + room.row
                actual_cell_y = column_offset + j + room.column

                if player.current_room == room:
                    color = PURPLE
                else:
                    color = ruleset['dark_room_color'] if not all_lit and not room.is_lit else ruleset[
                        'light_room_color']

                requests.append(
                    {
                        'updateCells': {
                            'rows': [
                                {'values': [{'userEnteredFormat': {
                                    'backgroundColor': color,
                                    'borders': self._room_to_borders(room, ruleset['blocked_door_color'])
                                }}]}],
                            'fields': 'userEnteredFormat',
                            'start': {
                                'sheetId': self.sheet_id,
                                # i represent the number of vertical spacers from the beginning
                                'rowIndex': actual_cell_x,
                                # j represent the number of horizontal spacers from the beginning
                                'columnIndex': actual_cell_y
                            }
                        }
                    }
                )
        body = {'requests': requests}
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=body).execute()

    @staticmethod
    def convert_cell_notation_to_index(notation: str):
        if match := re.search(r'([A-Z]+)([1-9]+)', notation):
            ch = match.group(1)[::-1]
            x = int(match.group(2))
        else:
            raise ValueError('Notation cannot be converted')
        y = [(ord(ch[i]) - 64) * 25**i for i in range(len(ch))]
        return x, sum(y)

    def read_map(self, row_offset, column_offset, ruleset, map_: models.Map):
        for i, row in enumerate(self.grid[row_offset:row_offset+(2*ruleset['row_count']-1):2]):
            for j, cell in enumerate(row[column_offset:column_offset+(2*ruleset['column_count']-1):2]):
                room = map_.rooms[i][j]
                if borders := cell.get('borders'):
                    for key, brd in borders.items():
                        if brd['color'] == ruleset['blocked_door_color']:
                            room.doors[key].connects_to_door = None
                            room.doors[key].save()
                room.save()
                #     tile.update({'_cls': 'Wall', 'is_intact': True})
                # else:
                #     value = cell.get('formattedValue', '')
                #     tile.update({'_cls': 'Room',
                #                  'is_start': value == 'S',
                #                  'is_finish': value == 'F'})
                # else:
                #     tile.update({'_cls': 'Wall', 'is_intact': False})
        map_.save()


class GoogleSheetsApiHelper:
    def __init__(self, spreadsheet_id):
        self.service = self.generate_service()
        self.mapdesign = Sheet(self.service, spreadsheet_id=spreadsheet_id, sheet_name='Testmap')
        self.output_sheet = Sheet(self.service, spreadsheet_id=spreadsheet_id, sheet_name='Output')
        self.map = None
        self.ruleset = None
        self.player = None

    def generate_editable(self, name, n, m):
        pass

    def set_player(self, player):
        self.player = player

    def generate_map(self):
        self.ruleset = self.mapdesign.get_map_rules()
        map_ = models.Map.generate_map(self.ruleset['map_name'],
                                       self.ruleset['row_count'],
                                       self.ruleset['column_count'])
        self.map = map_
        x, y = Sheet.convert_cell_notation_to_index(self.ruleset['map_start'])
        self.mapdesign.draw_map(map_, self.player, self.ruleset, True, x, y)

    def load_map(self):
        self.ruleset = self.mapdesign.get_map_rules()
        x, y = Sheet.convert_cell_notation_to_index(self.ruleset['map_start'])
        try:
            self.map = models.Map.objects(name=self.ruleset['map_name'])[0]
        except IndexError:
            self.generate_map()
        self.mapdesign.read_map(x, y, self.ruleset, self.map)

    def draw_map(self):
        self.output_sheet.draw_map(self.map, self.player, self.ruleset)

    def draw_player(self, player: models.Player):
        self.output_sheet.draw_player(player)

    def draw_empty_map(self):
        pass

    @staticmethod
    def generate_service():
        """Shows basic usage of the Sheets API.
        Prints values from a sample spreadsheet.
        """
        creds_ = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds_ = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds_ or not creds_.valid:
            if creds_ and creds_.expired and creds_.refresh_token:
                creds_.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds_ = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds_, token)
        return build('sheets', 'v4', credentials=creds_)

