"""
When a Version status is changed, update the linked Task to the same Status.

Ported from TheThirdFloor/pipeline at tag 5.24.1

"""


SCRIPT_NAME = ''
SCRIPT_KEY  = ''
SERVER_URL  = ''


def registerCallbacks(reg):
    matchEvents = {
        'Shotgun_Version_Change': ['sg_status_list'],
    }
    
    reg.registerCallback(SCRIPT_NAME, SCRIPT_KEY, flipTask, matchEvents, None)


def flipTask(sg, logger, event, args):
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


if __name__ == "__main__":
    import logging
    from shotgun_api3 import Shotgun
    
    logging.basicConfig()
    logger = logging.getLogger("status_flip_task_from_version")
    logger.setLevel(logging.DEBUG)

    sg = Shotgun(SERVER_URL, SCRIPT_NAME, SCRIPT_KEY)
    # Find a relevant event
    # Version
    eventsIDs = [3121814, 3122028] # Version
    
    events = []
    
    for eventID in eventsIDs:
        filters = [
                 ['id', 'is', eventID]
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
        events.append(event)
    
    for event in events:
        flipTask(sg, logger, event, None)
        
        
        
        
        