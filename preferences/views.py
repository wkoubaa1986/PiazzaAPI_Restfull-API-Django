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
def post_preference(request,pk):
    '''
    Create a Preference to the post pk. Input should be in the format:
        {"value": "Like" / "Dislike" chose preference action}
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
        serializer_set=PreferenceSerializer(queryset_preference, many=True)
        r = {
            'Post Title:': serializer.data['title'],
            'Post Owner:': serializer.data['owner'],
            'Post Status:': serializer.data['status'],
            'Preferences': serializer_set.data,}
        return Response(r)
    elif request.method == 'POST':
                #Update time_to_expire_field
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer) 
        if serializer.data['status'] == 'Live':# Allow post preference only if the post is still Live
            data_mutable=request.data.copy()#make the QueryDict mutable
            data_mutable['owner']=request.user.id # set the current user as user
            #request.data['owner']=request.user.id # set the current user as user
            if request.user.id!=serializer.data['owner']:# Allow the post since the current user is different from the post owner
                #Create preference
                data_mutable['post']=serializer.data['id']
                data_mutable['time_to_expire']=t
                pref_serializer = PreferenceSerializer(data=data_mutable)
                # Check if user has already liked the post
                if not(check_preference_exist(queryset_preference,data_mutable['owner'],data_mutable['post'])): # the current user did not like the post already
                    if pref_serializer.is_valid():
                        pref_serializer.save(owner=request.user)# set the current user as user
                        r = {
                            'User ID': request.user.id,
                            'message': 'Successfully created preference',
                            'Data': pref_serializer.data,}
                        #Update the likes/ dislikes in Post
                        like=serializer.data['likes']
                        dislike=serializer.data['dislikes']
                        if data_mutable['value'] == 'Like':
                            like+=1
                        else:
                            dislike+=1
                        serializer = PostSerializer(post, data=serializer.data)
                        if serializer.is_valid():
                            serializer.save(likes=like,dislikes=dislike)
                            return Response(r)
                        return Response(serializer.errors) 
                    return Response(pref_serializer.errors) 
                else: #the current user did a preference for the post already
                    return Response(['Action denied, you interracted with the post already if you want to change your preference please select it and patch it'])
                
            else:# Current user is the post owner
                return Response('Action denied, you are the owner of the Post')
        else: # Post is expired
            return Response('Action denied, Post has expired')



# Add preference delete / Change of mind
@api_view(['GET','PATCH','DELETE'])
def preference_details(request,pk,pk1):
    '''
    Change your Preference for post pk, preference pk1. Input should be in the format:
        {"value": "Like" / "Dislike" chose preference action}
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
        preference = Preference.objects.get(pk=pk1)

    except Preference.DoesNotExist:
        return Response('Preference '+str(pk1) + ' Not found ')
    
    if request.method == 'GET':
        #Update time_to_expire_field
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer) 
        serializer_pref=PreferenceSerializer(preference)
        r = {
            'Post Title:': serializer.data['title'],
            'Post Owner:': serializer.data['owner'],
            'Post Status:': serializer.data['status'],
            'Preference Detail': serializer_pref.data,}
        return Response(r)
    elif request.method == 'PATCH':
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer) 
        if serializer.data['status'] == 'Live':# Allow  preference modification only if the post is still Live
            serializer_pref=PreferenceSerializer(preference)
            data_mutable=request.data.copy()#make the QueryDict mutable
            data_mutable['owner']=request.user.id # set the current user as user
            if data_mutable['owner']==serializer_pref.data['owner']:# Allow modification only if the user is the owner of the preference
                serializer_pref_new=PreferenceSerializer(preference,data=data_mutable,partial=True)
                if serializer_pref_new.is_valid():
                    if request.data['value']==serializer_pref.data['value']:
                        return Response('You have already made a :' + request.data['value'])
                    else:#perform the update
                    
                    #update the number of likes dislike to the post related to the preference
                                            #Update the likes/ dislikes in Post
                        like=serializer.data['likes']
                        dislike=serializer.data['dislikes']
                        if request.data['value'] == 'Like':
                            like+=1
                            dislike-=1
                        else:
                            dislike+=1
                            like-=1
                        serializer = PostSerializer(post, data=serializer.data)
                        if serializer.is_valid():
                            serializer.save(likes=like,dislikes=dislike)
                        else:
                            return Response(serializer.errors) 
                        serializer_pref_new.save()
                    return Response(serializer_pref_new.data) 
                else:    
                    return Response(serializer_pref_new.errors) 
            else:# User not owner of the preference
                return Response('Action denied, You are not the owner of this preference')
        else:#Post expired
            return Response('Action denied, Post has expired')
    elif request.method == 'DELETE':

        #Update time to expire
        t=post.time_to_expire()# get time to expire
        t=timezone.timedelta(seconds=int(t))
        serializer = PostSerializer(post)
        update_time(queryset_comment,t,CommentSerializer)
        update_time(queryset_preference,t,PreferenceSerializer) 
        serializer_pref=PreferenceSerializer(preference)
        if serializer.data['status'] == 'Live':# Allow  preference modification only if the post is still Live
            if request.user.id == serializer_pref.data['owner']: #he is the owner
                preference.delete()
                #Update the number of likes
                like=serializer.data['likes']
                dislike=serializer.data['dislikes']
                if serializer_pref.data['value'] == 'Like':
                    like-=1
                else:
                    dislike-=1

                serializer = PostSerializer(post, data=serializer.data)
                if serializer.is_valid():
                    serializer.save(likes=like,dislikes=dislike)
                else:
                    return Response(serializer.errors)
                r = {
                    'message': 'Successfully Deleted',
                    }
                return Response(r)
            else:
                return Response('Action can not performed! you are not owner of the preference. the owner Id is: ' + str(serializer_pref.data['owner']))
        else:
            return Response('Action denied, Post has expired')

#****************************************************************************************************************
def check_preference_exist(queryset,own,pos):
    val_exist=False
    for item in queryset:
        my_field = item.get_unique_pref()
        test1=(own,pos,'Like')
        test2=(own,pos,'Dislike')
        if test1 == my_field or test2 == my_field:
            val_exist=True
            break
    return val_exist
