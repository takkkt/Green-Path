"""Select from the editable dialogue.json; keep dialogue RNG separate from combat."""
import json
from pathlib import Path
import random

CONTENT = json.loads(Path(__file__).with_name("dialogue.json").read_text(encoding="utf-8"))
LOGIN_FLAVOUR = CONTENT["login_flavour"]
FACTS = [(fact["topic"], fact["text"], fact["source"]) for fact in CONTENT["facts"]]
SCENES = CONTENT["scenes"]

class ShuffleBag:
    def __init__(self, items):
        self.items = list(items)
        self.remaining = []
        self.last = None
        self.rng = random.Random()

    def next(self):
        if not self.remaining:
            self.remaining = self.items.copy()
            self.rng.shuffle(self.remaining)
            if len(self.remaining) > 1 and self.remaining[-1] == self.last:
                self.remaining[0], self.remaining[-1] = self.remaining[-1], self.remaining[0]
        self.last = self.remaining.pop()
        return self.last

def fact_deck(name):
    name = name.lower()
    topics = {'water', 'plastic'} if 'ganga' in name or 'river' in name else {'air', 'plastic'} if any(w in name for w in ('taj', 'delhi', 'city', 'agra')) else {'air', 'water', 'plastic'}
    return ShuffleBag([text for topic, text, source in FACTS if topic in topics])

def scene_for(place):
    place = dict(place)
    scene = SCENES.get(place['name'], {'title': 'A place worth protecting',
        'arrival': place['description'], 'victory': 'One more place can breathe. Nicely done.'})
    return dict(scene, arrival=place['description']) if place.get('art_style') else scene
