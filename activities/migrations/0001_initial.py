from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('leads', '0005_lead_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_type', models.CharField(choices=[('call', 'Call'), ('email', 'Email'), ('meeting', 'Meeting'), ('note', 'Note'), ('task', 'Task')], default='note', max_length=20)),
                ('title', models.CharField(max_length=120)),
                ('notes', models.TextField(blank=True)),
                ('completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='leads.lead')),
            ],
            options={
                'verbose_name_plural': 'activities',
                'ordering': ['-created_at'],
            },
        ),
    ]
