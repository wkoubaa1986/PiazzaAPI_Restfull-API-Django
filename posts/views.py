from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import viewsets
from posts.models import Post, MY_CHOICES
from comments.models import Comment
from preferences.models import Preference
from posts.serializers import PostSerializer 
from comments.serializers import CommentSerializer
from preferences.serializers import PreferenceSerializer
from django.utils import timezone
from django.db.models import F, Sum, Max
import requests

# Create your views here.
class PostViewSet(viewsets.ModelViewSet):
    queryset=Post.objects.all()
    serializer_class=PostSerializer
    

@api_view(['GET','POST'])
def create_post(request):
    '''
    Create a post to the  server. Input should be in the format:
        {"title": "title1",
        "expiration_time": 10080, # in minutes Optional by default the post is valid 7 days
        "topic": ["Politics"],
        "content": "Bla Bla Bla"}
    '''
    if request.method == 'GET':    
        posts = Post.objects.all()
        # update all the time to exipire
        for item in posts:
            t=item.time_to_expire()# get time to expire
            t=timezone.timedelta(seconds=int(t))
            serializer = PostSerializer(item)
            queryset_comment =Comment.objects.filter(post=serializer.data['id']) # find all the comment related to a post
            queryset_preference =Preference.objects.filter(post=serializer.data['id']) # find all the preference related to a post 
            update_time(queryset_comment,t,CommentSerializer)
            update_time(queryset_preference,t,PreferenceSerializer) 

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data_mutable=request.data.copy()#make the QueryDict mutable
        data_mutable['owner']=request.user.id # set the current user as user
        serializer = PostSerializer(data=data_mutable)
        if serializer.is_valid():
            serializer.save(owner=request.user)# set the current user as user
            r = {
                'User ID': request.user.id,
                'message': 'Successfully created Post',
                'Data': serializer.data,}
            return Response(r)
        return Response(serializer.errors)       


@api_view(['GET', 'PUT', 'DELETE'])
def post_detail(request, pk):
    """
    Retrieve, update or delete a  Post.
    """

    try:
        post = Post.objects.get(pk=pk)
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        queryset_comment =Comment.objects.filter(post=serializer.data['id']) # find all the comment related to a post
        queryset_preference =Preference.objects.filter(post=serializer.data['id']) # find all the preference related to a post
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer)
    except Post.DoesNotExist:
        return Response('Post '+str(pk) + ' Not found ')

    if request.method == 'GET':
        
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer)
        r = {
            'Number of comments:': len(serializer.data['comments']),
            'Data': serializer.data,}
        return Response(r)


    elif request.method == 'PUT':
        
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer)
        if serializer.data['status'] == 'Live':# Allow  preference modification only if the post is still Live
        #Check if the current user is different from post owner
            if request.user.id == serializer.data['owner']:# he is the owner 
                data_mutable=request.data.copy()#make the QueryDict mutable
                data_mutable['owner']=request.user.id # set the current user as user
                serializer = PostSerializer(post, data=data_mutable)
        
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors)
            else:
                return Response('Action denied! you are not owner of the post. the owner Id is: ' + str(serializer.data['owner']))
        else:
            return Response('Action denied, Post has expired')

    elif request.method == 'DELETE':
                #Update time to expire
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer) 
        if serializer.data['status'] == 'Live':# Allow  preference modification only if the post is still Live
            if request.user.id == serializer.data['owner']:# he is the owner
                post.delete()
                r = {
                    'message': 'Successfully Deleted',
                    }
                return Response(r)
            else:
                return Response('Action can not performed! you are not owner of the post. the owner Id is: ' + str(serializer.data['owner']))
        else:
            return Response('Action denied, Post has expired')
#******************************************************************************************************************************************
@api_view()
def browse(request,n):

    topics=['politics','health','sport', 'tech']
    status=['live','expired']
    interrest=['highestinterest','lowestinterest']

    query_action=n.split('+')
    # list of actions:
    my_filter={} 
    interest=0 
    for i in query_action:
        # Ignore spoace Cap Letter and "-"  "_" 
        action=i.lower()
        action=action.replace(" ","")
        action=action.replace("_","")
        action=action.replace("-","")
        if action in topics:
            #find the topic to select
            my_action='topic__icontains'
            my_filter[my_action]=action.capitalize()
        elif action in status:
            my_action='status__icontains'
            my_filter[my_action]=action.capitalize()
        elif action in interrest:
            if action =='highestinterest':
                interest=1
            else:
                interest=2
        
    queryset=Post.objects.all().filter(**my_filter)
    if interest==1:
        queryset=queryset.annotate(total_like=Sum(F('likes') + F('dislikes'))).order_by('total_like')
        queryset=queryset.last()
        queryset=Post.objects.filter(pk=queryset.pk)
    elif interest==2:
        queryset=queryset.annotate(total_like=Sum(F('likes') + F('dislikes'))).order_by('total_like')
        queryset=queryset.first()
        queryset=Post.objects.filter(pk=queryset.pk)        

    if not (len(my_filter)==0 and interest==0) :
        for item in queryset:
            # update all the time to exipire
            t=item.time_to_expire()# get time to expire
            t=timezone.timedelta(seconds=int(t))
            serializer = PostSerializer(item)
            queryset_comment =Comment.objects.filter(post=serializer.data['id']) # find all the comment related to a post
            queryset_preference =Preference.objects.filter(post=serializer.data['id']) # find all the preference related to a post 
            update_time(queryset_comment,t,CommentSerializer)
            update_time(queryset_preference,t,PreferenceSerializer) 
        serializer = PostSerializer(queryset, many=True)
        return Response(serializer.data)
    
    else:
       return Response('No Action in ' + n + ' is recognised')


@api_view()
def BooststrapFilterView(request):
    selectionTop=request.GET.get('TopicSlection')
    selectionStu=request.GET.get('StatusSlection')
    print(selectionTop)
    print(selectionStu)
    return render(request,"boostrap_form.html",{})

#***********************************************************************************************************************************
##Additional function
#Function to update time_to_expiry field for comment and preference
def update_time(queryset,time_val,ser_func):
    for item in queryset:
        serializer=ser_func(item)
        serializer.data['time_to_expire']=time_val
        serializer = ser_func(item, data=serializer.data)
        if serializer.is_valid():
            serializer.save(time_to_expire=time_val)





        

    
