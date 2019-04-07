from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings


GENDER_CHOICES = (
    ('1', '女性'),
    ('2', '男性'),
)


class Article(models.Model):
    text = models.CharField("投稿内容", max_length=140)
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField("投稿日時", default=timezone.now)

    def __str__(self):
        return self.text


class Profile(models.Model):
    introduction = models.TextField("自己紹介", blank=True)
    sex = models.CharField("性別", max_length=2, choices=GENDER_CHOICES, blank=True)
    # black_list = models.TextField("ブラックリスト", blank=True, default="", editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.introduction


class Like(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='like_user')
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class BlackListM(models.Model):
    add_user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='bl_add')
    target_user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='bl_target')
    created_at = models.DateTimeField(auto_now_add=True)
