from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE core_profile "
                "ADD COLUMN IF NOT EXISTS monthly_income numeric(12,2) NOT NULL DEFAULT 0;"
            ),
            reverse_sql=(
                "ALTER TABLE core_profile "
                "DROP COLUMN IF EXISTS monthly_income;"
            ),
        ),
        migrations.RunSQL(
            sql=(
                "ALTER TABLE core_profile "
                "ADD COLUMN IF NOT EXISTS money_on_hand numeric(12,2) NOT NULL DEFAULT 0;"
            ),
            reverse_sql=(
                "ALTER TABLE core_profile "
                "DROP COLUMN IF EXISTS money_on_hand;"
            ),
        ),
    ]



