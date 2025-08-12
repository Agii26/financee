from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_fix_profile_columns"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE core_profile "
                "ADD COLUMN IF NOT EXISTS created_at timestamp with time zone NOT NULL DEFAULT NOW();"
            ),
            reverse_sql=(
                "ALTER TABLE core_profile "
                "DROP COLUMN IF EXISTS created_at;"
            ),
        ),
        migrations.RunSQL(
            sql=(
                "ALTER TABLE core_profile "
                "ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone NOT NULL DEFAULT NOW();"
            ),
            reverse_sql=(
                "ALTER TABLE core_profile "
                "DROP COLUMN IF EXISTS updated_at;"
            ),
        ),
    ]



