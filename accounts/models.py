from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('admin', '系統管理員'),
        ('coach', '教練'),
        ('player', '球員'),
    ]
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='player',
        verbose_name='使用者類型'
    )
    
    is_approved = models.BooleanField(
        default=False,
        verbose_name='是否已審核'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='電話號碼'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='建立時間'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新時間'
    )
    
    class Meta:
        verbose_name = '使用者'
        verbose_name_plural = '使用者'
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

