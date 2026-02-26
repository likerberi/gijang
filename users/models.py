from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """커스텀 사용자 모델"""
    email = models.EmailField('이메일', unique=True)
    phone = models.CharField('전화번호', max_length=20, blank=True)
    department = models.CharField('부서', max_length=100, blank=True)
    created_at = models.DateTimeField('가입일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.email})"

