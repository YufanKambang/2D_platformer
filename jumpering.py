import arcade
import pathlib

# _____________game constants_____________
#  the dimensions of the window
SCREEN_WIDTH = 1250
SCREEN_HEIGHT  = 700
SCREEN_TITLE = "Arcade Platformer"

# scaling constant
MAP_SCALING = 1
CHARACTER_SCALING = 0.5
TILE_SCALING = 0.5
COIN_SCALING = 0.5
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING

# player constant
GRAVITY = 1
PLAYER_START_X = 50
PLAYER_START_Y = 512
MOVEMENT_SPEED = 7
PLAYER_JUMP_SPEED = 14

# assets path
ASSET_PATH = pathlib.Path(__file__).resolve().parent / "assets"

# constants used to track if player is facing left or right
LEFT_FACING = 1
RIGHT_FACING = 0

# what are the names of the layers in the map
wall_layer = "ground"
coin_layer = "coins"
goal_layer = "goal"
background_layer = "background"
ladder_layer = "ladders"
moving_platform_layer = "moving platform"
player_layer = "Player"

def load_texture_pair(filename):
    """load a texture pair, with second being a mirror image"""
    return[
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]

class player_character(arcade.Sprite):
    """Player Sprite"""
    def __init__(self):

        # set up parent class
        super().__init__()

        # default to right facing
        self.player_face_direction = RIGHT_FACING

        # used for flipping between image sequences
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        # track our state
        self.jumping = False
        self.climbing = False
        self.is_on_ladder = False

        # --- load textures ---
        
        # address to the blue alien asset pack
        main_path = ASSET_PATH / "images" / "Players" / "128x256" / "Blue" / "alienBlue"

        # load textures for idle standing
        self.idle_texture_pair = load_texture_pair(f"{main_path}_stand.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}_duck.png")

        # load textures for walking
        self.walk_texture = []
        for i in range(1, 3):
            texture = load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_texture.append(texture)

        # load textures for climbing
        self.climbing_texture = []
        for i in range(1, 3):
            texture = arcade.load_texture(f"{main_path}_climb{i}.png")
            self.climbing_texture.append(texture)

        # set the initial texture
        self.texture = self.idle_texture_pair[0]

        # hit box will be based on the first image used
        # if you want to specify a diff hit box, can do it like the code below
        # set_hit_box = [[-22, -64], [22, -64], [22, 28], [-22, 28]]
        self.hit_box = self.texture.hit_box_points

    def update_animation(self, delta_time: float = 1 / 60):
        
        # figure out if we need to flip face to left or right
        if self.change_x < 0 and self.player_face_direction == RIGHT_FACING:
            self.player_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.player_face_direction == LEFT_FACING:
            self.player_face_direction = RIGHT_FACING

        # jumping animation
        if self.change_y > 0 and not self.is_on_ladder:
            self.texture = self.jump_texture_pair[self.player_face_direction]
            return
        elif self.change_y < 0 and not self.is_on_ladder:
            self.texture = self.jump_texture_pair[self.player_face_direction]
            return
        
        # idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.player_face_direction]
            return

        # walking animation
        self.cur_texture += 1
        if self.cur_texture >= 2:
            self.cur_texture = 0
        self.texture = self.walk_texture[self.cur_texture][self.player_face_direction]

