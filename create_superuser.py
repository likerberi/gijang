import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('슈퍼유저 생성 완료!')
    print('Username: admin')
    print('Password: admin123')
else:
    print('슈퍼유저가 이미 존재합니다.')
