from django.db import migrations
from django.conf import settings


def set_topic_created_by(apps, schema_editor):
    Topic = apps.get_model('topics', 'Topic')
    User = apps.get_model('accounts', 'User')

    admin_user = User.objects.filter(role='admin').order_by('id').first()
    if not admin_user:
        return

    Topic.objects.filter(created_by__isnull=True).update(created_by=admin_user)


def reverse_func(apps, schema_editor):
    Topic = apps.get_model('topics', 'Topic')
    Topic.objects.update(created_by=None)


class Migration(migrations.Migration):

    dependencies = [
        ('topics', '0002_topic_created_by'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_topic_created_by, reverse_func),
    ]
