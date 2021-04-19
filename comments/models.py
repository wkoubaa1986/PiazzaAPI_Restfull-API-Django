from django.db import models
from django.contrib.auth.models import User
from posts.models import Post
# Create your models here.
class Comment(models.Model):
    post = models.ForeignKey(Post,on_delete=models.CASCADE,related_name='comments')
    owner= models.ForeignKey(User, on_delete = models.CASCADE,default=None)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    time_to_expire=models.DurationField()
    

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return 'Comment {} by {}'.format(self.body, self.owner)
