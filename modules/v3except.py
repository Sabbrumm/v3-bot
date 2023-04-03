class V3Exception(Exception):
    USER_NOT_IN_DB = 0
    POST_NOT_IN_DB = 1
    DATABASE_EXCEPTION = 2
    @property
    def extra(self):
        return self._extra

    @property
    def code(self):
        return self._code

    def __init__(self, code, extra=None):
        self._code = code
        self._extra = extra
        if extra is not None:
            extrastr = str(extra)
        else:
            extrastr = ''



        if code == V3Exception.USER_NOT_IN_DB:
            super(V3Exception, self).__init__(
                f"User not in database. Error extra: {extrastr}")

        elif code == V3Exception.POST_NOT_IN_DB:
            super(V3Exception, self).__init__(
                f"Post not in database. Error extra: {extrastr}")

        elif code == V3Exception.DATABASE_EXCEPTION:
            super(V3Exception, self).__init__(
                f"Exception in SQLite3 database. Error extra: {extrastr}")

