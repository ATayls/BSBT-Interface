class DevConfig(object):
    SECRET_KEY = 'your_secret_key'
    CONFIG_TYPE = 'Development'
    WEBSITE_TITLE = 'BSBT-Interface'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI='sqlite:///../comparative_judgements.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALL_CLUSTERS_KNOWN = True
    USE_PROBABILITIES = True


class ProdConfig(object):
    CONFIG_TYPE = 'Production'
    DB = None
