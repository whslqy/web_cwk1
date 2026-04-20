from django.db import migrations, models


def populate_bookids(apps, schema_editor):
    Book = apps.get_model('books', 'Book')
    for index, book in enumerate(Book.objects.order_by('id'), start=1):
        Book.objects.filter(pk=book.pk).update(bookid=index)


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_book_dataset_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='bookid',
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True, unique=True),
        ),
        migrations.RunPython(populate_bookids, migrations.RunPython.noop),
    ]
