from __future__ import annotations

import abc
import typing
import logging
import shotgun_api3


class Callback(typing.Protocol):
    @abc.abstractstaticmethod
    def __call__(
        sg: shotgun_api3.Shotgun,
        logger: logging.Logger,
        event: dict,
        args: object,
    ) -> None:
        pass


class Registrar(typing.Protocol):
    @abc.abstractstaticmethod
    def registerCallback(
        sgScriptName: str,
        sgScriptKey: str,
        callback: Callback,
        matchEvents: dict,
        args: object = None,
        stopOnError: bool = True,
    ) -> None:
        pass

    @abc.abstractstaticmethod
    def setEmails(*emails: object) -> None:
        pass

    @abc.abstractmethod
    def getLogger(self) -> logging.Logger:
        pass

    @abc.abstractproperty
    def logger(self) -> logging.Logger:
        pass
