import logging
from django.core.exceptions import ImproperlyConfigured
from django.core.management.commands.runserver import Command
import fiveruns_dash, aspects

logger = logging.getLogger('fiveruns_dash.django')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

configuration = None

def start(settings):
    """
    Since there's no easy way to detect if autoreloading will be used when the server
    starts, we wrap ``django.core.management.commands.runserver.Command`` to check
    the options directly.

    Note: if ``manage.py runserver`` is not used to start the server, this approach
        may not work.

    settings -- a module that defines ``APP_TOKEN`` and an optional ``configure`` function
    """
    global configuration
    if not hasattr(settings, 'DASH_TOKEN'):
        raise ImproperlyConfigured, 'Error configuring fiveruns_dash.django. Is DASH_TOKEN defined?'
    configuration = fiveruns_dash.configure(app_token = settings.DASH_TOKEN)
    for recipe in _builtin_recipes():
        configuration.add_recipe(recipe)
    if hasattr(settings, 'DASH_RECIPES'):
        logger.info("Adding additional recipes from settings.py")
        for recipe in settings.DASH_RECIPES:
            configuration.add_recipe(*list(recipe))
    aspects.with_wrap(_start_unless_reloading, Command.handle)

def _start_unless_reloading(*args, **options):
    if options.get('use_reloader', True):
        logger.warn("FiveRuns Dash not supported when using autoreloading (use --noreload to activate)")
    else:
        logger.debug("Not using autoreloading; activating FiveRuns Dash")
        _start()
    yield aspects.proceed

def _start():
    if configuration:
        logger.debug("Found configuration")
        return fiveruns_dash.start(configuration)
    else:
        logger.error("Could not find configuration")
        return False

def _builtin_recipes():
    """
    Define and yield the recipes for Django
    """
    recipe = fiveruns_dash.recipe('django', 'http://dash.fiveruns.com')
    from django.db.models import Model
    recipe.time('saves', 'Calls to Model.save', wrap = Model.save)
    yield recipe
