from ptbcontrib.postgres_persistence import PostgresPersistence
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from logging import getLogger
from typing import Any

from telegram.ext.dictpersistence import DictPersistence


class MySQLorPostgresPersistence(PostgresPersistence):
    def __init__(
        self,
        url: str = None,
        session: scoped_session = None,
        on_flush: bool = False,
        **kwargs: Any,
    ) -> None:

        if url:
            if not (url.startswith("postgresql://") or url.startswith("mysql://")):
                raise TypeError(
                    f"{url} isn't a valid PostgreSQL or MySQL database URL."
                )
            engine = create_engine(url, client_encoding="utf8")
            self._session = scoped_session(sessionmaker(bind=engine, autoflush=False))

        elif session:

            if not isinstance(session, scoped_session):
                raise TypeError(
                    "session must needs to be `sqlalchemy.orm.scoped_session` object"
                )
            self._session = session

        else:
            raise TypeError("You must need to provide either url or session.")
        self.logger = getLogger(__name__)
        super(DictPersistence, self).__init__(**kwargs)

        self.on_flush = on_flush
        self.__init_database()
        self.__load_database()
