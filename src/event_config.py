import json
import sys
from pathlib import Path
from typing import Optional

CONFIG_FILENAME = "config.json"

class EventConfigError(Exception):
    pass

class Config(object):
    def __init__(self, path):
        self._path = path
        self._data = None
        self.read(path)

    @property
    def path(self):
        return self._path

    @property
    def data(self) -> dict:
        return self._data

    @property
    def flow(self) -> dict:
        """
        Flow (Shotgun) connection options for the daemon

        """

        return self._data.get('flow', {})

    @property
    def service(self) -> dict:
        """
        General daemon operational settings

        """

        return self._data.get('service', {})

    @property
    def plugins(self) -> dict:
        """
        Plugin related settings

        """

        return self._data.get('plugins', {})

    @property
    def email(self) -> dict:
        """
        Email notification settings. These are used for error reporting because
        we figured you wouldn't constantly be tailing the log and would rather
        have an active notification system.

        Any error above level 40 (ERROR) will be reported via email.

        All of these value must be provided for there to be alerts sent out.

        """

        return self._data.get('email', {})

    @property
    def log_dir(self) -> Path:
        """
        The path where to put log files

        """

        config_value = self.service.get('log_dir')
        log_dir = Path(config_value)
        return log_dir.resolve()

    @property
    def service_name(self) -> str:

        name = self.service.get('name')
        if not name:
            raise EventConfigError("Service Name Not Defined")
        elif " " in name:
            msg = "Service Name cannot contain spaces: {name}"
            msg = msg.format(name=name)
            raise EventConfigError(msg)

        return name

    @property
    def conn_retry_sleep(self) -> int:
        """
        If the connection to shotgun fails, number of seconds to wait until we
        retry. This allows for occasional network hiccups, server restarts,
        application maintenance, etc.

        """

        return self.service.get('conn_retry_sleep')

    @property
    def max_conn_retries(self) -> int:
        """
        Number of times to retry connection before logging an error level
        message (which sends an email in the default configuration)

        """

        return self.service.get('max_conn_retries')

    @property
    def fetch_interval(self) -> int:
        """
        Number of seconds to wait before requesting new events after each batch
        of events is done processing

        """

        return self.service.get('fetch_interval')

    @property
    def use_session_uuid(self) -> bool:
        """
        Sets the session_uuid from every event in the Shotgun instance to
        propagate in any events generated by plugins. This will allow the
        Shotgun UI to display updates that occur as a result of a plugin.

        Shotgun server v2.3+ required.
        Shotgun API v3.0.5+ required

        """

        return self.flow.get('use_session_uuid')

    def read(self, path) -> None:
        with open(path, "r+") as json_f:
            self._data = json.load(json_f)

    def getShotgunURL(self) -> str:
        """
        The Shotgun url the event processing framework should connect to.

        """

        return self.flow.get('server')

    def getEngineScriptName(self) -> str:
        """
        The Shotgun script name the framework should connect with.

        """

        return self.flow.get('script_name')

    def getEngineScriptKey(self) -> str:
        """
        The Shotgun api key the framework should connect with. You'll need to
        replace this random useless key with the one corresponding to the
        script you've setup.

        """

        return self.flow.get('script_key')

    def getEngineProxyServer(self) -> Optional[str]:
        """
        The address of the proxy server used to connect to your Shotgun server
        in the format 111.222.333.444:8080. Leave this empty if you don't have
        a proxy server.

        """

        proxy_server = self.flow.get('proxy_server')
        if proxy_server == "":
            proxy_server = None
        return proxy_server

    def getEventIdFile(self) -> str:
        """
        The eventIdFile is the location where the daemon will store the id of
        the last processed event. This will allow the daemon to pick up where
        it left off when last shutdown thus not missing any events. If you want
        to ignore any events since last daemon shutdown, remove this file before
        daemon startup and the daemon will process only new events created after
        startup.

        """

        config_value = self.service.get('event_id_filename')
        filename = config_value.format(service_name=self.service_name)
        return str(self.log_dir / filename).replace('\\', '/')

    def getEnginePIDFile(self) -> str:
        """
        The pidFile is the location where the daemon will store its process id.
        If this file is removed while the daemon is running, it will shutdown
        cleanly after the next pass through the event processing loop.
        """

        config_value = self.service.get('pid_filename')
        filename = config_value.format(service_name=self.service_name)
        return str(self.log_dir / filename).replace('\\', '/')

    def getPluginPaths(self) -> list:
        """
        List of paths where the framework should look for plugins to load

        """

        paths = self.plugins.get('paths', [])
        abs_paths = [Path(path).resolve() for path in paths]
        return [str(path).replace('\\', '/') for path in abs_paths]

    def getSMTPServer(self) -> str:
        """
        # The server that should be used for smtp connections.

        """

        return self.email.get('server')

    def getSMTPPort(self) -> int:
        """
        An alternate port such as 587 for GMail TLS SMTP

        """

        return self.email.get('port', 25)

    def getFromAddr(self) -> str:
        """
        The from address that should be used in emails

        """

        return self.email.get('from')

    def getToAddrs(self) -> list:
        """
        List of email addresses to whom these alerts should be sent

        """
        return self.email.get('to', [])

    def getEmailSubject(self) -> str:
        """
        An email subject prefix that can be used by mail clients to help sort
        out alerts sent by the Shotgun event framework.

        Can include {server}, {script_name}, and/or {service_name} for string
        substitution

        """

        config_value = self.email.get("subject")
        subject = config_value.format(
            server = self.getShotgunURL(),
            script_name = self.getEngineScriptName(),
            service_name=self.service_name
        )
        return subject

    def getEmailUsername(self) -> str:
        """
        Username credentials for the smtp connection

        """

        return self.email.get('username')

    def getEmailPassword(self) -> str:
        """
        Password credentials for the smtp connection

        """

        return self.email.get('password')

    def getSecureSMTP(self) -> bool:
        """
        Use TLS for SMPT email connections

        """

        return self.email.get('use_tls', False)

    def getLogMode(self) -> int:
        """
        The logging mode to operate in:
        0 = all log message in the main log file
        1 = one main file for the engine, one file per plugin

        """

        return self.service.get("log_mode")

    def getLogLevel(self) -> int:
        """
        The level of logging that should be sent to the log file. This value
        is only applicable to the main dispatching engine and can be overriden
        on a per plugin basis. This value is passed to the logging library.
        Any positive integer value is valid but most common cases are:
            10 - Debug
            20 - Info
            30 - Warnings
            40 - Error
            50 - Critical

        """

        return self.service.get("log_level")

    def getMaxEventBatchSize(self) -> int:
        """
        Maimum number of events to fetch at once.

        """

        return self.service.get("max_event_batch_size", 500)

    def getLogFile(self, filename=None) -> str:
        """
        The name of the daemon log file. The setup is for 10 log files that
        rotate every night at midnight

        Can include {service_name} for string substitution

        Args:
            filename (str): Optional file name, will use value from config if
                            not provided.

        """

        if filename is None:
            filename = self.service.get("log_filename")
        filename = filename.format(service_name=self.service_name)
        return str(self.log_dir / filename).replace('\\', '/')

    def getTimingLogFile(self) -> Optional[str]:
        """
        Timing logging is a separate log file that will log timing information
        regarding event dispatching and processing run time. This is to help
        diagnose which plugins are taking the most amount of time and where
        any potential queue processing delay might be coming from. Valid
        values are `on` to enable or anything else to disable.

        """

        use_log = self.service.get('timing_log')

        if use_log == "on":
            return self.getLogFile().rstrip(".log") + ".timing"
        else:
            return None

