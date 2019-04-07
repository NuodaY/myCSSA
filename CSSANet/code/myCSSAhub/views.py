from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import MerchantsForm
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm

from django.views import View
from django.views.generic import CreateView, UpdateView, FormView
from django.contrib.auth.models import update_last_login
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from .models import AccountMigration, DiscountMerchant
from UserAuthAPI import models as UserModels
from BlogAPI import models as BlogModels
from UserAuthAPI.forms import BasicSiginInForm, UserInfoForm, MigrationForm, UserAcademicForm, UserProfileUpdateForm, EasyRegistrationForm
from LegacyDataAPI import models as LegacyDataModels
from CommunicateManager.send_email import send_emails

from CSSANet.settings import MEDIA_ROOT, MEDIA_URL
import json
import base64
import io
import hashlib

from urllib import parse

from django.core.files import File

import datetime

from django.urls import reverse

# Create your views here.


def register_guide(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/hub/home/")
    return render(request, 'myCSSAhub/register_guide.html')


@login_required(login_url='/hub/login/')
def home(request):
    return render(request, 'myCSSAhub/home.html')


################################# calendar ########################################
class Calendar(LoginRequiredMixin, View):
    login_url = '/hub/login/'
    template_name = 'Communication/calendar.html'

    def get(self, request):

        return render(request, self.template_name, locals())

    def post(self, request):

        return render(request, self.template_name)


class Email_Message(LoginRequiredMixin, View):
    login_url = '/hub/login/'
    template_name = 'myCSSAhub/email_message.html'

    def get(self, request):

        return render(request, self.template_name, locals())

    def post(self, request):

        return render(request, self.template_name)


class Email_Compose(LoginRequiredMixin, View):
    login_url = '/hub/login/'
    template_name = 'myCSSAhub/email_compose.html'

    def get(self, request):

        return render(request, self.template_name, locals())

    def post(self, request):

        return render(request, self.template_name)

################################# calendar ########################################


class Calendar(LoginRequiredMixin, View):
    login_url = '/hub/login/'
    template_name = 'myCSSAhub/calendar.html'

    def get(self, request):

        return render(request, self.template_name, locals())

    def post(self, request):

        return render(request, self.template_name)


################################# merchants ########################################


class Merchants_list(PermissionRequiredMixin, LoginRequiredMixin, View):
    login_url = '/hub/login/'
    template_name = 'myCSSAhub/merchants_list.html'
    permission_required = ('myCSSAhub.change_discountmerchant')

    def get(self, request):
        if request.user.is_authenticated:
            infos = DiscountMerchant.objects.all().order_by("merchant_add_date").values()

        return render(request, self.template_name, locals())

    def post(self, request):
        return render(request, self.template_name)


class Merchant_add(PermissionRequiredMixin, LoginRequiredMixin, View):
    login_url = '/hub/login/'
    template_name = 'myCSSAhub/merchant_add.html'
    permission_required = ('myCSSAhub.change_discountmerchant')
    form_class = MerchantsForm

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': self.form_class})

    def post(self, request, *args, **kwargs):
        have_update = False
        # 从表单获取图片并上传
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            # 标注：所有跟表单相关的保存操作，用ModelForm绑定，不要手写model field，容易出错
            form.save()
            have_update = True
        # return render(request, self.template_name, {'update': have_update})

        return render(request, self.template_name, {'update': have_update, 'form': form})

#


class Merchant_profile(LoginRequiredMixin, View):
    '''
    加载已经加入商家的信息，并更新
    '''

    login_url = '/hub/login/'
    template_name = 'myCSSAhub/merchant_profile.html'
    form_class = MerchantsForm

    def get(self, request,  *args, **kwargs):

        profileID = self.kwargs.get('id')
        obj = get_object_or_404(DiscountMerchant, merchant_id=profileID)
        form = self.form_class(instance=obj)

        return render(request, self.template_name, {'form':form, 'submit_url':reverse('myCSSAhub:merchant_profile', args=[str(profileID)])})
   
      
    def post(self, request,  *args, **kwargs):
        have_update = False
        profileID = self.kwargs.get('id')    
        obj = get_object_or_404(DiscountMerchant, merchant_id=profileID)
        form = self.form_class(data=request.POST or None, files=request.FILES or None, instance=obj)
        if form.is_valid():
            form.save() 
            have_update = True

        return render(request, self.template_name, {'update': have_update, 'form':form, 'submit_url':reverse('myCSSAhub:merchant_profile', args=[str(profileID)])})
      

###### logout page ##########

@login_required(login_url='/hub/login/')
def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')


###### 账号相关 ##########
# 用户登陆CBV -- 范例
class LoginPage(View):
    # 类属性
    model = UserModels.User
    template_name = 'myCSSAhub/login.html'
    loginErrorMsg = {"result": "Login Failed!"}
    loginSuccessful = {"result": "Login Successful!"}

    # 请求处理函数 （get）
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect("/hub/home/")
        return render(request, self.template_name)

    # 请求处理函数（post）
    def post(self, request, *args, **kwargs):
        email = request.POST['email'].lower()
        userQuery = self.model.objects.filter(email__iexact=email).first()
        # Patch, clean email with capitalisation
        if any(c.isupper for c in userQuery.email):
            _email_convert = userQuery.email.lower()
            userQuery.email = _email_convert
            userQuery.save()

        redirect_to = request.GET.get('redirect_to')
        if userQuery is None:
            return JsonResponse(self.loginErrorMsg)
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            update_last_login(None, user)
            if redirect_to:
                self.loginSuccessful['redirect'] = redirect_to
            else:
                self.loginSuccessful['redirect'] = reverse('PublicSite:index')
            return JsonResponse(self.loginSuccessful)
        else:
            return JsonResponse(self.loginErrorMsg)


class EasyRegistrationView(View):
    template_name = 'myCSSAhub/easy_registration.html'
    account_form = BasicSiginInForm
    profile_form = EasyRegistrationForm

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect("/hub/home/")
        """Handle GET requests: instantiate a blank version of the form."""
        id = self.kwargs.get('id')
        legacy_data = None
        if id:
            try:
                migration_record = AccountMigration.objects.filter(
                    id=id).first()
                legacy_data = LegacyDataModels.LegacyUsers.objects.get(
                    Q(studentId=migration_record.studentId) & Q(
                        membershipId=migration_record.membershipId)
                )
            except ObjectDoesNotExist:
                print("The user is not registered successfully.")

        return render(request, self.template_name, {'LegacyData': legacy_data})

    def post(self, request, *args, **kwargs):
        account_form = BasicSiginInForm(data=request.POST)
        profile_form = EasyRegistrationForm(data=request.POST)
        academic_form = UserAcademicForm(data=request.POST)
        if account_form.is_valid() and profile_form.is_valid() and academic_form.is_valid():
            account_register = account_form.save(commit=False)
            account_form.save()
            profile = profile_form.save(commit=False)
            profile.user = account_register
            academic = academic_form.save(commit=False)
            academic.userProfile = account_register
            if profile.membershipId and profile.membershipId != '':
                profile.isValid = True
            profile.save()
            academic.save()

            # 完成信息保存以后，发送注册成功的邮件
            user_name = '%s %s' % (profile.lastNameEN, profile.firstNameEN)
            # target_email = account_register.email
            # send_emails('Register Successful', user_name, target_email, None)

        else:
            return JsonResponse({
                'success': False,
                'errors': [dict(account_form.errors.items()), dict(profile_form.errors.items()), dict(academic_form.errors.items())]
            })
        return HttpResponseRedirect(reverse('myCSSAhub:hub_regformConfirmation'))


def EasyConfirmationPage(request):
    return render(request, 'myCSSAhub/easy_confirmation.html')


class NewUserSignUpView(View):
    template_name = 'myCSSAhub/registrationForm.html'
    account_form = BasicSiginInForm
    profile_form = UserInfoForm

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect("/hub/home/")
        """Handle GET requests: instantiate a blank version of the form."""
        id = self.kwargs.get('id')
        legacy_data = None
        if id:
            try:
                migration_record = AccountMigration.objects.filter(
                    id=id).first()
                legacy_data = LegacyDataModels.LegacyUsers.objects.get(
                    Q(studentId=migration_record.studentId) & Q(
                        membershipId=migration_record.membershipId)
                )
            except ObjectDoesNotExist:
                print("The user record doesn't exist.")

        return render(request, self.template_name, {'LegacyData': legacy_data})

    def post(self, request, *args, **kwargs):
        account_form = BasicSiginInForm(data=request.POST)
        profile_form = UserInfoForm(data=request.POST, files=request.FILES)
        academic_form = UserAcademicForm(data=request.POST)
        if account_form.is_valid() and profile_form.is_valid() and academic_form.is_valid():
            account_register = account_form.save(commit=False)
            account_form.save()
            profile = profile_form.save(commit=False)
            profile.user = account_register
            academic = academic_form.save(commit=False)
            academic.userProfile = account_register
            if profile.membershipId and profile.membershipId != '':
                profile.isValid = True
            profile.save()
            academic.save()

            # 完成信息保存以后，发送注册成功的邮件
            target_email = account_form.email
            userName = profile_form.firstNameEN + " " + profile_form.lastNameEN
            send_emails('Register Successful', userName, target_email, None)

        else:
            return JsonResponse({
                'success': False,
                'errors': [dict(account_form.errors.items()), dict(profile_form.errors.items()), dict(academic_form.errors.items())]
            })
        return JsonResponse({
            'success': True, })


class migrationView(View):
    template_name = 'myCSSAhub/migration.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        migration_request = MigrationForm(data=request.POST)
        if migration_request.is_valid():
            try:
                legacy_record = LegacyDataModels.LegacyUsers.objects.get(
                    Q(studentId=migration_request['studentId'].value()) & Q(
                        membershipId=migration_request['membershipId'].value())
                )
                if legacy_record.email == migration_request['email'].value() or legacy_record.telNumber == migration_request['telNumber'].value():
                    new_migration = AccountMigration(
                        studentId=migration_request['studentId'].value(),
                        membershipId=migration_request['membershipId'].value()
                    )
                    new_migration.save()
                    return JsonResponse({
                        'success': True,
                        'status': '200',
                        'migrationId': new_migration.id
                    })
            except ObjectDoesNotExist:
                return JsonResponse({
                    'success': False,
                    'status': '404',
                })


class UpdatePasswordView(LoginRequiredMixin, View):
    login_url = 'hub/login/'
    model = UserModels.User
    form_class = PasswordChangeForm
    template_name = 'myCSSAhub/update-password.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': self.form_class(request.user)})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'New Password has been updated!')
            return HttpResponseRedirect('/hub/home')
        else:
            messages.error(request, 'Please double-check your input.')
        return render(request, self.template_name, {'form': form})


