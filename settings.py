from os import environ

SESSION_CONFIGS = [
    dict(
        name='twoback',  # Your existing task
        display_name="Two-Back Task",
        num_demo_participants=1,
        app_sequence=['Two_Back']
    ),
    dict(
        name='three_back',  # New task
        display_name="Three-Back Task",
        num_demo_participants=1,
        app_sequence=['Three_Back']
    ),
    dict(
        name='memory_words',  # New task
        display_name="Memory Words Task",
        num_demo_participants=1,
        app_sequence=['Memory_Task']
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '2609276517330'
