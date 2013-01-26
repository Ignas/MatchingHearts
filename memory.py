#!/usr/bin/env python
import math
import os.path
import random
import logging
import itertools
from contextlib import contextmanager

import pyglet
from pyglet.window import key
from pyglet import gl


DEBUG_VERSION = False


log = logging.getLogger('dodo')

if DEBUG_VERSION:
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())


pyglet.resource.path = ['assets']
pyglet.resource.reindex()


window = None

def load_image(filename, **kw):
    img = pyglet.resource.image(filename)
    for k, v in kw.items():
        setattr(img, k, v)
    return img


@contextmanager
def gl_matrix():
    gl.glPushMatrix()
    try:
        yield
    finally:
        gl.glPopMatrix()


class Heart(object):

    def __init__(self):
        self.sprite = pyglet.sprite.Sprite(load_image('MessageHeart.png'))
        self.sprite.image.anchor_x = self.sprite.image.width // 2
        self.sprite.image.anchor_y = self.sprite.image.height // 2

    def draw(self):
        self.sprite.x = window.width // 2
        self.sprite.y = window.height // 2
        self.sprite.draw()


class Game(object):

    update_freq = 1 / 60.

    def __init__(self):
        self.game_is_over = False
        pyglet.clock.schedule_interval(self.update, self.update_freq)
        self.heart = Heart()

    def update(self, dt):
        pass

    def draw(self):
        with gl_matrix():
            if self.game_is_over:
                pass
            self.heart.draw()


class Main(pyglet.window.Window):

    fps_display = None

    def __init__(self):
        super(Main, self).__init__(width=1024, height=600,
                                   resizable=True,
                                   caption='Memory game')
        self.set_minimum_size(320, 200) # does not work on linux with compiz
        self.set_fullscreen()
        self.set_mouse_visible(True)
        self.set_icon(pyglet.image.load(
            os.path.join(pyglet.resource.location('MessageHeart.png').path, 'MessageHeart.png')))
        self.game = Game()

        self.fps_display = pyglet.clock.ClockDisplay()
        self.fps_display.label.y = self.height - 50
        self.fps_display.label.x = self.width - 170

    def on_draw(self):
        self.clear()
        self.game.draw()
        if self.fps_display:
            self.fps_display.draw()

    def run(self):
        pyglet.app.run()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.dispatch_event('on_close')

        if symbol == key.F:
            self.set_fullscreen(not self.fullscreen)

    def on_resize(self, width, height):
        if self.fps_display:
            self.fps_display.label.y = self.height - 50
            self.fps_display.label.x = self.width - 170
        super(Main, self).on_resize(width, height)


def main():
    global window
    window = Main()
    window.run()


if __name__ == '__main__':
    main()
