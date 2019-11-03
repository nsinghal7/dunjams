#####################################################################
#
# gfxutil.py
#
# Copyright (c) 2015, Eran Egozy
#
# Released under the MIT License (http://opensource.org/licenses/MIT)
#
#####################################################################


from kivy.clock import Clock as kivyClock
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Rectangle, Ellipse, Color, Fbo, ClearBuffers, ClearColor, Line
from kivy.graphics import PushMatrix, PopMatrix, Scale, Callback
from kivy.graphics.texture import Texture
from kivy.uix.label import Label
from kivy.core.window import Window

import numpy as np


# return a Label object configured to look good and be positioned at
# the top-left of the screen
def topleft_label() :
    l = Label(text = "text", valign='top', font_size='20sp',
              pos=(Window.width * 0.5 - 40, Window.height * 0.5 - 55),
              text_size=(Window.width, Window.height))
    return l

# if screen size has changed, call this, and it will move the label so that
# it remains in the top-left.
def resize_topleft_label(label):
    label.pos = (Window.width * 0.5 - 40, Window.height * 0.5 - 55)
    label.text_size = (Window.width, Window.height)

# class for creating labels that can be added
# to Widget canvases like standard Kivy graphics
# objects, like Rectangle and Circle
class CLabelRect(InstructionGroup):
    def __init__(self, pos, text = "Hello World", font_size = 21, font_name = "Arial"):
        super(CLabelRect, self).__init__()

        self.pos = pos
        self.font_size = font_size
        self.font_name = font_name

        self.label = Label(text=text, font_size=str(self.font_size)+"sp", font_name=self.font_name)
        self.label.texture_update()
        self.rect = Rectangle(pos=(pos[0]-(self.label.texture_size[0]*0.5), pos[1]-(self.label.texture_size[1]*0.5)), size=self.label.texture_size, texture=self.label.texture)
        self.add(self.rect)

    # this function must be called to trigger a texture update when changing a label's text
    def set_text(self, text):
        self.label.text = text
        self.label.texture_update()
        
        self.rect.pos = (self.pos[0]-(self.label.texture_size[0]*0.5), self.pos[1]-(self.label.texture_size[1]*0.5))
        self.rect.size = self.label.texture_size
        self.rect.texture = self.label.texture



# Override Ellipse class to add centered functionality.
# use cpos and csize to set/get the ellipse based on a centered registration point
# instead of a bottom-left registration point
class CEllipse(Ellipse):
    def __init__(self, **kwargs):
        super(CEllipse, self).__init__(**kwargs)
        if 'cpos' in kwargs:
            self.cpos = kwargs['cpos']

        if 'csize' in kwargs:
            self.csize = kwargs['csize']

    def get_cpos(self):
        return (self.pos[0] + self.size[0]/2, self.pos[1] + self.size[1]/2)

    def set_cpos(self, p):
        self.pos = (p[0] - self.size[0]/2 , p[1] - self.size[1]/2)

    def get_csize(self) :
        return self.size

    def set_csize(self, p) :
        cpos = self.get_cpos()
        self.size = p
        self.set_cpos(cpos)

    cpos = property(get_cpos, set_cpos)
    csize = property(get_csize, set_csize)



# Override Rectangle class to add centered functionality.
# use cpos and csize to set/get the rectangle based on a centered registration point
# instead of a bottom-left registration point
class CRectangle(Rectangle):
    def __init__(self, **kwargs):
        super(CRectangle, self).__init__(**kwargs)
        if 'cpos' in kwargs:
            self.cpos = kwargs['cpos']

        if 'csize' in kwargs:
            self.csize = kwargs['csize']

    def get_cpos(self):
        return (self.pos[0] + self.size[0]/2, self.pos[1] + self.size[1]/2)

    def set_cpos(self, p):
        self.pos = (p[0] - self.size[0]/2 , p[1] - self.size[1]/2)

    def get_csize(self) :
        return self.size

    def set_csize(self, p) :
        cpos = self.get_cpos()
        self.size = p
        self.set_cpos(cpos)

    cpos = property(get_cpos, set_cpos)
    csize = property(get_csize, set_csize)



# KeyFrame Animation class
# initialize with an argument list where each arg is a keyframe.
# one keyframe = (t, k1, k2, ...), where t is the time of the keyframe and
# k1, k2, ..., kN are the values
class KFAnim(object):
    def __init__(self, *kwargs):
        super(KFAnim, self).__init__()
        frames = list(zip(*kwargs))
        self.time = frames[0]
        self.frames = frames[1:]

    def eval(self, t):
        if len(self.frames) == 1:
            return np.interp(t, self.time, self.frames[0])
        else:
            return [np.interp(t, self.time, y) for y in self.frames]

    # return true if given time is within keyframe range. Otherwise, false.
    def is_active(self, t) :
        return t < self.time[-1]


# AnimGroup is a simple manager of objects that get drawn, updated with
# time, and removed when they are done
class AnimGroup(InstructionGroup) :
    def __init__(self):
        super(AnimGroup, self).__init__()
        self.objects = []

    # add an object. The object must be an InstructionGroup (ie, can be added to canvas) and
    # it must have an on_update(self, dt) method that returns True to keep going or False to end
    def add(self, obj):
        super(AnimGroup, self).add(obj)
        self.objects.append(obj)

    def on_update(self):
        dt = kivyClock.frametime
        kill_list = [o for o in self.objects if o.on_update(dt) == False]

        for o in kill_list:
            self.objects.remove(o)
            self.remove(o)

    def size(self):
        return len(self.objects)


# A graphics object for displaying a point moving in a pre-defined 3D space
# the 3D point must be in the range [0,1] for all 3 coordinates.
# depth is rendered as the size of the circle.
class Cursor3D(InstructionGroup):
    def __init__(self, area_size, area_pos, rgb, size_range = (10, 50), border = True):
        super(Cursor3D, self).__init__()
        self.area_size = area_size
        self.area_pos = area_pos
        self.min_sz = size_range[0]
        self.max_sz = size_range[1]

        if border:
            self.add(Color(1, 0, 0))
            self.add(Line(rectangle= area_pos + area_size))

        self.color = Color(*rgb)
        self.add(self.color)

        self.cursor = CEllipse(segments = 40)
        self.cursor.csize = (30,30)
        self.cursor.cpos = self.area_pos
        self.add(self.cursor)

    def to_screen_coords(self, pos):
        return pos[0:2] * self.area_size + self.area_pos

    # position is a 3D point with all values from 0 to 1
    def set_pos(self, pos):
        radius = self.min_sz + pos[2] * (self.max_sz - self.min_sz)
        self.cursor.csize = (radius*2, radius*2)
        self.cursor.cpos = pos[0:2] * self.area_size + self.area_pos

    def set_color(self, rgb):
        self.color.rgb = rgb

    def get_screen_xy(self) :
        return self.cursor.cpos



# convert the point pt to a unit range point spanning 0-1 in x,y, and z
# _range should be the array ((x_min, x_max), (y_min, y_max), (z_min, z_max))
# this is the expect bounds of the input point pt.
# if pt == 0, 
def scale_point(pt, _range):
    range_min = np.array((_range[0][0], _range[1][0], _range[2][0]))
    range_max = np.array((_range[0][1], _range[1][1], _range[2][1]))

    # pt == 0 is a special case meaning "no point". Return instead a point that is "furthest back" in Z
    if np.all(pt == 0):
        return np.array((0, 0, 1))

    pt = (pt - range_min) / (range_max - range_min)
    pt = np.clip(pt, 0, 1)
    return pt
