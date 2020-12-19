import models
import google_sheets


class GameEngine:
    def __init__(self):
        self.gs = google_sheets.GoogleSheetsApiHelper('1KazNpZe2H_LewGExiwVskpMCji0VF2P_ovy4l1qNCUg', )
        self.map = None
        self.protagonist = None
        self.is_set_up = False

    # def load_from_sheets(self,
    #                      sheet_id='101TbUrHCJ5wgNqRvyfoYb8FAtyHVYrj9LDPOElF3FN4',
    #                      tab_name='Map',1
    #                      force=False):
    #     result = google_api_helper.fetch_map_data(sheet_id, tab_name)
    #     db_map = models.Map.objects(name=result['name'])
    #     if (not db_map
    #        or db_map[0]['column_count'] != result['column_count']
    #        or db_map[0]['row_count'] != result['row_count']
    #        or force):
    #         self.map = models.Map.from_dict(result)
    #         self.map.save()
    #         self.is_set_up = False
    #     else:
    #         self.map = db_map[0]
    #         self.is_set_up = True

    def generate_map(self, name: str, n: int, m: int):
        self.map = models.Map.generate_map(name, n, m)
        self.is_set_up = False

    # def upload_to_sheets(self,
    #                      spreadsheet_id='1KazNpZe2H_LewGExiwVskpMCji0VF2P_ovy4l1qNCUg'):
    #     map_dict = self.map.to_dict()
    #     print(map_dict)
    #     player = self.controller.player.to_dict()
    #     google_api_helper.render_game(spreadsheet_id, map_dict, player)

    def setup(self):
        try:
            self.protagonist = models.Player.objects(name='Chat')[0]
        except IndexError:
            self.protagonist = models.Player(name='Chat')
            self.protagonist.save()
        self.gs.set_player(self.protagonist)
        self.gs.load_map()
        self.map = self.gs.map
        self.protagonist.move(self.map.get_start_room())
        self.is_set_up = True

    def play(self):
        if not self.is_set_up:
            self.setup()
        while True:
            self._mainloop()

    def _mainloop(self):
        self.gs.draw_map()
        # gs.draw_player(self.protagonist)
        doors = self.protagonist.current_room.doors
        useable_doors = {key: doors[key] for key in doors
                         if not doors[key].is_blocked}
        possible_directions = list(useable_doors.keys())
        while True:
            try:
                chosen = input('Merre menjek?\n  '
                               + '\n  '.join(possible_directions)
                               + '\n')
                useable_doors[chosen].go_through(self.protagonist)
                break
            except KeyError:
                continue




