"""
When the user is set to Disabled, remove all linked Projects.

Ported from TheThirdFloor/pipeline at tag 5.24.1

"""


SCRIPT_NAME = ''
SCRIPT_KEY  = ''
SERVER_URL  = ''


def registerCallbacks(reg):
    eventsFilter = {
        'Shotgun_HumanUser_Change': ['sg_status_list']
    }
    
    # Register the event to the daemon
    reg.registerCallback(SCRIPT_NAME, SCRIPT_KEY, cleanup_user, \
                         eventsFilter, None)
    reg.logger.setLevel(logging.INFO)


def cleanup_user(sg, logger, event, args):

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


if __name__ == "__main__":

    import logging
    from shotgun_api3 import Shotgun
    
    logging.basicConfig()
    logger = logging.getLogger("user_cleanup")
    logger.setLevel(logging.DEBUG)
    
    sg = Shotgun(SERVER_URL, SCRIPT_NAME, SCRIPT_KEY)
    
    # A single event
    event_id = 7926994

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
    cleanup_user(sg, logger, event, None)