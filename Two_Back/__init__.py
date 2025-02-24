from otree.api import *

doc = """2-back task"""

class C(BaseConstants):
    NAME_IN_URL = 'Two_Back'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    N = 2 # The "n" in n-back
    trialDuration = 2000  # Time per round (ms)
    intertrialDuration = 1000  # Time between rounds (ms)
    item_styles = ["glyphicon-tree-deciduous", "glyphicon-fire", "glyphicon-tint", "glyphicon-certificate"]

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    item_sequence = models.StringField(initial="12132312134312134312134312132312132312134312")

    # fields to store summary statistics
    total_correct = models.IntegerField()
    total_trials = models.IntegerField()
    avg_response_time = models.FloatField()
    false_positives = models.IntegerField()  # Count of incorrect presses
    false_negatives = models.IntegerField()  # Count of missed presses

    final_score = models.CurrencyField()

def set_payoffs(group):
    """Calculate payoffs using the penalty scheme and store them in player.payoff."""
    for player in group.get_players():
        trials = Trial.filter(player=player)
        false_positives = sum(1 for t in trials if t.false_positive)
        false_negatives = sum(1 for t in trials if t.false_negative)

        # Compute payoff using cu()
        starting_points = cu(40)  # Start with 40 currency units
        penalty = cu((false_negatives * 2) + (false_positives * 1))  # Calculate penalty
        final_score = max(cu(12), starting_points - penalty)  # Prevents going below 12

        # Store in oTree's built-in `payoff` field
        player.payoff = final_score

class Trial(ExtraModel):
    """Stores each trial separately instead of using a string."""
    player = models.Link(Player)
    round_number = models.IntegerField()
    item_shown = models.IntegerField()
    player_response = models.BooleanField()
    is_correct = models.BooleanField()
    response_time = models.FloatField()
    false_positive = models.BooleanField()  # Pressed when not needed
    false_negative = models.BooleanField()  # Did not press when required

class Instructions(Page):
    @staticmethod
    def vars_for_template(player):
        trials = Trial.filter(player=player)
        sequence = player.item_sequence
        n_back = C.N

        return {
            "length": len(sequence),
            "n_back": n_back,
            "trial_duration": C.trialDuration,
            "starting_points": 40,
            "penalty_miss": 2,
            "penalty_wrong_press": 1,
            "penalty_spam": 28
        }


class NBack(Page):
    @staticmethod
    def js_vars(player):
        return {
            "item_sequence": [int(i) for i in player.item_sequence],
            "target_responses": [
                int(player.item_sequence[int(i)] == player.item_sequence[int(i) - C.N] and int(i) >= C.N)
                for i in range(len(player.item_sequence))
            ],
        }

    @staticmethod
    def live_method(player, data):
        """Receives data from JavaScript and stores trial results."""
        if "end" in data:
            return {"finished": True}

        # Store the trial data
        Trial.create(
            player=player,
            round_number=data["round_number"],
            item_shown=int(player.item_sequence[data["round_number"]]),
            player_response=data["response"] == 1,  # True if spacebar pressed
            is_correct=data["is_correct"] == 1,  # True if correct response
            response_time=data.get("response_time", None),  # Stores reaction time
            false_positive=data["false_positive"] == 1,  # Store false positive
            false_negative=data["false_negative"] == 1   # Store false negative
        )

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

class Results(Page):
    @staticmethod
    def vars_for_template(player):
        trials = Trial.filter(player=player)
        sequence = player.item_sequence
        n_back = C.N

        # Count the expected N-back matches
        total_trials = sum(1 for i in range(n_back, len(sequence)) if sequence[i] == sequence[i - n_back])

        # Filter trials where responses were expected
        expected_trials = [t for t in trials if
                           t.round_number >= n_back and sequence[t.round_number] == sequence[t.round_number - n_back]]

        total_correct = sum(1 for t in expected_trials if t.is_correct)
        false_positives = sum(1 for t in trials if t.false_positive)
        false_negatives = sum(1 for t in trials if t.false_negative)

        return {
            "correct_count": total_correct,
            "total_count": total_trials,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "payoff": player.payoff,  # Fetching calculated payoff
        }

    @staticmethod
    def before_next_page(player, timeout_happened):
        """Ensure total_trials is computed using the correct logic."""
        trials = Trial.filter(player=player)
        sequence = player.item_sequence  # Get the sequence string
        n_back = C.N  # Use the configured N value

        # ✅ Compute total expected trials directly from item_sequence
        total_trials = sum(1 for i in range(n_back, len(sequence)) if sequence[i] == sequence[i - n_back])

        # ✅ Filter only recorded trials where a response was required
        expected_trials = [t for t in trials if t.round_number >= n_back and sequence[t.round_number] == sequence[t.round_number - n_back]]

        total_correct = sum(1 for t in expected_trials if t.is_correct)
        false_positives = sum(1 for t in trials if t.false_positive)
        false_negatives = sum(1 for t in trials if t.false_negative)

        avg_response_time = (
            sum(t.response_time for t in expected_trials if t.response_time is not None) / total_trials
            if total_trials > 0 else 0
        )

        # ✅ Store the correct values in the Player table
        player.total_correct = total_correct
        player.total_trials = total_trials  # Correct N-back trials count
        player.avg_response_time = avg_response_time
        player.false_positives = false_positives
        player.false_negatives = false_negatives


page_sequence = [Instructions, NBack, ResultsWaitPage, Results]
