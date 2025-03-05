from otree.api import *

class C(BaseConstants):
    NAME_IN_URL = 'Memory_Task'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    # Memory Task Constants
    NUM_WORDS = 20  # Total words in the list
    PAYOFF_PER_CORRECT_WORD = cu(2)  # Payoff per correct word
    TIME_LIMIT_MEMORY = 240  # 4 minutes

    # Logic Task Constants
    NUM_QUESTIONS = 7
    TIME_LIMIT_LOGIC = 300  # 5 minutes
    PAYOFF_PER_CORRECT_QUESTION = 0.50  # EUR per correct answer

    # List of correct words
    WORD_LIST = [
        "wool", "fate", "secret", "meaning", "portion",
        "hospital", "silk", "bowl", "fame", "plane",
        "attitude", "religion", "happiness", "knife", "maid",
        "stamp", "passion", "importance", "event", "possession"
    ]

    CORRECT_ANSWERS = [5, 5, 47, 4, 29, 20, "c"]  # Correct answers for auto-scoring

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    # Store each word separately (20 fields for 20 words)
    for i in range(20):
        locals()[f"word_{i}"] = models.StringField(blank=True)
    del i  # Clean up variable

    recall_correct = models.IntegerField(initial=0)  # Count correct words
    total_recalled = models.IntegerField(initial=0)  # Count total words attempted

    # Logic Task Variables
    logic_correct = models.IntegerField(initial=0)
    q1 = models.IntegerField()
    q2 = models.IntegerField()
    q3 = models.IntegerField()
    q4 = models.IntegerField()
    q5 = models.IntegerField()
    q6 = models.IntegerField()
    q7 = models.StringField(choices=["a", "b", "c"], widget=widgets.RadioSelect)

    # Auto-score logic task
    def score_logic(self):
        answers = [self.q1, self.q2, self.q3, self.q4, self.q5, self.q6, self.q7]
        self.logic_correct = sum(1 for i in range(7) if answers[i] == C.CORRECT_ANSWERS[i])
        self.payoff += self.logic_correct * C.PAYOFF_PER_CORRECT_QUESTION

    # Auto-score memory task
    def score_recall(self):
        correct_set = set(word.lower() for word in C.WORD_LIST)

        # Collect all words entered
        recalled_words = [
            getattr(self, f"word_{i}").strip().lower()
            for i in range(20) if getattr(self, f"word_{i}")
        ]

        # Count correct words
        self.recall_correct = sum(1 for word in recalled_words if word in correct_set)
        self.total_recalled = len(recalled_words)

        # Calculate payoff
        self.payoff += self.recall_correct * C.PAYOFF_PER_CORRECT_WORD

# -------------------- PAGES -------------------- #

class MemoryInstructions(Page):
    timeout_seconds = C.TIME_LIMIT_MEMORY

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            word_list=C.WORD_LIST,
            num_words=C.NUM_WORDS,
            time_limit=C.TIME_LIMIT_MEMORY // 60,
            payoff_per_correct=C.PAYOFF_PER_CORRECT_WORD
        )

class LogicQuestions(Page):
    form_model = 'player'
    form_fields = ['q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7']
    timeout_seconds = C.TIME_LIMIT_LOGIC

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.score_logic()

    @staticmethod
    def vars_for_template(player: Player):
        return dict(time_limit_logic=C.TIME_LIMIT_LOGIC // 60)

class WordRecall(Page):
    form_model = 'player'
    form_fields = [f"word_{i}" for i in range(20)]  # Collect 20 words

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.score_recall()


class Results_Memory(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            recall_correct=player.recall_correct,
            total_recalled=player.total_recalled,
            earnings=player.recall_correct * C.PAYOFF_PER_CORRECT_WORD
        )

page_sequence = [MemoryInstructions, LogicQuestions, WordRecall, Results_Memory]