class UpdateUserProfileView(LoginRequiredMixin, View):
    login_url = 'hub/login/'
    model = UserModels.UserProfile
    form_class = UserProfileUpdateForm
    template_name = 'myCSSAhub/userInfo.html'

    def get(self, request, *args, **kwargs):
        current_data = self.model.objects.filter(user=request.user).first()
        return render(request, self.template_name, {'form': self.form_class, 'data': current_data})

    def post(self, request, *args, **kwargs):
        current_data = self.model.objects.get(user=request.user)
        form = self.form_class(request.POST or None, request.FILES or None, instance=current_data)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'User Profile has been updated!')
            return HttpResponseRedirect('/hub/home')
        else:
            messages.error(request, 'Please double-check your input.')
        return render(request, self.template_name, {'form': form, 'data': current_data})


class MembershipCardView(LoginRequiredMixin, View):
    login_url = 'hub/login/'
    template_name = 'myCSSAhub/membership-home.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

############################# blog ####################################################


def editBlog(request):
    # 需要判断contentId
    # avatar没有的时候会报错

    NEW_BLOG = -1

    CR_BLOG = "创建Blog"
    CH_BLOG = "更改Blog"
    blogId = request.GET["blogId"]
    try:
        blogId = int(blogId)
    except:
        return bad_request(request)

    ViewBag = {}

    userAuthed = request.user.is_authenticated

    if userAuthed:
        user = request.user
        ViewBag["user"] = {
            "user": request.user,
            "userProfile": UserModels.UserProfile.objects.filter(user=user)[0]
        }
    else:
        return bad_request(request)

    blogContentSingle = -1
    blogTitle = ""
    blogMainContent = ""

    if blogId != NEW_BLOG:
        blogWrittenBys = BlogModels.BlogWrittenBy.objects.filter(blogId=blogId)
        wrote = False
        if blogWrittenBys:
            for blogWrittenBy in blogWrittenBys:
                if userAuthed and blogWrittenBy.userId == request.user:
                    wrote = True

            # user没有写blog
            if wrote == False:
                return permission_denied(request)
        blog = BlogModels.Blog.objects.filter(blogId=blogId)
        if not blog:
            return bad_request(request)
        blogContentSingle = blog[0]
        blogTitle = blogContentSingle.blogTitle
        blogMainContent = blogContentSingle.blogMainContent
        ViewBag["toolTitle"] = CH_BLOG
        curBlogTag = BlogModels.BlogInTag.objects.filter(blogId=blog[0])
        blogTag = json.dumps(
            [x.tagId.tagName for x in curBlogTag]).replace("\\", "\\\\")

        ViewBag["blogTag"] = blogTag
    else:
        ViewBag["toolTitle"] = CR_BLOG

        ViewBag["blogTag"] = []
        pass

    ViewBag["blogId"] = blogId
    ViewBag["blogTitle"] = blogTitle
    ViewBag["blogMainContent"] = blogMainContent

    return render(request, 'myCSSAhub/blogeditpage.html', ViewBag)

