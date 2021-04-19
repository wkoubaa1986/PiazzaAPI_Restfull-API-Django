from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import create_post, post_detail, browse, BooststrapFilterView
from preferences.views import post_preference, preference_details
from comments.views import post_comment, comment_details

urlpatterns = [ 
    path('', create_post),
    path('<int:pk>/', post_detail),
    path('<int:pk>/preference/', post_preference),
    path('<int:pk>/preference/<int:pk1>', preference_details),
    path('<int:pk>/comment/', post_comment),
    path('<int:pk>/comment/<int:pk1>', comment_details),
    path('Browse/',BooststrapFilterView),
    path('<str:n>/', browse),
    
]
#urlpatterns = format_suffix_patterns(urlpatterns)