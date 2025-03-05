from otree.api import *
import random
import math


class Constants(BaseConstants):
    name_in_url = 'welcome'
    players_per_group = 2
    num_rounds = 1
    BONUS_AMOUNT = Currency(5000)
    SENDER_ROLE = 'Player A'
    RECEIVER_ROLE = 'Player B'
    SHOW_UP_FEE = Currency(5000)

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass

class Player(BasePlayer):
    payoff_relevant_list = models.LongStringField(blank=True, default='')

    
    # Whether the current round is payoff-relevant (1) or not (0)




class Welcome(Page):

    def is_displayed(player: Player):

        return player.round_number == 1

    @staticmethod
    def before_next_page(player: Player, timeout_happened):

        if player.id_in_group == 1 or player.id_in_group == 3:
            player.participant.role = 'Player A'
        else:
            player.participant.role = 'Player B'
            if player.session.config['treatment'] == 'Decode':
                player.participant.receiver_type = 'Decode'
            else:
                player.participant.receiver_type = 'Direct'

        # Assign treatment based on session config
        if player.session.config['treatment'] == 'Babbling':
            player.participant.treatment = 'Babbling'
        if player.session.config['treatment'] == 'TruthButton':
            player.participant.treatment = 'TruthButton'
        if player.session.config['treatment'] == 'Decode':
            player.participant.treatment = 'Decode'
        

        
    # form_model = 'player'
    # form_fields = ['Prolific_ID']



page_sequence = [Welcome]
