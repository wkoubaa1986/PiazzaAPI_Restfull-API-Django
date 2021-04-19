from django.db import models
from django.contrib.auth.models import User
from multiselectfield import MultiSelectField
from django.template.defaultfilters import slugify
from django.utils import timezone

MY_CHOICES = (
    ('Politics', "Politics"),
    ('Health', "Health"),
    ('Sport', "Sport"),
    ('Tech', "Tech"),
)
status_choices = (('Live', 'Live'), ('Expired', 'Expired'))
# Create your models here.
class Post(models.Model):
    
    title = models.CharField(max_length=200)
    url= models.SlugField(unique=True, blank=True, default=None, null=True)
    owner= models.ForeignKey(User, on_delete = models.CASCADE)
    created_on = models.DateTimeField(auto_now=False, auto_now_add=True)
    expiration_time = models.IntegerField(default=10080)  #assume minutes, default one week of validity
    status= models.CharField(max_length=16, choices=status_choices, default='Live')
    topic=MultiSelectField(choices=MY_CHOICES, max_length=100)
    content= models.TextField()
    likes= models.IntegerField(default=0)
    dislikes= models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.url= slugify(self.title)
        super(Post, self).save(*args, **kwargs)
    

    # Define Values for Status
    def time_to_expire(self,*args, **kwargs):
        t=self.created_on + timezone.timedelta(minutes=self.expiration_time)
        z=t-timezone.now()
        
        if z.total_seconds() > 0:
            return z.total_seconds()
        else:
            self.status='Expired'
            super(Post, self).save(*args, **kwargs)
            return 0

    def __str__(self):
        return 'Posted by {}'.format( self.owner)

    class Meta:
        ordering = ["created_on"]

