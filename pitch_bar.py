from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle, Triangle
from kivy.core.window import Window

# TODO: make this class be the bar on the right/bottom side of the screen indicating pitch matching???
# for now it's just a colored block
class PitchBar(InstructionGroup):
        def __init__(self, base_midi, width_ratio, height_ratio):
            super(PitchBar, self).__init__()

            self.base_midi = base_midi
            self.width_ratio = width_ratio
            self.height_ratio = height_ratio

            self.keys = []
            self.key_colors = []

            for i in range(12):
                color = Color(1, 1, 1)
                self.key_colors.append(color)
                self.add(color)
                key = Rectangle()
                self.keys.append(key)
                self.add(key)

            self.div_lines = []

            self.add(Color(0, 0, 0))

            for i in range(13):
                line = Line(width=3.0)
                self.div_lines.append(line)
                self.add(line)

            self.enemy_ptr_color = Color(1, 1, 1)
            self.add(self.enemy_ptr_color)
            self.enemy_ptr = Triangle()
            self.add(self.enemy_ptr)

            self.player_pitch = None
            self.enemy_pitch = None

            self.on_update()

        def on_enemy_note(self, midi):
            self.enemy_pitch = self.get_index(midi)

        def on_player_note(self, midi):
            self.set_key_color(self.player_pitch, (1, 1, 1))
            self.player_pitch = self.get_index(midi)
            self.set_key_color(self.player_pitch)

        def set_key_color(self, index, rgb=None):
            if index is not None:
                if rgb is None:
                    rgb = Color(index / 13, 1, 1, mode='hsv').rgba
                self.key_colors[index].rgb = rgb

        def get_index(self, midi):
            midi = int(round(midi))
            return None if midi == 0 else (midi - self.base_midi) % 12

        def on_update(self):
            width_ratio = self.width_ratio
            height_ratio = self.height_ratio

            for i, key in enumerate(self.keys):
                x = Window.width * width_ratio * (i + 1) // 14
                key.pos = (x, 0)
                key.size = (Window.width * width_ratio // 14, Window.height * height_ratio)

            for i, line in enumerate(self.div_lines):
                x = Window.width * width_ratio * (i + 1) // 14
                line.points = (x, 0, x, Window.height * height_ratio - 2)

            if self.enemy_pitch is None:
                self.enemy_ptr.points = (-1, -1, -1, -1, -1, -1)
            else:
                self.enemy_ptr_color.rgb = self.key_colors[self.enemy_pitch].rgb
                x = Window.width * width_ratio * (self.enemy_pitch + 1) // 14 + Window.width * width_ratio // (14 * 2)
                dx = Window.width * width_ratio // (14 * 8)
                y = Window.height * height_ratio * 5 // 4
                dy = Window.height * height_ratio // 10
                self.enemy_ptr.points = (x - dx, y, x + dx, y, x, y - dy)
