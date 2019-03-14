from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from app.models import Profile, Article, Like
from app.forms import ProfileForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from libs import BlackList
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


# アカウント新規作成
class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'accounts/signup.html'


# ユーザー情報見る
class UserDetail(LoginRequiredMixin, generic.DetailView):
    model = get_user_model()
    template_name = 'accounts/user_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            str_bl = BlackList.read_bl(self.request.user.profile.black_list)
            int_bl = BlackList.str_to_int(str_bl)
            context["black_list"] = int_bl
            context["profile"] = True
            if int_bl:
                user_list = []
                for u in int_bl:
                    user_list.append(User.objects.get(id=u))
                context["user_list"] = user_list
                context["mix_list"] = zip(int_bl, user_list)
        except Profile.DoesNotExist:
            context["profile"] = False

        try:
            context["my_article"] = Article.objects.filter(author=self.kwargs["pk"]).order_by("-created_at")
        except Article.DoesNotExist:
            context["my_article"] = False

        return context


# ユーザー情報を変更
class UserUpdate(LoginRequiredMixin, generic.UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'accounts/user_update.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied("あなたはこのユーザー情報を編集できません")
        if not Profile.objects.filter(id=self.kwargs["pk"]):
            raise PermissionDenied("まだユーザー情報が登録されていません")
        return super(UserUpdate, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "更新しました")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "更新に失敗しました")

    def get_success_url(self):
        obj = self.get_object()
        return reverse_lazy('accounts:user_detail', kwargs={"pk": obj.user.id})


# ユーザー情報を登録
class UserCreate(LoginRequiredMixin, generic.CreateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'accounts/user_create.html'
    success_url = reverse_lazy("accounts:user_detail")

    def dispatch(self, request, *args, **kwargs):
        if Profile.objects.filter(user_id=self.kwargs["pk"]):
            raise PermissionDenied("すでにユーザー情報が登録されています")
        if Profile.objects.filter(user_id=self.request.user.id):
            raise PermissionDenied("あなたはこのユーザー情報を登録できません")
        return super(UserCreate, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "ユーザー情報を登録しました")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "ユーザー情報の登録に失敗しました")
        return reverse_lazy('accounts:password_change')

    def get_success_url(self):
        return reverse_lazy('accounts:user_detail', kwargs={"pk": self.request.user.id})


# パスワードを変更
class PasswordChange(LoginRequiredMixin, PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = "accounts/password_change.html"

    def form_valid(self, form):
        messages.success(self.request, "パスワードを変更しました")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('accounts:password_change_done', kwargs={"pk": self.request.user.id})


# 変更できた告知
class PasswordChangeDone(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"


# ブラックリスト追加 / 削除
@login_required
def black_list(request, pk):
    if request.method == 'POST':
        req_profile = Profile.objects.get(user_id=request.user.id)
        text = req_profile.black_list

        if "add_bl" in request.POST:
            new_bl = BlackList.add_bl(text, str(pk))
            profile = Profile.objects.get(user_id=request.user.id)
            profile.black_list = new_bl
            profile.save()
            return redirect('accounts:user_detail', pk=request.user.id)

        elif "del_bl" in request.POST:
            new_bl = BlackList.delete_bl(text, str(pk))
            profile = Profile.objects.get(user_id=request.user.id)
            profile.black_list = new_bl
            profile.save()
            return redirect('accounts:user_detail', pk=request.user.id)


# いいねした記事一覧
class MyLikeArticle(LoginRequiredMixin, generic.ListView):
    template_name = "accounts/mylike.html"
    model = Article
    paginate_by = 5

    def get_context_data(self, **kwargs):
        # いいねした投稿をフィルター
        context = super().get_context_data(**kwargs)
        my_like = Like.objects.filter(user_id=self.kwargs["pk"]).order_by("-article_id")
        res_list = []
        for my in my_like:
            article = Article.objects.get(id=my.article_id)
            res_list.append(article)
        context["like_list"] = res_list

        # いいね
        like_dic = {}
        status_dic = {}
        articles = Article.objects.all()
        for article in articles:
            # いいね数読み込み
            try:
                like_count = Like.objects.filter(article_id=article.id).count()
                like_dic[article.id] = like_count
            except Like.DoesNotExist:
                like_dic[article.id] = 0

            # リクエストユーザーがいいねしたかどうか
            try:
                # いいねしてる
                Like.objects.filter(article_id=article.id).get(user_id=self.request.user.id)
                status_dic[article.id] = True
            except Like.DoesNotExist:
                # いいねしてない
                status_dic[article.id] = False
        context["likes"] = like_dic
        context["status_dic"] = status_dic

        return context


# いいね機能
@login_required
def dellike(request, pk):
    if request.method == 'POST':
        # いいね追加
        if "add_like" in request.POST:
            add_like = Like(article_id=pk, user_id=request.user.id)
            add_like.save()
            return redirect("accounts:mylike", pk=request.user.id)

        # いいね削除
        elif "del_like" in request.POST:
            del_like = Like.objects.get(article_id=pk, user_id=request.user.id)
            del_like.delete()
            return redirect("accounts:mylike", pk=request.user.id)
