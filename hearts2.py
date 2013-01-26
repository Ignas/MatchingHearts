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


log = logging.getLogger('hearts')

if DEBUG_VERSION:
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())


pyglet.resource.path = ['assets']
pyglet.resource.reindex()


window = None
font = dict(font_name='Andale Mono',
            font_size=20)

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


class Board(object):

    def __init__(self):
        self.board = pyglet.sprite.Sprite(load_image('blackbox.png'))
        self.board.image.anchor_x = self.board.image.width // 2
        self.board.image.anchor_y = self.board.image.height // 2

    def draw(self):
        self.board.x = window.width // 2
        self.board.y = window.height // 2
        self.board.draw()

def mapMapCoords(pxX, pxY):
    pxWidth = 50
    pxHeight = 50
    pxCenterX = window.width // 2
    pxCenterY = window.height // 2
    mapCenterX = 7
    mapCenterY = 7

    pxOffsetX = pxX - pxCenterX
    pxOffsetY = pxY - pxCenterY

    mapOffsetX = pxOffsetX // pxWidth
    mapOffsetY = pxOffsetY // pxHeight

    mapX = mapCenterX + mapOffsetX
    mapY = mapCenterY + mapOffsetY

    return mapX, mapY


class Ear(object):

    def __init__(self, sound_file, image_file, mapX, mapY, heart):
        self.sound = pyglet.resource.media(sound_file, streaming=True)
        self.sprite = pyglet.sprite.Sprite(load_image(image_file))
        self.sprite.image.anchor_x = self.sprite.image.width // 2
        self.sprite.image.anchor_y = self.sprite.image.height // 2
        self.player = pyglet.media.Player()
        self.player.queue(self.sound)
        self.player.eos_action = self.player.EOS_LOOP
        self.player.play()
        self.heart = heart
        self.mapX, self.mapY = mapX, mapY
        self.computeVolume()

    def computeVolume(self):
        mapDistance = math.hypot(self.mapX - self.heart.mapX, self.mapY - self.heart.mapY)
        sound_level = computeVolume(mapDistance)
        self.player.volume = sound_level % 1.0

    def pxScreenCoords(self, mapX, mapY):
        pxWidth = 50
        pxHeight = 50
        pxCenterX = window.width // 2
        pxCenterY = window.height // 2
        mapCenterX = 7
        mapCenterY = 7

        mapOffsetX = mapX - mapCenterX
        mapOffsetY = mapY - mapCenterY

        pxOffsetX = mapOffsetX * pxWidth + 25
        pxOffsetY = mapOffsetY * pxHeight + 25

        return (pxCenterX + pxOffsetX , pxCenterY + pxOffsetY)

    def move(self, x, y):
        mapX, mapY = mapMapCoords(x, y)
        if not (0 <= mapX <= 13 and 0 <= mapY <= 13):
            return
        if not (mapX in (0, 13) or mapY in (0, 13)):
            return
        self.mapX, self.mapY = mapX, mapY
        self.computeVolume()

    def draw(self):
        self.sprite.x, self.sprite.y = self.pxScreenCoords(self.mapX, self.mapY)
        self.sprite.draw()


def computeVolume(distance):
    return (1/900.0 * (distance ** 2) - (13/180.0 * distance) + 241/225.0)


class Heart(object):

    def __init__(self, mapX, mapY):
        self.mapX, self.mapY = mapX, mapY



class Main(pyglet.window.Window):

    fps_display = None
    update_freq = 1/60.

    def __init__(self):
        super(Main, self).__init__(width=1024, height=600,
                                   resizable=True,
                                   caption='Matching Hearts')
        self.set_minimum_size(320, 200) # does not work on linux with compiz
        self.set_fullscreen()
        self.set_mouse_visible(True)
        self.set_icon(pyglet.image.load(
            os.path.join(pyglet.resource.location('MessageHeart.png').path, 'MessageHeart.png')))
        self.board = Board()
        self.heart = Heart(random.randint(1, 12), random.randint(1, 12))
        self.left_ear = Ear('left.wav', 'left.png', 0, 13, self.heart)
        self.right_ear = Ear('right.wav', 'right.png', 13, 0, self.heart)
        pyglet.clock.schedule_interval(self.update_flashes, self.update_freq)
        self.fps_display = pyglet.clock.ClockDisplay()
        self.fps_display.label.y = self.height - 50
        self.fps_display.label.x = self.width - 170

    def on_draw(self):
        self.clear()
        self.board.draw()
        self.left_ear.draw()
        self.right_ear.draw()
        self.draw_flashes()
        # self.game.draw()
        if self.fps_display:
            self.fps_display.draw()

    def run(self):
        pyglet.app.run()

    def on_mouse_release(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            self.left_ear.move(x, y)
        elif button == pyglet.window.mouse.RIGHT:
            self.right_ear.move(x, y)
        elif button == pyglet.window.mouse.MIDDLE:
            mapX, mapY = mapMapCoords(x, y)
            distance = math.hypot(mapX - self.heart.mapX, mapY - self.heart.mapY)
            self.flash_text("Distance: %.2f" % round(distance, 2),
                            window.width // 2,
                            window.height // 2,
                            1)
            self.heart.mapX, self.heart.mapY = random.randint(1, 12), random.randint(1, 12)
            self.left_ear.computeVolume()
            self.right_ear.computeVolume()

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


    flashes = []
    def flash(self, flash, t):
        self.flashes.append((t, flash))

    def draw_flashes(self):
        for t, flash in self.flashes:
            flash.draw()

    def update_flashes(self, dt):
        self.flashes = [(t - dt, flash)
                        for (t, flash) in self.flashes
                        if t - dt > 0]

    def flash_text(self, text, x, y, t):
        label = pyglet.text.Label(text, x=x, y=y, **font)
        label.height = 50
        label.width = len(text) * 40
        label.x = x - (label.width // 4)
        self.flash(label, t)


def main():
    global window
    window = Main()
    window.run()


if __name__ == '__main__':
    main()
