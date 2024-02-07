from manim import Scene, Square, Circle, BLUE, RED, GREEN, MoveAlongPath, Line, NumberPlane, BLACK, config, WHITE, AnimationGroup, ApplyMethod, UP, DOWN, LEFT, Rectangle, Text

config.pixel_height = 1920
config.pixel_width = 1920
config.frame_height = 16.0
config.frame_width = 16.0
config.background_color = WHITE

class Bot:
    def __init__(self, scene, color, initial_position):
        self.scene = scene
        grid_space_scale = 0.2
        self.box = Square(color=color).scale(3*grid_space_scale)
        self.box.move_to(self._grid_to_scene_coords(initial_position))
        self.held_item = None  

    def move_to_point(self, point, run_time=2):
        target_position = self._grid_to_scene_coords(point)
        bot_move_animation = ApplyMethod(self.box.move_to, target_position)

        if self.held_item is not None:

            item_move_animation = ApplyMethod(self.held_item.item.move_to, target_position)

            return AnimationGroup(bot_move_animation, item_move_animation, lag_ratio=0)
        else:
            return bot_move_animation

    def pick_up_item(self, item):

        if self._is_close_to(item):
            self.held_item = item
            item.being_held = True

            bot_center = self.box.get_center()

            move_to_bot_center = ApplyMethod(item.item.move_to, bot_center)
            return move_to_bot_center
        else:
            return None

    def place_item(self, new_position):
        if self.held_item is not None:
            animation = ApplyMethod(self.held_item.item.move_to, self._grid_to_scene_coords(new_position))
            self.held_item.being_held = False
            self.held_item = None
            return animation
        else:
            return None

    def _is_close_to(self, item):

        bot_pos = self.box.get_center()
        item_pos = item.item.get_center()
        return abs(bot_pos[0] - item_pos[0]) <= 1 and abs(bot_pos[1] - item_pos[1]) <= 1

    def _grid_to_scene_coords(self, point):
        x, y = point
        scene_x = ((x - 25) * 16 / 50)
        scene_y = ((y - 25) * 16 / 50)
        return scene_x, scene_y, 0

class Item:
    def __init__(self, scene, color, position):
        self.scene = scene
        grid_space_scale = 0.1  
        self.item = Circle(color=color).scale(3*grid_space_scale)  
        self.item.move_to(self._grid_to_scene_coords(position))
        self.being_held = False  

    def move_to(self, new_position):
        self.item.move_to(new_position)

    def _grid_to_scene_coords(self, point):
        x, y = point
        scene_x = ((x - 25) * 16 / 50)
        scene_y = ((y - 25) * 16 / 50)
        return scene_x, scene_y, 0

class RobotScene(Scene):
    def setup_scene(self):
        grid = NumberPlane(
            x_range=[0, 50, 5],
            y_range=[0, 50, 5],
            x_length=16,
            y_length=16,
            background_line_style={"stroke_color": BLACK, "stroke_width": 1}
        )
        self.add(grid)

        line = Line(start=grid.c2p(25, 0), end=grid.c2p(25, 50), color=BLACK, stroke_width=3)
        self.add(line)

        self.blue_bot = Bot(self, BLUE, (12.5, 25))
        self.add(self.blue_bot.box)

        self.red_bot = Bot(self, RED, (37.5, 25))
        self.add(self.red_bot.box)

        load_zone_color = BLUE
        load_zone_fill_opacity = 0.5
        left_positions = [(5, 40), (5, 25), (5, 10)]
        right_positions = [(45, 40), (45, 25), (45, 10)]
        load_zone_labels = ["A", "B", "C", "D", "E", "F"]

        for i, pos in enumerate(left_positions):
            zone = Rectangle(width=3, height=2, color=load_zone_color, fill_opacity=load_zone_fill_opacity)
            zone.move_to(grid.c2p(*pos))
            self.add(zone)

            label = Text(load_zone_labels[i], font_size=36, color=BLACK).move_to(zone)
            self.add(label)

        for i, pos in enumerate(right_positions, start=len(left_positions)):
            zone = Rectangle(width=3, height=2, color=load_zone_color, fill_opacity=load_zone_fill_opacity)
            zone.move_to(grid.c2p(*pos))
            self.add(zone)

            label = Text(load_zone_labels[i], font_size=36, color=BLACK).move_to(zone)
            self.add(label)

    def construct(self):
        self.setup_scene()
        
class AIScene(RobotScene):
    def construct(self):
        super().construct()

        # Load an item at load zone D
        item = Item(self, color=GREEN, position=(45, 40))
        self.add(item.item)

        # Move the red robot to load zone D to pick up the item
        self.play(self.red_bot.move_to_point((43, 40)))
        self.wait(1)

        # Pick up the item from load zone D
        self.play(self.red_bot.pick_up_item(item))
        self.wait(1)

        # Move the red robot to the barrier
        self.play(self.red_bot.move_to_point((27, 25)))
        self.wait(1)

        # Place the item on the barrier
        self.play(self.red_bot.place_item((25, 25)))
        self.wait(1)

        # Move the blue robot to the barrier to pick up the item
        self.play(self.blue_bot.move_to_point((23, 25)))
        self.wait(1)

        # Pick up the item from the barrier
        self.play(self.blue_bot.pick_up_item(item))
        self.wait(1)

        # Move the blue robot to load zone A
        self.play(self.blue_bot.move_to_point((5, 40)))
        self.wait(1)

        # Place the item at load zone A
        self.play(self.blue_bot.place_item((5, 40)))
        self.wait(1)







AIScene2 = AIScene()
AIScene2.render()