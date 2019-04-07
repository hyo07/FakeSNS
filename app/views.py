from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import generic
from .forms import ArticleForm
from .models import Article, Profile, Like, BlackListM


# トップページ
def top(request):
    return render(request, "app/index.html")


# 一覧表示
class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = "app/index.html"
    model = Article
    paginate_by = 10

    # 新規投稿を上に
    def get_queryset(self):
        return Article.objects.all().order_by("-created_at")

    # ブラックリストは表示しない
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ブラックリスト読み込み
        bl = BlackListM.objects.filter(add_user_id=self.request.user.id)
        bl_list = []
        for b in bl:
            bl_list.append(b.target_user_id)
        context["black_list"] = bl_list

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


# 新規投稿
class CreateView(LoginRequiredMixin, generic.CreateView):
    template_name = "app/create.html"
    model = Article
    form_class = ArticleForm
    success_url = reverse_lazy("app:index")

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "投稿しました")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "投稿に失敗しました")


# 編集
class UpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "app/update.html"
    model = Article
    form_class = ArticleForm
    success_url = reverse_lazy("app:index")

    # 投稿したユーザーとスーパーユーザーのみが編集を可能に
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied("あなたはこの投稿を編集できません")
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "変更を保存しました")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "変更の保存に失敗しました")


# 削除
class DeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = "app/delete.html"
    model = Article
    success_url = reverse_lazy("app:index")

    # 投稿したユーザーとスーパーユーザーのみが削除を可能に
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied("あなたはこの投稿を削除できません")
        return super(DeleteView, self).dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "投稿を削除しました")
        return super().delete(request, *args, **kwargs)


# いいね機能
@login_required
def like(request, pk):
    if request.method == 'POST':
        # いいね追加
        if "add_like" in request.POST:
            add_like = Like(article_id=pk, user_id=request.user.id)
            add_like.save()
            return redirect("app:index")

        # いいね削除
        elif "del_like" in request.POST:
            del_like = Like.objects.get(article_id=pk, user_id=request.user.id)
            del_like.delete()
            return redirect("app:index")
