from __future__ import annotations

import dataclasses
import datetime
import re
from collections.abc import Iterable
from typing import Optional

from shotgun_api3 import Shotgun

LogEntry = dict[str, object]

_START = {
    '',
}

_IDLE = {
    'wtg',
    'rdy',
    'hld',
}

_WORK = {
    'ip',
}

_REVIEW = {
    'rev',
}

_DONE = {
    'cmpt',
    'dply',
    'omt',
}

_LOG_TYPE = 'EventLogEntry'
_TICKET_TYPE = 'Ticket'
_EVENT_TYPE_FILTER = 'Shotgun_Ticket_Change'
_EVENT_SUMMARY = 'description'
_EVENT_CREATED = 'created_at'
_EVENT_LINK = 'entity'
_EVENT_TYPE = 'event_type'
_EVENT_ATTR = 'attribute_name'
_EVENT_ATTR_FILTER = 'sg_status_list'

_SUMMARY_ATTR_TO_TICKET_FIELD = {
    'start_time': 'sg_start_date',
    'aggregate_time_idle': 'sg_aggregate_idle_time',
    'aggregate_time_reviewed': 'sg_aggregate_review_time',
    'aggregate_time_worked': 'sg_aggregate_work_time',
    'aggregate_total_time': 'sg_aggregate_total_time',
    'completion_time': 'sg_end_date',
}


_DS_PROJECT_ID = 1482
_DS_PROJECT_FILTER = ('project', 'is', {'id': _DS_PROJECT_ID, 'type': 'Project',})


def get_ticket_by_id(
    id_: int,
    sg: Shotgun,
) -> dict:
    entity_type = _TICKET_TYPE
    filters = [
        _DS_PROJECT_FILTER,
        ['id', 'is', id_],
    ]
    ticket = sg.find_one(entity_type, filters)
    if not ticket:
        raise RuntimeError
    return ticket


def get_logs_from_ticket(
    ticket: dict,
    project: dict, 
    sg: Shotgun,
) -> list[dict]:
    entity_type = _LOG_TYPE
    filters = [
        ['project', 'is', project],
        [_EVENT_LINK, 'is', ticket],
        [_EVENT_TYPE, 'is', _EVENT_TYPE_FILTER],
        [_EVENT_ATTR, 'is', _EVENT_ATTR_FILTER],
    ]
    fields = [
        _EVENT_SUMMARY,
        _EVENT_CREATED,
    ]
    log_entries = sg.find(entity_type, filters, fields=fields)

    def key(log_entry: dict) -> int:
        created_at = log_entry[_EVENT_CREATED]
        return created_at.timestamp()

    log_entries.sort(key=key)
    return log_entries


_LOG_DESC_PATTERN = r'^.*"(?P<from>[a-z]*)" to "(?P<to>[a-z]*)".*$'
_log_desc_regex = re.compile(_LOG_DESC_PATTERN)


def get_status_transition_from_log_description(desc: str) -> tuple[str, str]:
    match_ = _log_desc_regex.match(desc)
    if not match_:
        raise RuntimeError
    return match_.groupdict()['from'], match_.groupdict()['to']


def update_ticket_from_summary(
    ticket: dict,
    summary: LogSummary,
    sg: Shotgun,
) -> None:
    data = {}
    for attr, field in _SUMMARY_ATTR_TO_TICKET_FIELD.items():
        value = getattr(summary, attr, None)
        if not value:
            continue
        if isinstance(value, datetime.datetime):
            value: datetime.datetime
            value = value.isoformat()
        elif isinstance(value, datetime.timedelta):
            # so... duration fields are f*%()'d on SG. There's no logic to them
            # what so ever, so I had to come up with a "fudge" factor that co-relates
            # 1.0 when passed to the field with the duration it displays, 0.0017.
            # I then multiply the actual days by that fudge. Idiotic.
            value: datetime.timedelta
            days = float(value.total_seconds()) / 60.0 / 60.0 / 24.0
            sg_fudge = 1.0 / 0.0017
            fudged_days = days * sg_fudge
            value = fudged_days
        data[field] = value
    ticket_id = ticket['id']
    sg.update(_TICKET_TYPE, ticket_id, data)
    

@dataclasses.dataclass
class LogSummary:

    start_time: Optional[datetime.datetime] = None
    aggregate_time_idle: datetime.timedelta = dataclasses.field(
        default_factory=datetime.timedelta
    )
    aggregate_time_worked: datetime.timedelta = dataclasses.field(
        default_factory=datetime.timedelta
    )
    aggregate_time_reviewed: datetime.timedelta = dataclasses.field(
        default_factory=datetime.timedelta
    )
    aggregate_total_time: datetime.timedelta = dataclasses.field(
        default_factory=datetime.timedelta
    )
    completion_time: Optional[datetime.datetime] = None

    @classmethod
    def aggregate(cls, log_entries: Iterable[LogEntry]) -> LogSummary:
        summary = LogSummary()
        last = None
        for log_entry in log_entries:
            desc = log_entry[_EVENT_SUMMARY]
            at = log_entry[_EVENT_CREATED]
            from_, to = get_status_transition_from_log_description(desc)
            starting = from_ in _START
            from_idle = from_ in _IDLE
            from_review = from_ in _REVIEW
            from_work = from_ in _WORK
            from_completed = from_ in _DONE
            completing = to in _DONE
            if last:
                delta = at - last
            if starting:
                summary.start_time = at
            if from_idle:
                if summary.aggregate_time_idle:
                    summary.aggregate_time_idle += delta
                else:
                    summary.aggregate_time_idle = delta
            elif from_review:
                if summary.aggregate_time_reviewed:
                    summary.aggregate_time_reviewed += delta
                else:
                    summary.aggregate_time_reviewed = delta
            elif from_work:
                if summary.aggregate_time_worked:
                    summary.aggregate_time_worked += delta
                else:
                    summary.aggregate_time_worked = delta
            elif from_completed:
                # someone restarted the ticket, we'll assume idle while in the
                # completed state
                if summary.aggregate_time_idle:
                    summary.aggregate_time_idle += delta
                else:
                    summary.aggregate_time_idle = delta
            if completing:
                summary.completion_time = at
                summary.aggregate_total_time = (
                    summary.aggregate_time_idle
                    + summary.aggregate_time_worked
                    + summary.aggregate_time_reviewed
                )
            last = at
        return summary
