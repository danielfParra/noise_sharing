from otree.api import Bot
from . import *

class PlayerBot(Bot):
    def play_round(self):
        # ✅ Ensure session is correctly set up before yielding pages
        if not hasattr(self.session, 'config'):
            self.session.config = {'treatment': 'TruthButton'}

        yield Welcome
