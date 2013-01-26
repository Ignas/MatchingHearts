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

from high_score import HighScores

DEBUG_VERSION = False


log = logging.getLogger('hearts')

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

    images = [load_image('MessageHeart.png'),
              load_image('BlueMessageHeart.png'),
              load_image('GreenMessageHeart.png'),
              load_image('YellowMessageHeart.png')]
    pxWidth = 64
    pxHeight = 64
    pxPadding = 10

    totalWidth = pxWidth + pxPadding
    totalHeight = pxHeight + pxPadding

    def pickHeart(self, n):
        self.n = n
        size_count = len(self.sizes)
        self.beat = self.sizes[n % size_count]

        remainder = n / size_count
        shift_count = len(self.shifts)
        self.shift = self.shifts[remainder % shift_count]

        remainder = remainder / shift_count
        self.image = self.images[remainder]

    def __init__(self, mapX, mapY, n):
        self.mapX = mapX
        self.mapY = mapY
        self.pickHeart(n)
        self.sprite = pyglet.sprite.Sprite(self.image)
        self.sprite.image.anchor_x = self.sprite.image.width // 2
        self.sprite.image.anchor_y = self.sprite.image.height // 2
        self.total_time = 0
        self.total_time += self.shift
        self.selected = False

    def draw(self):
        self.sprite.x = self.totalWidth * self.mapX
        self.sprite.y = self.totalHeight * self.mapY
        self.sprite.draw()

    sizes = ([0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.9, 1.0, 0.9],
             [0.8, 0.8, 0.8, 0.8, 0.9, 1.0, 0.9, 0.8, 0.8, 0.8, 0.8, 0.9, 1.0, 0.9])
    shifts = [0.0, 0.25, 0.5, 0.75]
    seconds = 2.0

    def update(self, dt):
        self.total_time += dt
        cycle = (self.total_time % self.seconds) / self.seconds
        frames = len(self.beat)
        frame = int(frames * cycle)
        scale = self.beat[frame]
        if self.selected:
            scale *= 1.5
        self.sprite.scale = scale

    def isHit(self, x, y):
        return ((self.sprite.y - self.sprite.image.anchor_y < y < self.sprite.y + self.sprite.image.anchor_y) and
                (self.sprite.x - self.sprite.image.anchor_x < x < self.sprite.x + self.sprite.image.anchor_x))


class Game(object):

    update_freq = 1 / 60.

    def updateOffsets(self):
        self.pxHorizontalShift = window.width // 2
        self.pxVerticalShift = window.height // 2
        self.pxHorizontalShift -= Heart.totalWidth * self.mapWidth // 2
        self.pxVerticalShift -= Heart.totalHeight * self.mapHeight // 2

    def __init__(self, level=0):
        self.game_is_over = False
        pyglet.clock.schedule_interval(self.update, self.update_freq)
        self.start(level)

    levels = [('Beginner', 4, 4),
              ('Easy', 4, 6),
              ('Normal', 6, 6),
              ('Hard', 6, 8),
              ('Expert', 8, 8)]
    modes = [l[0] for l in levels]

    def start(self, level):
        self.time_in_level = 0
        self.level = level
        self.mode, self.mapWidth, self.mapHeight = self.levels[level]
        heart_styles = range(self.mapHeight * self.mapWidth / 2) * 2
        random.shuffle(heart_styles)
        self.selected_heart = None
        self.hearts = []
        for mapX in range(self.mapWidth):
            for mapY in range(self.mapHeight):
                self.hearts.append(Heart(mapX, mapY, heart_styles.pop()))

    @property
    def score(self):
        return self.time_in_level

    def update(self, dt):
        self.time_in_level += dt
        for heart in self.hearts:
            heart.update(dt)
        self.updateOffsets()

    def draw(self):
        with gl_matrix():
            if self.game_is_over:
                pass
            with gl_matrix():
                gl.glTranslatef(self.pxHorizontalShift, self.pxVerticalShift, 0)
                for heart in self.hearts:
                    heart.draw()

    def on_mouse_release(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            pxRealX = x - self.pxHorizontalShift
            pxRealY = y - self.pxVerticalShift
            for heart in self.hearts:
                if heart.isHit(pxRealX, pxRealY):
                    heart.selected = True
                    if (self.selected_heart is not None and
                        heart.n == self.selected_heart.n and
                        heart is not self.selected_heart):
                        self.hearts.remove(heart)
                        self.hearts.remove(self.selected_heart)
                        self.selected_heart = None
                    else:
                        if self.selected_heart is not None:
                            self.selected_heart.selected = False
                        self.selected_heart = heart
            if not self.hearts:
                return Main.SCORE
        return Main.PLAYING


class Main(pyglet.window.Window):

    fps_display = None

    SCORE = object()
    PLAYING = object()
    START = object()

    def __init__(self):
        super(Main, self).__init__(width=1024, height=600,
                                   resizable=True,
                                   caption='Matching Hearts')
        self.set_minimum_size(320, 200) # does not work on linux with compiz
        self.set_fullscreen()
        self.set_mouse_visible(True)
        self.set_icon(pyglet.image.load(
            os.path.join(pyglet.resource.location('MessageHeart.png').path, 'MessageHeart.png')))
        self.game = Game()
        self.high_score = HighScores('hearts.score', self.game.modes)
        self.state = self.SCORE
        self.fps_display = pyglet.clock.ClockDisplay()
        self.fps_display.label.y = self.height - 50
        self.fps_display.label.x = self.width - 170

    def on_draw(self):
        self.clear()
        if self.state is self.START:
            self.game.start(self.game.level)
            self.high_score.mode = self.game.mode
            self.state = self.PLAYING
        elif self.state is self.SCORE:
            with gl_matrix():
                gl.glTranslatef(window.width / 2, window.height // 2, 0)
                self.high_score.draw()
        else:
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
        if symbol == key.PLUS or symbol == key.EQUAL:
            self.game.start(min(self.game.level + 1, 4))
            self.high_score.mode = self.game.mode
            self.high_score.generate_scores()
        if symbol == key.MINUS:
            self.game.start(max(self.game.level - 1, 0))
            self.high_score.mode = self.game.mode
            self.high_score.generate_scores()
        if symbol == key.ASCIITILDE:
            self.game.hearts = []
        if symbol == key.F:
            self.set_fullscreen(not self.fullscreen)

    def on_resize(self, width, height):
        if self.fps_display:
            self.fps_display.label.y = self.height - 50
            self.fps_display.label.x = self.width - 170
        super(Main, self).on_resize(width, height)

    def on_mouse_release(self, *args):
        if self.state is self.SCORE:
            self.state = self.START
        else:
            self.state = self.game.on_mouse_release(*args)
            if self.state == self.SCORE:
                self.high_score.set_score(self.game.score)

def main():
    global window
    window = Main()
    window.run()


if __name__ == '__main__':
    main()
