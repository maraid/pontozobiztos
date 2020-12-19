from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

LIGHT_BROWN = {'red': 0.92156863, 'green': 0.827451, 'blue': 0.6745098}
BROWN = {'red': 0.52156863, 'green': 0.427451, 'blue': 0.2745098}
LIGHT_GREEN = {'red': 0.80784315, 'green': 0.99607843, 'blue': 0.69411767}
GREEN = {'red': 0.40784315, 'green': 0.59607843, 'blue': 0.29411767}
PURPLE = {'red': 0.80784315, 'green': 0.29607843, 'blue': 0.69411767}

WALL_PX = 11
ROOM_PX = 25


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


def fetch_map_data(sheet_id, tab_name):
    # Call the Sheets API
    resource = service.spreadsheets()
    result = resource.get(spreadsheetId=sheet_id,
                          ranges=[f'{tab_name}!A:ZZ'],
                          includeGridData=True).execute()
    if not (sheet := result.get('sheets', [])):
        raise ValueError('No sheet found')
    sheet = sheet[0]

    map_ = {
        'name': sheet['data'][0]['rowData'][0]['values'][0]['formattedValue'],
        'row_count': sheet['properties']['gridProperties']['rowCount'],
        'column_count': sheet['properties']['gridProperties']['columnCount'],
        'tiles': []
    }

    for i, row in enumerate(sheet['data'][0]['rowData']):
        map_['tiles'].append(row_tiles := [])
        for j, cell in enumerate(row['values']):
            row_tiles.append(tile := {'row': i, 'column': j})
            if cell:
                if cell['effectiveFormat']['backgroundColor'] == LIGHT_BROWN:
                    tile.update({'_cls': 'Wall', 'is_intact': True})
                else:
                    value = cell.get('formattedValue', '')
                    tile.update({'_cls': 'Room',
                                 'is_start': value == 'S',
                                 'is_finish': value == 'F'})
            else:
                tile.update({'_cls': 'Wall', 'is_intact': False})
    return map_


def set_column_width(spreadsheet_id, sheet_id, indeces, width):
    requests = []
    for i in indeces:
        requests.append(
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
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
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body).execute()


def set_row_height(spreadsheet_id, sheet_id, indeces, height):
    requests = []
    for i in indeces:
        requests.append(
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": i,
                        "endIndex": i + 1
                    },
                    "properties": {
                        "pixelSize": height
                    },
                    "fields": "pixelSize"
                }
            })
    body = {'requests': requests}
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body).execute()


def color_rectangle(spreadsheet_id, sheet_id, map_json, color):
    body = {'requests': [
        {
            'updateCells': {
                'rows': [
                    {'values': [{'userEnteredFormat': {'backgroundColor': color}} for _ in row]}
                    for row in map_json['tiles']],
                'fields': 'userEnteredFormat',
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': map_json['row_count'],
                    'startColumnIndex': 0,
                    'endColumnIndex': map_json['column_count']}
            }
        }]}
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body).execute()


def color_single_cell(spreadsheet_id, sheet_id, row, column, color):
    body = {'requests': [
        {
            'updateCells': {
                'rows': [
                    {'values': [{'userEnteredFormat': {'backgroundColor': color}}]}],
                'fields': 'userEnteredFormat',
                'start': {
                    'sheetId': sheet_id,
                    'rowIndex': row,
                    'columnIndex': column
                }
            }
        }
    ]}
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body).execute()


def color_cells(spreadsheet_id, sheet_id, map_json):
    requests = []
    for row in map_json['tiles']:
        for cell in row:
            color = None
            if cell['_cls'] == 'HorizontalEdgeWall':
                if cell['is_intact']:
                    color = LIGHT_BROWN if cell['is_lit'] else BROWN
                else:
                    color = LIGHT_GREEN if cell['is_lit'] else GREEN
            if cell['_cls'] == 'Room':
                color = LIGHT_GREEN if cell['is_lit'] else GREEN
            requests.append(
                {
                    'updateCells': {
                        'rows': [
                            {'values': [{'userEnteredFormat': {'backgroundColor': color}}]}],
                        'fields': 'userEnteredFormat',
                        'start': {
                            'sheetId': sheet_id,
                            'rowIndex': cell['row'],
                            'columnIndex': cell['column']
                        }
                    }
                }
            )
    body = {'requests': requests}
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body).execute()


def set_dimensions(spreadsheet_id, sheet_id, map_json):
    set_column_width(spreadsheet_id, sheet_id, range(0, map_json['column_count'], 2), WALL_PX)
    set_column_width(spreadsheet_id, sheet_id, range(1, map_json['column_count'], 2), ROOM_PX)
    set_row_height(spreadsheet_id, sheet_id, range(0, map_json['row_count'], 2), WALL_PX)
    set_row_height(spreadsheet_id, sheet_id, range(1, map_json['row_count'], 2), ROOM_PX)


def render_game(spreadsheet_id, map_json, player):
    sheet_id = create_new_spreadsheet(spreadsheet_id, map_json)
    render_map(spreadsheet_id, sheet_id, map_json)
    render_player(spreadsheet_id, sheet_id, player)


def render_map(spreadsheet_id, sheet_id, map_json):
    set_dimensions(spreadsheet_id, sheet_id, map_json)
    color_cells(spreadsheet_id, sheet_id, map_json)


def render_player(spreadsheet_id, sheet_id, player):
    color_single_cell(spreadsheet_id, sheet_id,
                      player['current_room']['row'],
                      player['current_room']['column'],
                      PURPLE)


def find_sheet_id(spreadsheet_id, name):
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    res = [sheet['properties']['sheetId'] for sheet in sheets
           if sheet['properties']['title'] == name][0]
    return res


def create_new_spreadsheet(spreadsheet_id, map_json) -> int:
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
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body).execute()
    except HttpError:
        return find_sheet_id(spreadsheet_id, map_json['name'])
    return response['replies'][0]['addSheet']['properties']['sheetId']


service = generate_service()