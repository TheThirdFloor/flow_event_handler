"""
For detailed information please see

http://shotgunsoftware.github.com/shotgunEvents/api.html
Testing
Bugfix
"""

import flow_event_handler.src.handler_config as handler_config

PLUGIN_NAME = 'log_args'

def registerCallbacks(reg):
    """Register all necessary or appropriate callbacks for this plugin."""

    # Specify who should recieve email notifications when they are sent out.
    #
    #reg.setEmails('me@mydomain.com')

    # Use a preconfigured logging.Logger object to report info to log file or
    # email. By default error and critical messages will be reported via email
    # and logged to file, all other levels are logged to file.
    #
    #reg.logger.debug('Loading logArgs plugin.')

    # Register a callback to into the event processing system.
    #
    # Arguments:
    # - Shotgun script name
    # - Shotgun script key
    # - Callable
    # - Argument to pass through to the callable
    # - A filter to match events to so the callable is only invoked when
    #   appropriate
    #

    config = scripts_config.Config()
    script_name = config.get_script_name(PLUGIN_NAME)
    script_key = config.get_script_key(PLUGIN_NAME)
    #eventFilter = {'Shotgun_Task_Change': ['sg_status_list']}
    eventFilter = None
    reg.registerCallback(script_name, script_key, logArgs, eventFilter, None)

    # Set the logging level for this particular plugin. Let error and above
    # messages through but block info and lower. This is particularly usefull
    # for enabling and disabling debugging on a per plugin basis.
    reg.logger.setLevel(logging.INFO)


def log_args(sg, logger, event, args):
    """
    A callback that logs its arguments.

    @param sg: Shotgun instance.
    @param logger: A preconfigured Python logging.Logger object
    @param event: A Shotgun event.
    @param args: The args passed in at the registerCallback call.
    """

    logger.info("%s" % str(event))


def test():

    import logging
    from shotgun_api3 import Shotgun

    logging.basicConfig()
    logger = logging.getLogger(PLUGIN_NAME)
    logger.setLevel(logging.DEBUG)

    config = handler_config.Config(handler_config.getConfigPath())
    server_url = config.server_url
    script_name = config.get_api_script_name(PLUGIN_NAME)
    script_key = config.get_api_script_key(PLUGIN_NAME)

    sg = Shotgun(server_url, script_name, script_key)

    # A single event
    event_id = 10869366

    filters = [
        ['id', 'is', event_id]
    ]
    fields = [
        'entity',
        'user',
        'meta',
        'project',
        'attribute_name',
        'event_type',
        'created_at',
        'user',
        'session_uuid',
        'type',
    ]

    event = sg.find_one('EventLogEntry', filters, fields)
    log_args(sg, logger, event, None)


if __name__ == "__main__":
    test()