"""
When the user is set to Disabled, remove all linked Projects.

Ported from TheThirdFloor/pipeline at tag 5.24.1

"""


import logging
import handler_config

PLUGIN_NAME = 'user_cleanup'


def registerCallbacks(reg):
    config = handler_config.Config(handler_config.getConfigPath())
    script_name = config.get_api_script_name(PLUGIN_NAME)
    script_key = config.get_api_script_key(PLUGIN_NAME)

    eventsFilter = {
        'Shotgun_HumanUser_Change': ['sg_status_list']
    }
    
    # Register the event to the daemon
    reg.registerCallback(script_name, script_key, user_cleanup,
                         eventsFilter, None)
    reg.logger.setLevel(logging.INFO)


def user_cleanup(sg, logger, event, args):

    if not event['entity']:
        return

    logger.info("Processing Event %s" % event['id'])
       
    # Store the value of the new status
    new_status = event['meta']['new_value']

    if not new_status == "dis":
        logger.debug("User is not disabled")
        return  
    
    # Store the dict that represents the project
    user = event['entity']
    
    data = dict()
    data['projects'] = list()
    
    sg.update('HumanUser', user['id'], data)


def test():
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
    event_id = 10870149

    filters = [
        ['id', 'is', event_id]
    ]
    fields = ['entity',
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
    user_cleanup(sg, logger, event, None)

if __name__ == "__main__":
    test()