def getConfigPath():
    """
    Find the config path relative to this file defined by top level constant

    """

    script_path = Path(__file__)
    config_path = script_path.parent / CONFIG_FILENAME
    config_path = config_path.resolve()

    if config_path.exists():
        return str(config_path)
    else:
        msg = "Could not find config path at [{config_path}]"
        msg = msg.format(config_path=config_path.absolute())
        raise EventConfigError(msg)

def test():

    config = Config(getConfigPath())

    attrs_test = [
        'service_name',
        'log_dir',
        'conn_retry_sleep',
        'max_conn_retries',
        'fetch_interval',
    ]

    for attr in attrs_test:
        result = getattr(config, attr)
        msg = "Testing [{attr}]: {result}"
        msg = msg.format(attr=attr, result=result)
        print(msg)

    methods_test = [
        'getShotgunURL',
        'getEngineScriptName',
        'getEngineScriptKey',
        'getEngineProxyServer',
        'getEventIdFile',
        'getEnginePIDFile',
        'getPluginPaths',
        'getSMTPServer',
        'getSMTPPort',
        'getFromAddr',
        'getToAddrs',
        'getEmailSubject',
        'getEmailUsername',
        'getEmailPassword',
        'getSecureSMTP',
        'getLogMode',
        'getLogLevel',
        'getMaxEventBatchSize',
        'getLogFile',
        'getTimingLogFile',
    ]

    for method in methods_test:
        attr = getattr(config, method)
        msg = "Testing [{method}]: {result}"
        msg = msg.format(method=method, result=attr())
        print(msg)



if __name__ == "__main__":
    test()