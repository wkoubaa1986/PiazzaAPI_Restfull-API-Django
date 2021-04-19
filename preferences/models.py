from django.db import models
from django.contrib.auth.models import User
from posts.models import Post

# Create your models here.
class Preference(models.Model):
    status_choices = (('Like', 'Like'), ('Dislike', 'Dislike'))
    owner= models.ForeignKey(User, on_delete = models.CASCADE,related_name='prefrences')
    post= models.ForeignKey(Post, on_delete = models.CASCADE,default=None)
    value= models.CharField(max_length=16, choices=status_choices, default='Like')
    created_on= models.DateTimeField(auto_now_add=True)
    time_to_expire=models.DurationField()
    
    def __str__(self):
        return str(self.owner) + ':' + str(self.post) +':' + str(self.value)
    
    def get_unique_pref(self):
        return (self.owner.id,self.post.id,self.value)

    class Meta:
       unique_together = ("owner", "post", "value")
       ordering = ['created_on']