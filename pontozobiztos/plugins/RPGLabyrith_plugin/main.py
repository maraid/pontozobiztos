from RPGLabyrinth.models import Map, Player
from RPGLabyrinth.controller import GameEngine
import google_sheets

if __name__ == '__main__':
    engine = GameEngine()
    engine.setup()
    engine.play()

    # game = GameEngine()
    # # game.generate_map('smol', 5, 5)
    # # game.setup()
    # # game.upload_to_sheets('new_tab')
    # # game.render()
    #
    # game.generate_map('Testmap', 11, 11)
    # game.setup()
    # # game.upload_to_sheets()
    # # game.render()
    # # game.upload_to_sheets('asd')
    # # print(game.map.to_dict())
    # game.play()
    # google_api_helper.save_map_data()