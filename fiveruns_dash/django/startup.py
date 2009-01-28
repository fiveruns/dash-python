import logging, django, sys
from django.core.exceptions import ImproperlyConfigured
from django.core.management.commands.runserver import Command
import fiveruns_dash, aspects
from fiveruns_dash.metrics import Calculation

logger = logging.getLogger('fiveruns_dash.django')

configuration = None

def start(settings):
    """
    Since there's no easy way to detect if autoreloading will be used when the server
    starts, we wrap ``django.core.management.commands.runserver.Command`` to check
    the options directly.

    Note: if ``manage.py runserver`` is not used to start the server, this approach
          may not work.

    ``settings``
      a module that defines:
        ``DASH_TOKEN``
          Required; application token for this application
        ``DASH_RECIPES``
          Optional; a list/tuple of additional recipes to add to the configuration
        ``DASH_LOGGER_LEVEL``
          Optional; shorthand for ``logging.getLogger('fiveruns_dash').setLevel()``
          By default, this is ``logging.WARN``
        ``DASH_CONFIGURE_WITH``
          Optional; function to pass configuration object for manual modification

    """
    global configuration
    if not hasattr(settings, 'DASH_TOKEN'):
        raise ImproperlyConfigured, 'Error configuring fiveruns_dash.django. Is DASH_TOKEN defined?'
    if hasattr(settings, 'DASH_LOGGER_LEVEL'):
      logging.getLogger('fiveruns_dash').setLevel(settings.DASH_LOGGER_LEVEL)
    configuration = fiveruns_dash.configure(app_token = settings.DASH_TOKEN)
    for recipe in _builtin_recipes():
        configuration.add_recipe(recipe)
    _add_framework_metadata()
    if hasattr(settings, 'DASH_RECIPES'):
        logger.info("Adding additional recipes from settings.py")
        for recipe in settings.DASH_RECIPES:
            configuration.add_recipe(*list(recipe))
    if hasattr(settings, 'DASH_CONFIGURE_WITH'):
      settings.DASH_CONFIGURE_WITH(configure)
    aspects.with_wrap(_start_unless_reloading, Command.handle)

def _start_unless_reloading(*args, **options):
    if options.get('use_reloader', True):
        logger.warn("Not supported when using autoreloading (use --noreload)")
        yield aspects.proceed
    else:
        logger.debug("Activating...")
        thread = _start()
        try:
            yield aspects.proceed
        except:
            thread.stop()
            raise

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

    # Metric: orm_util
    # TODO: Wrap higher up?
    from django.db.models.sql import BaseQuery
    recipe.time('orm_time', 'django.db ORM Time', wrap = BaseQuery.execute_sql)

    # Metric: db_util
    from django.core.exceptions import ImproperlyConfigured
    try:
        import django.db
        # Get the cursor class
        cursor_names = ('CursorWrapper', 'FormatStylePlaceholderCursor')
        for name in cursor_names:
            if hasattr(django.db.backend, name):
                cursor_class = getattr(django.db.backend, name)
                recipe.time('db_time', 'django.db Backend Time', wrap = cursor_class.execute)
                break
        else:
            logger.error("Could not find Django DB backend cursor, skipping Database Utilization metric")
    except ImproperlyConfigured:
        logger.warn("Could not find Django DB backend, skipping Database Utilization metric")
        pass

    from django.core.handlers.base import BaseHandler

    # Metric: requests
    recipe.counter('requests', "Requests", wrap = BaseHandler.get_response)

    # Metric: response_time
    recipe.time('response_time', "Response Time", wrap = BaseHandler.get_response)

    recipe.percentage('orm_util', "django.db ORM Utilization",
                      calculation = Calculation(lambda orm, total: (orm / total) * 100.0, 'orm_time', 'response_time'))

    recipe.percentage('db_util', "django.db Backend Utilization",
                      calculation = Calculation(lambda db, total: (db / total) * 100.0, 'db_time', 'response_time'))

    yield recipe

def _add_framework_metadata():
    data = configuration.extra_payload_data.get('info', {})
    data.update({
        'framework_name': 'django',
        'framework_version': django.get_version()
        })
    configuration.extra_payload_data['info'] = data
