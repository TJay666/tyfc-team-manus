from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from team_management.models import Team

User = get_user_model()

class Command(BaseCommand):
    help = '建立預設使用者帳號'

    def handle(self, *args, **options):
        # 建立系統管理員
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                password='andy8668',
                email='admin@tyfc.com',
                user_type='admin',
                is_approved=True,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'成功建立系統管理員: {admin_user.username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('系統管理員 admin 已存在')
            )

        # 建立教練1
        if not User.objects.filter(username='coachbear').exists():
            coach1 = User.objects.create_user(
                username='coachbear',
                password='bear8888',
                email='coachbear@tyfc.com',
                user_type='coach',
                is_approved=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'成功建立教練: {coach1.username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('教練 coachbear 已存在')
            )

        # 建立教練2
        if not User.objects.filter(username='coachmilk').exists():
            coach2 = User.objects.create_user(
                username='coachmilk',
                password='milk8888',
                email='coachmilk@tyfc.com',
                user_type='coach',
                is_approved=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'成功建立教練: {coach2.username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('教練 coachmilk 已存在')
            )

        self.stdout.write(
            self.style.SUCCESS('預設帳號建立完成！')
        )

