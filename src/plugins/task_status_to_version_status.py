"""
When a Version status is changed, update the linked Task to the same Status.

Ported from TheThirdFloor/pipeline at tag 5.24.1

"""


import logging
import handler_config

PLUGIN_NAME = 'task_status_to_version_status'


def registerCallbacks(reg):
    config = handler_config.Config(handler_config.getConfigPath())
    script_name = config.get_api_script_name(PLUGIN_NAME)
    script_key = config.get_api_script_key(PLUGIN_NAME)

    # Register the event to the daemon
    event_filter = {
        'Shotgun_Version_Change': ['sg_status_list'],
    }

    # Register the event to the daemon
    reg.registerCallback(script_name, script_key,
                         task_status_to_version_status, event_filter, None)


def task_status_to_version_status(sg, logger, event, args):
    """Flip downstream Tasks to 'rdy' if all of their upstream Tasks are 'cmpt'"""
    
    # Check that the event is linked to something we can process
    if 'new_value' not in event['meta'] or event['entity'] is None:
        return
    
    # Check to see that Tasks have the new status we want to flip to
    new_value = event['meta']['new_value']
    status_schema = sg.schema_field_read('Task', 'sg_status_list', project_entity = event['project'])
    
    valid_values = []
    try:
        valid_values = status_schema['sg_status_list']['properties']['valid_values']['value']
    except:
        logger.debug('Unable to read schema. Skipping...')
        pass
    
    if not new_value in valid_values:
        logger.debug("New value %s not in Task status list. Skipping..." % new_value)
        return
    else:
        new_value_nice = status_schema['sg_status_list']['properties']['display_values']['value'][new_value]
    
    # Find the Version's Task
    filters = [
        ['id', 'is', event['entity']['id']]
    ]
    fields = ['sg_task']
    version = sg.find_one('Version', filters, fields)
    
    if not version:
        logger.debug('Linked version no longer exists. Skipping...')
        return
    
    task = version.get('sg_task')
    if not task:
        logger.debug('Version not linked to a task. Skipping...')
        return
    else:
        logger.info('Updating Status on Task %s to %s (%s)' % (task['id'],new_value_nice, new_value))
        sg.update('Task', task['id'], {'sg_status_list': new_value})


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
    event_id = 10870189

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
    task_status_to_version_status(sg, logger, event, None)

if __name__ == "__main__":
    test()
        
        
        
        
        