############################# AJAX Page Resources #####################################


def GetUserAvatar(request):
    data = {}
    if request.user.is_authenticated:
        userQuery = UserModels.UserProfile.objects.filter(
            user=request.user).first()
        if userQuery is None:
            data['avatarPath'] = "Undefined"
        else:
            data['avatarPath'] = str(userQuery.avatar.url)
    else:
        data['errMsg'] = "Permission Denied"
    return JsonResponse(data)

def CheckEmailIntegrity(request):
    data = {}
    if request.method == 'POST':
        email = request.POST['value']
        userQuery = UserModels.User.objects.filter(email__iexact=email).first()
        if userQuery is None:
            data['result'] = 'Valid'
        else:
            data['result'] = 'Invalid'
    else:
        data = {
            'status': '400', 'reason': 'Bad Requests!'
        }
    return JsonResponse(data)


def CheckTelIntegrity(request):
    data = {}
    if request.method == 'POST':
        telNumber = request.POST['value']
        userQuery = UserModels.User.objects.filter(telNumber=telNumber).first()
        if userQuery is None:
            data['result'] = 'Valid'
        else:
            data['result'] = 'Invalid'
    else:
        data = {
            'status': '400', 'reason': 'Bad Requests!'
        }
    return JsonResponse(data)


def CheckStudentIdIntegrity(request):
    data = {}
    if request.method == 'POST':
        studentId = request.POST['value']
        userQuery = UserModels.UserProfile.objects.filter(
            studentId=studentId).first()
        if userQuery is None:
            data['result'] = 'Valid'
        else:
            data['result'] = 'Invalid'
    else:
        data = {
            'status': '400', 'reason': 'Bad Requests!'
        }
    return JsonResponse(data)


