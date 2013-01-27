import pickle
import pyglet

FONT = dict(font_name='Andale Mono',
            font_size=20)

class Rectangle(object):
    '''Draws a rectangle into a batch.'''
    def __init__(self, x1, y1, x2, y2, batch):
        self.vertex_list = batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v2i', [x1, y1, x2, y1, x2, y2, x1, y2]),
            ('c4B', [20, 20, 20, 255] * 4)
        )

class TextWidget(object):
    def __init__(self, text, x, y, width, batch):
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.document.set_style(0, len(self.document.text),
            dict(color=(255, 255, 255, 255), **FONT)
        )
        font = self.document.get_font()
        height = font.ascent - font.descent

        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width, height, multiline=False, batch=batch)
        self.caret = pyglet.text.caret.Caret(self.layout)

        self.layout.x = x
        self.layout.y = y

        # Rectangular outline
        pad = 2
        self.rectangle = Rectangle(x - pad, y - pad,
                                   x + width + pad, y + height + pad, batch)

    def hit_test(self, x, y):
        return (0 < x - self.layout.x < self.layout.width and
                0 < y - self.layout.y < self.layout.height)


class HighScores(object):

    def __init__(self, score_filename, modes=('',)):
        self.active = False
        self.score_filename = score_filename
        self.scores = {}
        default_scores = [(999, 'Ignas')] * 10
        try:
            self.load()
        except:
            pass
        for mode in modes:
            self.scores.setdefault(mode, list(default_scores))
        self.save()
        self.modes = modes
        self.mode = self.modes[0]
        self.instructions = self.makeLabel("Click to start".center(20))
        self.instructions.x -= self.instructions.width // 2
        self.instructions.y = -300

        self.enter_score = self.makeLabel("Enter your name:".center(20))
        self.enter_score.x -= self.enter_score.width // 2
        self.enter_score.y = -220

        self.score_labels = []
        self.generate_scores()
        self.current_score = None

        self.batch = pyglet.graphics.Batch()
        self.widget = TextWidget('', -200, -260, 300, self.batch)
        self.pushed = False

    def makeLabel(self, text):
        label = pyglet.text.Label(text, x=0, y=0, **FONT)
        label.height = 50
        label.width = len(text) * 20
        return label

    def generate_scores(self):
        self.score_labels = []
        self.score_labels.append(self.makeLabel('     High scores     '))
        if self.mode.strip():
            self.score_labels.append(self.makeLabel(('(%s)' % self.mode).center(20)))
        self.score_labels.append(self.makeLabel('====================='))
        for score, name in self.scores[self.mode]:
            self.score_labels.append(self.makeLabel('%s     % 7.2f' % (name[:10].ljust(10), score)))
        top_y = 200
        for label in self.score_labels:
            label.y = top_y
            label.x -= label.width // 2
            top_y -= 30

    def set_score(self, score):
        self.current_score = score

    def load(self):
        with open(self.score_filename) as f:
            self.scores = pickle.load(f)

    def save(self):
        with open(self.score_filename, 'w') as f:
            pickle.dump(self.scores, f)

    def add_score(self, name, score):
        self.scores[self.mode] += [(score, name)]
        self.scores[self.mode] = sorted(self.scores[self.mode])
        if len(self.scores[self.mode]) > 10:
            self.scores[self.mode] = self.scores[self.mode][:-1]
        self.save()
        self.generate_scores()

    def on_mouse_release(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            return False
        return True

    def saveScore(self, name):
        if self.current_score is not None:
            self.add_score(name, self.current_score)
            self.current_score = None

    def draw(self):
        self.instructions.draw()
        if self.current_score:
            self.batch.draw()
            self.enter_score.draw()
        for label in self.score_labels:
            label.draw()
