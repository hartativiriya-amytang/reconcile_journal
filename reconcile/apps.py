from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_groups(sender, **kwargs):
    from django.contrib.auth.models import Group
    Group.objects.get_or_create(name='Finance')
    Group.objects.get_or_create(name='Admin Finance')


class ReconcileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reconcile'

    def ready(self):
        post_migrate.connect(create_groups, sender=self)
