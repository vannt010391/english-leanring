from django.db import migrations


def set_vocab_created_by(apps, schema_editor):
    Vocabulary = apps.get_model('vocabulary', 'Vocabulary')
    User = apps.get_model('accounts', 'User')

    admin_user = User.objects.filter(role='admin').order_by('id').first()

    for vocab in Vocabulary.objects.all():
        if vocab.created_by_id:
            continue
        if vocab.owner_id:
            vocab.created_by_id = vocab.owner_id
        elif admin_user:
            vocab.created_by_id = admin_user.id
        vocab.save(update_fields=['created_by'])


def reverse_func(apps, schema_editor):
    Vocabulary = apps.get_model('vocabulary', 'Vocabulary')
    Vocabulary.objects.update(created_by=None)


class Migration(migrations.Migration):

    dependencies = [
        ('vocabulary', '0003_vocabulary_created_by'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_vocab_created_by, reverse_func),
    ]
