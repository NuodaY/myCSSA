import dateutil
from django import views
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.views.generic.base import TemplateView, View
from django_datatables_view.base_datatable_view import BaseDatatableView
from rest_framework.generics import get_object_or_404
from django.db.models import OuterRef, Subquery, Count
from django.urls import reverse
from dateutil.parser import parse as parse_date

from CommunityAPI.models import Content, Post, PostImage, Report
from .serializers import resolve_post_content

def pk(instance):
    if not instance:
        return ''
    else:
        return instance.pk

class ShowPostView(LoginRequiredMixin, TemplateView):
    login_url = '/hub/login/'
    template_name = 'CommunityAPI/show_post.html'
    permission_required = ('CommunityAPI.censor_post')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id = self.request.GET.get('id', 0)
        post: Post = Post.objects.filter(id=id).first()

        if post:
            return {
                **context,
                'id': id,
                'post': post,
                'content': resolve_post_content(post),
                'post_fields': [
                    ('创建时间', post.createTime),
                    ('创建者', post.createdBy.pk),
                    ('Tag', post.tag.title if post.tag else ''),
                    ('未登录用户是否可见', post.viewableToGuest),
                    ('被删除', post.deleted),
                    ('被谁删除', pk(post.deletedBy)),
                    ('被屏蔽', post.censored),
                    ('被谁屏蔽', pk(post.censoredBy)),
                ]
            }
        else:
            return {
                **context,
                'id': id,
            }

class PostListView(LoginRequiredMixin, TemplateView):
    """
    列出所有的帖子
    """

    login_url = '/hub/login/'
    template_name = 'CommunityAPI/post_list.html'
    permission_required = ('CommunityAPI.censor_post',)

class PostListJsonView(LoginRequiredMixin, PermissionRequiredMixin, BaseDatatableView):
    login_url = '/hub/login/'
    permission_required = ('CommunityAPI.censor_post',)

    columns = [
        'id', 'type', 'tag', 'viewableToGuest', 'deleted', 'censored', 
        'createTime', 'editedTime', 'viewCount', 'reported', 'title', 'text', 
        'imageCount',
    ]
    order_columns = columns

    max_display_length = 500

    def get_initial_queryset(self):
        content = Content.objects.filter(post=OuterRef('id')) \
            .annotate(imageCount=Count('images')) \
            .order_by('editedTime')[:1]
        query = Post.objects.order_by('-createTime') \
            .annotate(reported=Count('report')) \
            .annotate(text=content.values('text')) \
            .annotate(title=content.values('title')) \
            .annotate(imageCount=content.values('imageCount')) \
            .annotate(editedTime=content.values('editedTime'))

        type = self.request.GET.get('type')
        if type == 'MAIN_POST':
            query = query.filter(replyToId__isnull=True)
        elif type == 'COMMENT':
            query = query.filter(replyToComment__isnull=True, replyToId__isnull=False)
        elif type == 'SUBCOMMENT':
            query = query.filter(replyToComment__isnull=False, replyToId__isnull=False)

        has_report = self.request.GET.get('has-report')
        if has_report == 'yes':
            query = query.filter(reported__gt=0)
        elif has_report == 'no':
            query = query.filter(reported=0)

        is_censored = self.request.GET.get('is-censored')
        if is_censored == 'yes':
            query = query.filter(censored=True)
        elif is_censored == 'no':
            query = query.filter(censored=False)

        create_after = self.request.GET.get('create-after')
        if create_after:
            query = query.filter(createTime__gte=parse_date(create_after))

        edit_after = self.request.GET.get('edit-after')
        if edit_after:
            query = query.filter(editedTime__gte=parse_date(edit_after))

        has_image = self.request.GET.get('has-image')
        if has_image == 'yes':
            query = query.filter(imageCount__gt=0)
        elif has_image == 'no':
            query = query.filter(imageCount=0)

        return query

    def render_column(self, row, column):
        if column == 'id':
            return f'''<a href="{
                reverse('myCSSAhub:CommunityAPI:show_post')}?id={row.id}">
                {row.id}</a>'''

        else: 
            return super().render_column(row, column)