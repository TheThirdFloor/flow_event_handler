from __future__ import annotations

import abc
import logging
import pathlib
import sys
from pprint import pformat
from types import MappingProxyType
from typing import Final, Protocol

import handler_config
from shotgun_api3 import Shotgun

_THIS_PATH = pathlib.Path(__file__)
_INJECT_PATH = _THIS_PATH.parent.as_posix()
if _INJECT_PATH not in set(sys.path):
    sys.path.insert(0, _INJECT_PATH)

from plugins._ticket_log_summaries import protocols, log_summary

_PLUGIN_NAME: Final[str] = 'ticket_log_summaries'
_EVENT_FILTER: Final[MappingProxyType] = MappingProxyType(
    {
        'Shotgun_Ticket_Change': ['sg_status_list'],
    }
)


def registerCallbacks(reg: protocols.Registrar):
    path = handler_config.getConfigPath()
    config = handler_config.Config(path)
    script_name = config.get_api_script_name(_PLUGIN_NAME)
    script_api_key = config.get_api_script_key(_PLUGIN_NAME)

    # Register the event to the daemon
    reg.registerCallback(
        script_name,
        script_api_key,
        summarize_logs,
        _EVENT_FILTER,
        None,
    )


def summarize_logs(
    sg: Shotgun,
    logger: logging.Logger,
    event: dict,
    args: object,
) -> None:
    project = event['project']
    ticket = event['entity']
    ticket_id = ticket['id']
    logger.info(f'Summarizing logs for ticket, {ticket_id}.')
    log_entries = log_summary.get_logs_from_ticket(ticket, project, sg)
    if not log_entries:
        logger.debug(f'No log entries for ticket, {ticket_id}. Early exit.')
        return
    logger.debug(f'Log entries for ticket status:')
    logger.debug(pformat(log_entries))
    summary = log_summary.LogSummary.aggregate(log_entries)
    logger.debug(f'Summary of log entries: {summary}')
    log_summary.update_ticket_from_summary(ticket, summary, sg)
    logger.debug(f'Completed update of ticket {ticket_id}')
