class CustomRouter:
    def db_for_read(self, model, **hints):
        return 'reader'

    def db_for_write(self, model, **hints):
        return 'default'
