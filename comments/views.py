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

import requests
from posts.views import update_time

# Create your views here.
# Post preference actions
@api_view(['GET','POST'])
def post_comment(request,pk):
    '''
    Create a Comments to the post pk. Input should be in the format:
        {"body": "right your comment" }
    '''
    try:
        #Update time_to_expire_field
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
        #Update time_to_expire_field
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer) 
        r = {
            'Number of comments:': len(serializer.data['comments']),
            'Data': serializer.data,}
        return Response(r)
    elif request.method == 'POST':
                #Update time_to_expire_field
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer) 
        if serializer.data['status'] == 'Live':# Allow post preference only if the post is still Live
            # No limitation on the Ownership to comment
            #No limitation on the number of time you can comments the same post
            #Create Comment
            data_mutable=request.data.copy()#make the QueryDict mutable
            data_mutable['post']=serializer.data['id']
            data_mutable['time_to_expire']=t
            data_mutable['owner']=request.user.id # set the current user as user
            comm_serializer = CommentSerializer(data=data_mutable)
            if comm_serializer.is_valid():
                comm_serializer.save(owner=request.user)# set the current user as user
                r = {
                    'User ID': request.user.id,
                    'message': 'Successfully created comment',
                    'Data': comm_serializer.data,}
                return Response(r)
            return Response(comm_serializer.errors) 

        else: # Post is expired
            return Response('Action denied, Post has expired')



# Add preference delete / Change of mind
@api_view(['GET','PATCH','DELETE'])
def comment_details(request,pk,pk1):
    '''
    Change your comment for post pk, comment pk1. Input should be in the format:
    {"body": "right your comment" }
    '''
    try:# Fectch the specific post
        post = Post.objects.get(pk=pk)
        #Update time_to_expire_field
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        queryset_comment =Comment.objects.filter(post=serializer.data['id']) # find all the comment related to a post
        queryset_preference =Preference.objects.filter(post=serializer.data['id']) # find all the preference related to a post 
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer) 
    
    except Post.DoesNotExist:
        return Response('Post '+str(pk) + ' Not found ')
    
    try:# Fetch the specific preference
        comment = Comment.objects.get(pk=pk1)

    except Comment.DoesNotExist:
        return Response('Comment '+str(pk1) + ' Not found ')
    
    if request.method == 'GET':
        #Update time_to_expire_field
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer) 
        serializer_comm=CommentSerializer(comment)
        r = {
            'Post Title:': serializer.data['title'],
            'Post Owner:': serializer.data['owner'],
            'Post Status:': serializer.data['status'],
            'Comment Detail': serializer_comm.data,}
        return Response(r)
    elif request.method == 'PATCH':
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer) 
        if serializer.data['status'] == 'Live':# Allow  preference modification only if the post is still Live
            serializer_comm=CommentSerializer(comment)
            data_mutable=request.data.copy()#make the QueryDict mutable
            data_mutable['owner']=request.user.id # set the current user as user
            if data_mutable['owner']==serializer_comm.data['owner']:# Allow modification only if the user is the owner of the preference
                serializer_comm_new=CommentSerializer(comment,data=data_mutable,partial=True)
                if serializer_comm_new.is_valid():                    
                    serializer_comm_new.save() 
                    r = {
                        'Post Title:': serializer.data['title'],
                        'Post Owner:': serializer.data['owner'],
                        'Post Status:': serializer.data['status'],
                        'Comment Detail': serializer_comm_new.data,}
                    return Response(r)    
                return Response(serializer_comm_new.errors) 
            else:# User not owner of the comment
                return Response('Action denied, You are not the owner of this comment')
        else:#Post expired
            return Response('Action denied, Post has expired')
    elif request.method == 'DELETE':

        #Update time to expire
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer) 
        serializer_comm=CommentSerializer(comment)
        if serializer.data['status'] == 'Live':# Allow  preference modification only if the post is still Live
            if request.user.id == serializer_comm.data['owner']: #he is the owner
                comment.delete()
                r = {
                    'message': 'Successfully Deleted',
                    }
                return Response(r)
            else:
                return Response('Action can not performed! you are not owner of the comment. the owner Id is: ' + str(serializer_comm.data['owner']))
        else:
            return Response('Action denied, Post has expired')


