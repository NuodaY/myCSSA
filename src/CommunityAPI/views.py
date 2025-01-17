from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from UserAuthAPI.models import UserProfile
from django.db.transaction import atomic

# Create your views here.

from typing import Optional, TypeVar, Callable
from . import models
from rest_framework import serializers, status, viewsets, permissions, mixins
from rest_framework.decorators import action, permission_classes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.fields import empty
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
import uuid
from CommunityAPI.filters import IsOwnerFilterBackend, NoImgFilter, TagFilter

from CommunityAPI.paginations import PostResultsSetPagination, NotificationSetPagination
from CommunityAPI.permissions import CanCensorPost, IsOwner, CanHandleReport
from .serializers import (
    EditCommentSerializer, PostImageSerializer, ReadCommentSerializer, TagSerializer, 
    EditMainPostSerializer, ReadMainPostSerializer, FavouritePostSerializer,
    NotificationSerializer, UserInformationSerializer, get_post_from_url, EditSubCommentSerializer, 
    ReadSubCommentSerializer, resolve_avatar, resolve_post_content, resolve_username, verify_comment, verify_main_post, 
    ReportSerializer, CreateReportSerializer, HandleReportSerializer
    )
from .models import Post, PostImage, Report, Tag, FavouritePost, Notification, UserInformation
from django.db.transaction import atomic

