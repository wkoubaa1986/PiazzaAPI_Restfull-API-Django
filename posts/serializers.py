from rest_framework import serializers
#from .models import Post, Preference, Comment, MY_CHOICES, 
from .models import Post, MY_CHOICES
from comments.serializers import CommentSerializer


    

class PostSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True,required=False, allow_null=True, read_only=True)# real only to handle nested serialiser during update/ No need to update comment
    topic = serializers.MultipleChoiceField( choices = MY_CHOICES)
    class Meta:
        model = Post
        fields=('id','title','owner','created_on','expiration_time','status','topic','content','likes','dislikes','comments')
        read_only_fields = ['url']
    

    





