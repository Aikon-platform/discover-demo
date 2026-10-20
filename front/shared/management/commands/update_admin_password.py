import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management import CommandError
from django.contrib.auth import get_user_model
from django.db.models import Q

class Command(BaseCommand):
    help = "Create the superuser if they don't aldready exist, and update their password"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        env_vars = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
        env_dict = {}
        for vname in env_vars:
            env_dict[vname] = os.environ.get(vname)

        if any(v is None for v in env_dict.items()):
            self.stdout.write(
                self.style.ERROR(f"⛔️ To update the admin password, the following environment variables must be set: {env_vars}")
            )
            return

        User = get_user_model()
        try:
            user = User.objects.filter(Q(username=env_dict["POSTGRES_USER"]) & Q(is_superuser=True)).first()
            # if the user exists, set it to superuser if necessary and update its password
            if user:
                user.set_password(env_dict["POSTGRES_PASSWORD"])
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✔️ User {env_dict['POSTGRES_USER']} password updated to follow .env config."
                    )
                )
            # otherwise, create the superuser
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ No superuser with name {env_dict['POSTGRES_USER']} found ! Update failed."
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"⛔️ Error updating password: {e}")
            )