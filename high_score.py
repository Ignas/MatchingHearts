import pickle
import pyglet

font = dict(font_name='Andale Mono',
            font_size=20)


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
        text = "Click to start".center(20)
        self.instructions = self.makeLabel(text)
        self.instructions.x -= self.instructions.width // 2
        self.instructions.y = -300
        self.score_labels = []
        self.generate_scores()
        self.current_score = None

    def makeLabel(self, text):
        label = pyglet.text.Label(text, x=0, y=0, **font)
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

    def draw(self):
        if self.current_score is not None:
            self.add_score('Ignas', self.current_score)
            self.current_score = None
        self.instructions.draw()
        for label in self.score_labels:
            label.draw()
