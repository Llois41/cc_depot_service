class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = "secret key"
    MONGO_URI = "mongodb://host.docker.internal:27018/CC_Projekt"
    STOCK_URI = "http://host.docker.internal:3000"

class ProductionConfig(Config):
    pass


class DevelopmentConfig(Config):
    DEBUG = True
    MONGO_URI = "mongodb://host.docker.internal:27017/CC_Projekt"

    
class TestingConfig(Config):
    TESTING = True