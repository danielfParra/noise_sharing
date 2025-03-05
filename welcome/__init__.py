from otree.api import *
import random
import math


class Constants(BaseConstants):
    name_in_url = 'welcome'
    players_per_group = 1
    num_rounds = 1
    SHOW_UP_FEE = Currency(5000)


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass

class Player(BasePlayer):
    pass





class Welcome(Page):

    def is_displayed(player: Player):

        return player.round_number == 1



page_sequence = [Welcome]
