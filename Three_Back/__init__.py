from otree.api import *

doc = """3-back task"""

class C(BaseConstants):
    NAME_IN_URL = 'Three_Back'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    N = 3 # The "n" in n-back
    trialDuration = 2000  # Time per round (ms)
    intertrialDuration = 1000  # Time between rounds (ms)
    item_styles = ["glyphicon-tree-deciduous", "glyphicon-fire", "glyphicon-tint", "glyphicon-certificate"]


class Subsession(BaseSubsession):
    pass

def creating_session(subsession):
    round_sequences = {
        1: "234424344433211222414424314111314412142221234314",
        2: "143313242414312211442121311324324331221341232243",
        3: "413123114133232423222224241434223244133341411412",
        4: "434134132112321423243331233344213432212343212222",
        5: "131441213431133424244331222333343124324344144242", # Length: 48, 3-back targets: 12
    }
    sequence_for_round = round_sequences.get(subsession.round_number, "")
    print(f"Assigning sequences for round {subsession.round_number}")

    for player in subsession.get_players():
        player.item_sequence = sequence_for_round
        print(f"Player {player.id_in_subsession} sequence: {player.item_sequence}")




class Group(BaseGroup):
    pass

class Player(BasePlayer):
    item_sequence = models.StringField(initial="123123311123221321313233113213221112112231212")

    target_response_times = models.StringField(blank=True) #all response times of target items

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
        starting_points = cu(50)  # Start with 40 currency units
        penalty = cu((false_negatives * 3) + (false_positives * 1))  # Calculate penalty
        final_score = max(cu(0), starting_points - penalty)  # Prevents going below 12

        # Store in oTree's built-in `payoff` field
        player.payoff = final_score

        #Use a 48‐item sequence with exactly 12 actual 3‐back matches (targets).
        # This guarantees more non‐targets (33 in the last 45 positions, plus the first 3) than targets.

        #Payoff scheme: Subtract 3 points for each missed target (false negative),
        # and 1 point for each press on a non‐target (false positive).
        # In that setup, the trivial strategies of “never press” vs. “always press” both lose 36 points,
        # thus end at the same final score.

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
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player):
        trials = Trial.filter(player=player)
        sequence = player.item_sequence
        n_back = C.N

        return {
            "length": len(sequence),
            "n_back": n_back,
            "trial_duration": C.trialDuration/1000,
            "starting_points": 50,
            "penalty_miss": 3,
            "penalty_wrong_press": 1,
            "penalty_spam": 36
        }

class countdown(Page):
    timeout_seconds = 5
    timer_text = 'The task starts in:'


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
            "lost_false_negatives": false_negatives * 3,
            "lost_false_positives": false_positives * 1,
            "payoff": player.payoff,  # Fetching calculated payoff
        }

    @staticmethod
    def before_next_page(player, timeout_happened):
        """Ensure total_trials is computed using the correct logic."""
        trials = Trial.filter(player=player)
        sequence = player.item_sequence  # Get the sequence string
        n_back = C.N  # Use the configured N value

        # Filter and collect response times for target items
        target_response_times = []
        for trial in trials:
            # Check if this is a target item
            if (trial.round_number >= n_back and
                    sequence[trial.round_number] == sequence[trial.round_number - n_back]):
                # Store the response time if not None
                if trial.response_time is not None:
                    target_response_times.append(str(trial.response_time))

        # Store target response times as a comma-separated string
        player.target_response_times = ','.join(target_response_times)

        # Optional: print to verify
        print(f"Target Response Times: {player.target_response_times}")

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


page_sequence = [Instructions, countdown, NBack, ResultsWaitPage, Results]
