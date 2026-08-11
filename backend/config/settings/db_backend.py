# Install PyMySQL as MySQLdb so Django's mysql backend works without mysqlclient.
# Safe no-op until USE_MYSQL=True / production MySQL is configured (Phase 3).
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    pass