class UserLookup(LoginRequiredMixin, PermissionRequiredMixin, View):
    login_url = '/hub/login/'
    permission_required = ()

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'success': False,
            'status': '400',
        })

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            search = request.POST.get('search', "")
            db_lookup = UserModels.UserProfile.objects.filter(
                Q(firstNameEN__istartswith=search) | Q(lastNameEN__istartswith=search) |
                Q(firstNameCN__istartswith=search) | Q(lastNameCN__istartswith=search) |
                Q(studentId__istartswith=search) |
                Q(user__email__istartswith=search) |
                Q(user__telNumber__icontains=search)
            )
            if db_lookup:
                result_set = []
                for result in db_lookup:
                    lookupResult = {
                        'id': result.user.id,
                        'full_name': str(result.firstNameEN) + " " + str(result.lastNameEN),
                        'full_name_cn': str(result.firstNameCN) + " " + str(result.lastNameCN),
                        'email': str(result.user.email),
                        'text': str(result.user.email)
                    }
                    if result.avatar:
                        lookupResult['avatar'] = str(result.avatar.url)
                    result_set.append(lookupResult)

                return JsonResponse({
                    'success': True,
                    'status': '200',
                    'result': result_set,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'status': '404',
                    'result': None,
                })
        else:
            return JsonResponse({
                'success': False,
                'status': '400',
            })


################################# errors pages ########################################


def bad_request(request):
    return render(request, 'errors/page_400.html')


def permission_denied(request):
    return render(request, 'errors/page_403.html')


def page_not_found(request):
    return render(request, 'errors/page_404.html')


def server_error(request):
    return render(request, 'errors/page_500.html')


def under_dev_notice(request):
    return render(request, 'myCSSAhub/under-dev-function.html')