# 相关的后端开发文档参见： https://dev.cssaunimelb.com/doc/rest-framework-sSVw9rou1R

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    APIs to allow tags being read
    """
    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]

class FavouritePostViewSet(
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet):

    '''
    list: 返回当前用户的收藏列表

    destroy: 取消收藏
    '''

    serializer_class = FavouritePostSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (JWTAuthentication,)

    def get_queryset(self):

        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return FavouritePost.objects.none()

        query_set = FavouritePost.objects.filter(user=self.request.user.id, post__censored=False, post__deleted=False)

        return query_set

    

    def create_favourite_notification(self, 
        favouritePost: Post, favouriteUser: UserProfile):
     
        if self.request.user.pk == favouritePost.createdBy_id:
            return None
        
        return Notification.objects.create(
            user = favouritePost.createdBy,
            targetPost = favouritePost,
            type= Notification.FAVOURITE,
            sender_id = favouriteUser.pk,
            data={
                "target_post_tag": favouritePost.tag_id,
                'target_post_title': resolve_post_content(favouritePost).title,
            },
        )
    
    @atomic
    @swagger_auto_schema(method='PUT', operation_description='添加收藏',
        request_body=None, responses={202: '创建成功'})
    @action(methods=['PUT'], detail=True, url_path='add', url_name='add_favouritepost',
        serializer_class=None, permission_classes=[permissions.IsAuthenticated])
    def add_favouritepost(self, request, pk=None):
        userProfile: UserProfile = self.request.user
        post = pk
        favourite = models.FavouritePost.objects.filter(user=self.request.user.id,post=post).first()
        if favourite:
            return Response(status=status.HTTP_202_ACCEPTED)
        favourite = models.FavouritePost.objects.create(
            user_id=userProfile.pk,
            post_id=post
        )
        favouritePost = Post.objects.get(id = post)
    
        self.create_favourite_notification( favouritePost, userProfile)
        return Response(status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        user = self.request.user.id
        post = kwargs['pk']
        try:
            instance = FavouritePost.objects.get(user=user,post=post)
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class PostViewSetBase(viewsets.ReadOnlyModelViewSet, mixins.DestroyModelMixin):
    permission_classes = [permissions.AllowAny]
    authentication_classes = (JWTAuthentication,)
    pagination_class = PostResultsSetPagination
    filter_backends = [IsOwnerFilterBackend, NoImgFilter]

    def get_permissions(self):
        if self.action == 'destroy':
            # 对于自动生成的方法（比如这里的destroy），需要在这里指定权限
            # 权限必须是一个实例，而上面的 permission_classes 必须是类名
            return [IsOwner()] 
        else:
            return super().get_permissions()


    def perform_destroy(self, instance: Post):
        instance.deleted = True
        # 通过后缀名 _id 可以直接传 id。不加后缀的时候需要传进去一个 model instance
        # 不知道为啥， request.user 不能直接传，只能用它的id
        instance.deletedBy_id = self.request.user.id
        instance.save()

    T = TypeVar('T')
    def create_serializer(self, serializer: Callable[..., T], instance=None, data=empty) -> T:
        """
        使用context创建一个 serializer
        """
        return serializer(instance=instance, data=data, 
            context=self.get_serializer_context())

    def edit_post_base(self, request,
        edit_serializer=EditMainPostSerializer,
        read_serializer=ReadMainPostSerializer):

        instance = self.get_object()
        serializer = self.create_serializer(edit_serializer, 
            instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save()

        # 从 super().update 里复制来的代码（估计是缓存用的）
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        result = self.create_serializer(read_serializer, instance=post).data
        return Response(data=result, status=status.HTTP_202_ACCEPTED)

    def create_post_instance(self, request, edit_serializer) -> Post:
        serializer = self.create_serializer(edit_serializer, data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def create_post_response(self, post, read_serializer):
        result = self.create_serializer(read_serializer, instance=post).data
        return Response(data=result, status=status.HTTP_201_CREATED)
    
    def create_reply_notification(self, 
        target: Post, replier: Post, comment: Post, main_post: Post) -> Optional[Notification]:
        """
        创建一个回复通知。

        参数之间的关系如下：
        replier --回复给-> target --它们属于哪个一级评论-> comment --它们的主贴为-> main_post

        如果 request.user 跟 target.createBy 是同一个人的话，不创建通知
        """
        CONTENT_TEXT_LENGTH = 50

        if self.request.user.pk == target.createdBy_id:
            return None

        return Notification.objects.create(
            user=target.createdBy,
            targetPost=target,
            type=Notification.REPLY,
            sender=replier.createdBy,
            data={
                'main_post_id': main_post.pk,
                'main_post_tag_id': main_post.tag_id,
                'main_post_title': resolve_post_content(main_post).title,
                'reply_content_summary': resolve_post_content(replier).text[:CONTENT_TEXT_LENGTH],
                'comment_id': comment.pk,
            },
            )

class MainPostViewSet(PostViewSetBase):
    """
    主贴的增删改查

    retrieve: 获取一个帖子的全文

    list: 获取帖子的列表，其中，正文只包括前50个字符。

    destroy: 删除帖子
    """

    serializer_class = ReadMainPostSerializer
    filter_backends = PostViewSetBase.filter_backends + [TagFilter]
    
    def get_queryset(self):

        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return Post.objects.none()

        query = Post.objects.filter(
            censored=False, 
            deleted=False, 
            replyToId=None, 
            replyToComment=None,
            )

        if self.request.user.is_anonymous:
            query = query.filter(viewableToGuest=True)

        # 如果想要这个功能的话，可以在这里让管理员能看见被屏蔽和删除的文章

        return query.order_by('-createTime').select_related('createdBy') \
            .prefetch_related('createdBy__userinformation')

    # 在swagger文档里的条目定义：
    @swagger_auto_schema(method='POST', operation_description='添加一个帖子',
        request_body=EditMainPostSerializer, responses={
            201: ReadMainPostSerializer, 451: '用户发布的内容不合法'})
    # 给 rest_framework 用的view定义（这两个decorator的顺序不能反）
    @action(methods=['POST'], detail=False, url_path='create', url_name='create_post',
        serializer_class=EditMainPostSerializer,
        permission_classes=[permissions.IsAuthenticated])
    def create_post(self, request):
        post = self.create_post_instance(request, EditMainPostSerializer)
        return self.create_post_response(post, ReadMainPostSerializer)

    @swagger_auto_schema(method='POST', operation_description='修改帖子，不能修改 tag 和 viewableToGuest',
        request_body=EditMainPostSerializer, responses={
            202: ReadMainPostSerializer, 451: '用户发布的内容不合法'})
    @action(methods=['POST'], detail=True, url_path='edit', url_name='edit_post',
        serializer_class=EditMainPostSerializer, permission_classes=[IsOwner])
    def edit_post(self, request, pk=None):
        return self.edit_post_base(request, EditMainPostSerializer, ReadMainPostSerializer)

    @swagger_auto_schema(method='POST', operation_description='为帖子的浏览量+1',
        request_body=None, responses={202: 'Add view count successfully'})
    @action(methods=['POST'], detail=True, url_path='add-view-count', url_name='add_view_count',
        serializer_class=None, permission_classes=[AllowAny])
    @atomic
    def add_view_count(self, request, pk=None):
        post = self.get_object()
        post.viewCount = post.viewCount + 1
        post.save(update_fields=['viewCount'])
        return Response(status=status.HTTP_202_ACCEPTED)

class CommentViewSet(PostViewSetBase):
    """
    一级评论的增删改查

    list: 根据 post_id 获取其一级评论（全文）

    retrieve: 获取某一个评论的数据。必须同时指定 post_id 和 id

    destroy: 删除某个一级评论（post_id必须对应）
    """

    serializer_class = ReadCommentSerializer

    def get_queryset(self):

        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return Post.objects.none()

        mainPost = get_post_from_url(self)
        verify_main_post(mainPost)

        query = Post.objects.filter(
            censored=False, 
            deleted=False, 
            replyToId=mainPost, 
            replyToComment=None,
            )

        # 如果想要这个功能的话，可以在这里让管理员能看见被屏蔽和删除的文章

        return query.order_by('createTime').select_related('createdBy') \
            .prefetch_related('createdBy__userinformation')

    @swagger_auto_schema(method='POST', operation_description='添加一个评论',
        request_body=EditCommentSerializer, responses={
            201: ReadCommentSerializer, 451: '用户发布的内容不合法'})
    @action(methods=['POST'], detail=False, url_path='create', url_name='create_comment',
        serializer_class=EditCommentSerializer,
        permission_classes=[permissions.IsAuthenticated])
    def create_post(self, request, post_id=None): # 我们在url里定义了 post_id，这里就必须要声明，否则会报错
        post = self.create_post_instance(request, EditCommentSerializer)

        # 给被回复方添加通知
        target: Post = post.replyToId
        self.create_reply_notification(target, post, post, target)

        return self.create_post_response(post, ReadCommentSerializer)

    @swagger_auto_schema(method='POST', operation_description='修改回复',
        request_body=EditCommentSerializer, responses={
            202: ReadCommentSerializer, 451: '用户发布的内容不合法'})
    @action(methods=['POST'], detail=True, url_path='edit', url_name='edit_comment',
        serializer_class=EditCommentSerializer, permission_classes=[IsOwner])
    def edit_post(self, request, pk=None, post_id=None):
        return self.edit_post_base(request, EditCommentSerializer, ReadCommentSerializer)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (JWTAuthentication,)
    pagination_class = NotificationSetPagination
    filterset_fields = ['read']
    
    def get_queryset(self):

        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return Notification.objects.none()

        query = Notification.objects.filter(user_id=self.request.user.id).order_by('-id')
        return query
      
    @swagger_auto_schema(method='PUT', operation_description='设为已读',
        request_body=None, responses={202: '成功'})
    @action(methods=['PUT'], detail=True, url_path='read', url_name='mark_notification',
        serializer_class = None, permission_classes=[permissions.IsAuthenticated])
    @atomic
    def mark_notification(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response(status=status.HTTP_202_ACCEPTED)
       
class SubCommentViewSet(PostViewSetBase):
    """
    二级（及以上）回复的增删改查

    list: 根据 comment_id 获取某个一级评论下的所有评论（全文）

    retrieve: 获取某一个评论的数据。必须同时指定 comment_id 和 id

    destroy: 删除某个评论（comment_id 必须对应）
    """

    serializer_class = ReadSubCommentSerializer

    def get_queryset(self):

        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return Post.objects.none()

        comment = get_post_from_url(self, 'comment_id')
        verify_comment(comment)

        query = Post.objects.filter(
            censored=False, 
            deleted=False, 
            # replyToId != None
            replyToComment=comment,
            )

        # 如果想要这个功能的话，可以在这里让管理员能看见被屏蔽和删除的文章

        return query.order_by('createTime').select_related('createdBy') \
            .prefetch_related('createdBy__userinformation')

    @swagger_auto_schema(method='POST', operation_description='添加一个评论，用 replyTo 指定回复的对象，'
        '它必须跟本评论属于同一个一级评论。想要直接回复给一级评论，请将 replyTo 指定为 comment_id',
        request_body=EditSubCommentSerializer, responses={
            201: ReadSubCommentSerializer, 451: '用户发布的内容不合法'})
    @action(methods=['POST'], detail=False, url_path='create', url_name='create_subcomment',
        serializer_class=EditSubCommentSerializer,
        permission_classes=[permissions.IsAuthenticated])
    def create_post(self, request, comment_id=None): # 我们在url里定义了 post_id，这里就必须要声明，否则会报错
        post = self.create_post_instance(request, EditSubCommentSerializer)

        # 给被回复方添加通知
        target: Post = post.replyToId
        comment: Post = post.replyToComment
        mainPost: Post = comment.replyToId
        self.create_reply_notification(target, post, comment, mainPost)

        return self.create_post_response(post, ReadSubCommentSerializer)

    @swagger_auto_schema(method='POST', operation_description='修改回复，无法修改 replyTo',
        request_body=EditSubCommentSerializer, responses={
            202: ReadSubCommentSerializer, 451: '用户发布的内容不合法'})
    @action(methods=['POST'], detail=True, url_path='edit', url_name='edit_subcomment',
        serializer_class=EditSubCommentSerializer, permission_classes=[IsOwner])
    def edit_post(self, request, pk=None, comment_id=None):
        return self.edit_post_base(request, EditSubCommentSerializer, ReadSubCommentSerializer)

class ImageUploadView(APIView):
    parser_classes = (MultiPartParser,)
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (JWTAuthentication,)

    # from https://stackoverflow.com/a/45566729 and https://github.com/axnsan12/drf-yasg/issues/600
    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter(
                            name="file",
                            in_=openapi.IN_FORM,
                            type=openapi.TYPE_FILE,
                            required=True,
                            description="要上传的图片，大小不能超过10M"
                            )],
        operation_description='上传一个图片', responses={201: PostImageSerializer})
    @action(detail=False, methods=['post'])
    def post(self, request, **kwargs):
        try:
            file = request.data['file']
        except KeyError:
            raise ParseError('Request has no resource file attached')

        if file.size > 10485760:
            raise serializers.ValidationError("The maximum file size that can be uploaded is 10MB")

        image = PostImage.objects.create(id=uuid.uuid4(), uploader_id=request.user.id, image=file)
        output = PostImageSerializer(image, context={'request': request})

        return Response(output.data, status=status.HTTP_201_CREATED)

def get_notification_data_for_censor(instance: Post):
    NOTIFICATION_CONTENT_TEXT_LENGTH = 50

    type = instance.type
    if type == Post.MAIN_POST:
        return {
            'type': 'main_post',
            'main_post_id': instance.pk,
            'main_post_tag_id': instance.tag_id,
            'main_post_title': resolve_post_content(instance).title, 
            'content_summary': resolve_post_content(instance).text[:NOTIFICATION_CONTENT_TEXT_LENGTH],      
        }
    elif type == Post.COMMENT:
        return {
            'type': 'comment',
            'main_post_id': instance.replyToId.id, 
            'main_post_tag_id': instance.replyToId.tag_id,
            'main_post_title': resolve_post_content(instance.replyToId).title, 
            'content_summary': resolve_post_content(instance).text[:NOTIFICATION_CONTENT_TEXT_LENGTH],      
        }
    else:
        assert type == Post.SUBCOMMENT
        return {
            'type': 'subcomment',
            'main_post_id': instance.replyToComment.replyToId.id, 
            'main_post_tag_id': instance.replyToComment.replyToId.tag_id,
            'main_post_title': resolve_post_content(instance.replyToComment.replyToId).title, 
            'content_summary': resolve_post_content(instance).text[:NOTIFICATION_CONTENT_TEXT_LENGTH],      
        }

class CensorViewSet(viewsets.GenericViewSet):
    permission_classes = [CanCensorPost]
    authentication_classes = (JWTAuthentication, SessionAuthentication)
    queryset=models.Post.objects.filter(deleted=False)

    def _resolve_all_reports(self):
        instance: Post = self.get_object()

        # 批量处理举报
        Report.objects.filter(targetPost=instance).update(
            resolved=True,
            resolvedBy_id=self.request.user.pk,
        )

    @atomic
    @swagger_auto_schema(method='POST', operation_description='屏蔽帖子，并将关联的举报设置为已处理',
        request_body=None, responses={202: '处理成功', 401: '未授权'})
    @action(methods=['POST'], detail=True, url_path='censor', url_name='censor_post',
        serializer_class=None)
    def censor_post(self, request, pk=None):
        instance: Post = self.get_object()

        self._resolve_all_reports()

        if instance.censored:
            return Response(status=status.HTTP_202_ACCEPTED)

        instance.censored=True
        instance.censoredBy_id=request.user.id
        instance.save()

        Notification.objects.create(
            user=instance.createdBy,
            targetPost=instance,
            type=Notification.CENSOR,
            data={
                **get_notification_data_for_censor(instance),
                'reason': '其他理由',      
            },
            )
            
        return Response(status=status.HTTP_202_ACCEPTED)

    @atomic
    @swagger_auto_schema(method='POST', operation_description='取消帖子屏蔽，并将关联的举报设置为已处理',
        request_body=None, responses={202: '处理成功', 401: '未授权'})
    @action(methods=['POST'], detail=True, url_path='decensor',
        serializer_class=None)
    def decensor_post(self, request, pk=None):
        instance: Post = self.get_object()

        self._resolve_all_reports()

        if not instance.censored:
            return Response(status=status.HTTP_202_ACCEPTED)

        instance.censored=False
        instance.censoredBy=None
        instance.save()

        Notification.objects.create(
            user=instance.createdBy,
            targetPost=instance,
            type=Notification.DECENSOR,
            data={
                **get_notification_data_for_censor(instance),
            },
            )
            
        return Response(status=status.HTTP_202_ACCEPTED)

class UserInformationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (JWTAuthentication,)

    @swagger_auto_schema(operation_summary='获取我的信息（信息不存在时返回404）',
        responses={200: UserInformationSerializer, 404: '用户信息不存在'})
    def get(self, request):
        info = get_object_or_404(UserInformation.objects.all(), 
            user_id=request.user.id)

        return Response(
            UserInformationSerializer(info).data, 
            status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_summary='更新我的信息',
        request_body=UserInformationSerializer, responses={202: '更新成功'})
    @atomic
    def put(self, request):
        instance = UserInformation.objects.filter(user_id=request.user.id).first()
        serializer = UserInformationSerializer(data=request.data, instance=instance)
        serializer.is_valid(raise_exception=True)

        serializer.save(user_id=request.user.id)

        return Response(status=status.HTTP_202_ACCEPTED)

    def delete(self, request):
        """
        删除我的信息
        """
        UserInformation.objects.filter(user_id=request.user.id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ReportViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [CanHandleReport]
    authentication_classes = (JWTAuthentication,)
    serializer_class = ReportSerializer
    queryset = Report.objects.filter()

    @atomic
    @swagger_auto_schema(method='POST', operation_description='举报帖子',
        request_body=None, responses={202: '举报成功'})
    @action(methods=['POST'], detail=False, url_path='create', url_name='report_post',
        serializer_class=CreateReportSerializer, permission_classes=[permissions.IsAuthenticated])
    def report_post(self, request):
        userProfile: UserProfile = self.request.user
        
        Report.objects.create(
            createdBy_id = userProfile.pk, 
            targetPost_id = request.data['targetPost'], 
            reason = request.data['reason'], 
            type=request.data['type']
        )
        return Response(status=status.HTTP_202_ACCEPTED)

    @atomic
    @swagger_auto_schema(method='POST', operation_description='处理举报（拒绝）',
        request_body=None, responses={202: '处理成功', 401: '未授权'})
    @action(methods=['POST'], detail=False, url_path='reject', url_name='reject_report',
        serializer_class=HandleReportSerializer, permission_classes=[CanHandleReport])
    def reject_report(self, request):
        userProfile: UserProfile = self.request.user
        id_list = list(request.data['id_list'])

        instances = Report.objects.filter(id__in=id_list)
        instances.update(resolved=True, resolvedBy_id=userProfile.pk)

        return Response(status=status.HTTP_202_ACCEPTED)

    @atomic
    @swagger_auto_schema(method='POST', operation_description='处理举报（接受）',
        request_body=None, responses={202: '处理成功', 401: '未授权'})
    @action(methods=['POST'], detail=False, url_path='accept', url_name='accept_report',
        serializer_class=HandleReportSerializer, permission_classes=[CanHandleReport])
    def accept_report(self, request):
        userProfile: UserProfile = self.request.user
        id_list = list(request.data['id_list'])
        
        instances = Report.objects.filter(id__in=id_list)
        instances.update(resolved=True, resolvedBy_id=userProfile.pk)

        for i in id_list:
            report_instance=Report.objects.get(id=i)
            post_instance = report_instance.targetPost
            if not post_instance.censored:
                # 每个单独检查，若已经屏蔽，则不覆盖原有信息，且不会创建新的notification
                post_instance.censored=True
                post_instance.censoredBy_id=request.user.id
                post_instance.save()

                Notification.objects.create(
                    user=post_instance.createdBy,
                    targetPost=post_instance,
                    type=Notification.CENSOR,
                    data={
                        **get_notification_data_for_censor(post_instance),
                        'reason': report_instance.type, # TODO:这里是返回reason还是type
                    },
                    )

        return Response(status=status.HTTP_202_ACCEPTED)