class Platform(arcade.Window):
    def __init__(self) -> None:
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        
        # these lists will hold different sets of sprites
        self.coin = None
        self.background = None
        self.walls = None
        self.ladders = None
        self.goals = None
        self.enemies = None

        #the scene that contain all the sprites to be on
        self.scene = None
        # player sprite
        self.player_sprite = None

        # tracks the current state of keys being pressed for movement
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        #physiscs engine
        self.physics_engine = None

        # a camera that can be used for scrolling the screen
        self.camera = None

        # a camera used to draw 
        self.gui_camera = None

        # keep track of the score
        self.score = 0

        # our TileMap Object
        self.tile_map = None

        # level they are on
        self.level = 1

        # load up our sounds here
        self.coin_sound = arcade.load_sound(
            str(ASSET_PATH / "sounds" / "coin.wav")
        )

        self.jump_sound = arcade.load_sound(
            str(ASSET_PATH / "sounds" / "jump.mp3")
        )

        self.victory_sound = arcade.load_sound(
            str(ASSET_PATH / "sounds" / "victory.wav")
        )

    def setup(self) -> None:
        """sets up game for the current level"""
        # initialize scene
        self.scene = arcade.Scene()

        # # create the ground for platyer to stand on
        # for x in range(0, 1500, 64):
        #     wall = arcade.Sprite(ASSET_PATH / "images" / "Ground" / "Grass" / "grassMid.png", TILE_SCALING)
        #     wall.center_x = x
        #     wall.center_y = 32
        #     self.scene.add_sprite("Walls", wall)

        # # put some crates in the ground 
        # # coordinate list that is used to place sprites
        # coordinate_list = [[512, 96], [256, 96], [768, 96]]

        # for coordinate in coordinate_list:
        #     # add a crate to the ground
        #     wall = arcade.Sprite(
        #         ASSET_PATH / "images" / "Tiles" / "boxCrate_double.png", TILE_SCALING 
        #     )
        #     wall.position = coordinate
        #     self.scene.add_sprite("Walls", wall)

        # # use loop to place coins for player to pick up
        # for x in range(128, 1250, 256):
        #     coin = arcade.Sprite(ASSET_PATH / "images" / "Items" / "coinGold.png", COIN_SCALING)
        #     coin.center_x = x
        #     coin.center_y = 96
        #     self.scene.add_sprite("Coins", coin)


        # set up camera
        self.camera = arcade.Camera(self.width, self.height)

        # set up GUI camera
        self.gui_camera = arcade.Camera(self.width, self.height)

        # keep track of the score
        self.score = 0 

        # get the current map based on the level
        map_name = f"platform_level_{self.level:02}.tmx"
        map_path = ASSET_PATH / map_name

        # load the current map
        game_map = arcade.TileMap(str(map_path))

        # these are the layer specific options for Tilemap // "use_spactial_hash" when true will detect collisions
        # doing this will make the SpriteList for the platform layers
        # use spatial hashing for detection
        layer_options = {
            wall_layer: {
                "use_spatial_hash": True,
            },
            moving_platform_layer: {
                "use_spatial_hash": False,
            },
            coin_layer: {
                "use_spatial_hash": True,
            },
            goal_layer: {
                "use_spatial_hash": True,
            },
            background_layer: {
                "use_spatial_hash": False,
            },
            ladder_layer: {
                "use_spatial_hash": True,
            },
        }

        # load in the tile map
        self.tile_map = arcade.load_tilemap(map_path, TILE_SCALING, layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map) # turn fix this as it as the tile map need to be intersted into the scene list and then drawn

        #self.player_sprite = arcade.Sprite(ASSET_PATH / "images" / "Players" / "128x256" / "Blue" / "alienBlue_stand.png", CHARACTER_SCALING)
        self.player_sprite = player_character()

        # add sprite to your scene which is new sprite list
        # add the player sprite list before the "ground" layer
        #akes sure the "ground" is drawn after the player
        self.scene.add_sprite_list_after(player_layer, wall_layer)
        
        # set the player into the starting position
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        
        # adds player sprite the sprite list
        self.scene.add_sprite(player_layer, self.player_sprite)        

        # set the background colour
        background_colour = arcade.color.FRESH_AIR
        if game_map.background_color:
            background_colour = game_map.background_color
        arcade.set_background_color(background_colour)

        # # create the player sprite if not already set up
        # if not self.player:
        #     self.player = self.create_player_sprite()


        

        #load the physics engine for this map
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            player_sprite = self.player_sprite,
            platforms = self.scene[moving_platform_layer],
            gravity_constant = GRAVITY,
            walls = self.scene[wall_layer],
        )

    def create_player_sprite() -> arcade.AnimatedWalkingSprite:
        """creates a animates player sprite"""

    def update_player_speed(self):
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        if self.up_pressed and not self.down_pressed:
            self.player_sprite.change_y = PLAYER_JUMP_SPEED
            self.up_pressed = False
        elif self.down_pressed and not self.up_pressed:
            self.player_sprite.change_y = -MOVEMENT_SPEED
        if self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -MOVEMENT_SPEED

    def on_draw(self):
        """renders the screeen fro the player"""
        # clears the screen to background colour
        self.clear()

        # activates our camera
        self.camera.use()

        # draws all the sprite 
        self.scene.draw()
        
        # Activate the GUI camera before drawing GUI element
        self.gui_camera.use()

        # Draw our score on the screen, scrolling it with the viewport
        score_text = f"Score: {self.score}"
        arcade.draw_text(
            text= score_text,
            start_x= 10,
            start_y= 10,
            color= arcade.csscolor.WHITE,
            font_size= 18,
        )

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.W or key == arcade.key.UP:
            if self.physics_engine.can_jump(): # when player holds down the up keys after jumping and presses left orrighht to move, they jump and move 
                self.up_pressed = True
                arcade.play_sound(self.jump_sound)
                self.update_player_speed()
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.down_pressed = True
            self.update_player_speed()
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.right_pressed = True
            self.update_player_speed()
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.left_pressed = True
            self.update_player_speed()

    def on_key_release(self, key: int, modifiers: int):
        if key == arcade.key.W or key == arcade.key.UP:
            self.up_pressed = False
            self.update_player_speed()
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.down_pressed = False
            self.update_player_speed()
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.right_pressed = False
            self.update_player_speed()
        elif key == arcade.key.A or key == arcade.key.LEFT:
            self.left_pressed = False
            self.update_player_speed()

    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (self.camera.viewport_height / 2)

        # dont let the camera travel past 0
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        player_centered = screen_center_x, screen_center_y

        self.camera.move_to(player_centered)

    def on_update(self, delta_time: float):

        # moves the player with physics engine
        self.physics_engine.update()

        # update the animation
        self.scene.update_animation(
            delta_time, [player_layer]
        )

        # position the camera
        self.center_camera_to_player()

        # update walls, usind with moving platforms
        self.scene.update()

        # see if player hits coin
        coin_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[coin_layer]
        )

        # loop through each coin we hit (if any) and remove it
        for coin in coin_hit_list:

            # figure out how many points a coin is worth
            if "point_value" not in coin.properties:
                print("Warning! no point property in collected coin")
            else:
                points = int(coin.properties["point_value"])
                self.score += points
            
            # removes a coin
            coin.remove_from_sprite_lists()
            # play a sound
            arcade.play_sound(self.coin_sound)
            

    
if __name__ == "__main__":
    window = Platform()
    window.setup()
    arcade.run()
    print()