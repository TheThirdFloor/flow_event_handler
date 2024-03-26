"""
When a Project is flipped to "Wrap", remove all Artists and Supervisors
from the project.

Ported from TheThirdFloor/pipeline at tag 5.24.1

"""


SCRIPT_NAME = ''
SCRIPT_KEY  = ''
SERVER_URL  = ''


def registerCallbacks(reg):
    eventsFilter = {
        'Shotgun_Project_Change': ['sg_status']
    }
    
    # Register the event to the daemon
    reg.registerCallback(SCRIPT_NAME, SCRIPT_KEY, cleanup_project,
                         eventsFilter, None)
    reg.logger.setLevel(logging.INFO)


def cleanup_project(sg, logger, event, args):

    if not event['entity']:
        return

    logger.info("Processing Event %s" % event['id'])
       
    # Store the value of the new status
    new_status = event['meta']['new_value']

    if not new_status == "Wrap":
        logger.info("Project status is not Wrap")
        return  
    
    # Store the dict that represents the project
    wrap_project = event['entity']

    # Define filters to find users with Artist or Supervisor permissions
    artist_filter = [
        ['code', 'is', 'artist'],
    ]
    artist_permission = sg.find_one("PermissionRuleSet", artist_filter)

    supe_filter = [
        ['code', 'is', 'supervisor'],
    ]
    supe_permission = sg.find_one("PermissionRuleSet", supe_filter)
    
          
    team_fields = ['name', 'projects']
    # Filter to find both Artists and Supervisors within a wrapped project
    team_filters = [
        ['projects', 'in', wrap_project],
        {
            "filter_operator" : "any",
            "filters" : [
                ['permission_rule_set', 'is', artist_permission],
                ['permission_rule_set', 'is', supe_permission]
            ]
        }
    ]

    # Query that finds all Artists and Supes that are in the project
    team_members = sg.find('HumanUser', team_filters, team_fields)
       
    # Loops through members of project, checks to see if any member project IDs match wrapped project,
    # and creates updated list of projects.        
    for member in team_members:
        test_member_projects = member['projects']
        updated_member_projects = []
        for project in test_member_projects:
            if not project['id'] == wrap_project['id']:
                updated_member_projects.append(project)
                        
        new_data = dict()
        new_data['projects'] = updated_member_projects 

        logger.info("Updating HumanUser %s[%s] with data %s" % (member['name'], member['id'], new_data))
        sg.update("HumanUser", member['id'], new_data)




if __name__ == "__main__":
    import logging
    from shotgun_api3 import Shotgun
    
    logging.basicConfig()
    logger = logging.getLogger("project_wrap_cleanup")
    logger.setLevel(logging.DEBUG)
    
    sg = Shotgun(SERVER_URL, SCRIPT_NAME, SCRIPT_KEY)
    
    # A single event
    event_id = 7697139

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
    cleanup_project(sg, logger, event, None)