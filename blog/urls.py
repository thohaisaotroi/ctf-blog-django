from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ── Public Auth ───────────────────────────────────────────────────────────
    path('auth/register/',   views.register,  name='register'),
    path('auth/profile/',    views.user_profile, name='user_profile'),
    path('auth/login/',
         auth_views.LoginView.as_view(template_name='auth/login.html'),
         name='login'),
    path('auth/logout/',
         auth_views.LogoutView.as_view(next_page='/'),
         name='logout'),
    # Password change (requires login)
    path('auth/password-change/',
         auth_views.PasswordChangeView.as_view(
             template_name='auth/password_change.html',
             success_url='/auth/password-change/done/',
         ), name='password_change'),
    path('auth/password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='auth/password_change_done.html',
         ), name='password_change_done'),
    # Password reset via email
    path('auth/password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset_form.html',
             email_template_name='auth/password_reset_email.html',
             html_email_template_name='auth/password_reset_email_html.html',
             subject_template_name='auth/password_reset_subject.txt',
             success_url='/auth/password-reset/done/',
         ), name='password_reset'),
    path('auth/password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/password_reset_done.html',
         ), name='password_reset_done'),
    path('auth/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html',
             success_url='/auth/reset/done/',
         ), name='password_reset_confirm'),
    path('auth/reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_complete.html',
         ), name='password_reset_complete'),

    # ── Public ────────────────────────────────────────────────────────────────
    path('',                              views.index,               name='index'),
    path('blog/',                         views.blog,                name='blog'),
    path('blog/<slug:slug>/',             views.post_detail_by_slug, name='post_detail_slug'),
    path('search/',                       views.search,              name='search'),
    path('about/',                        views.about,               name='about'),
    path('contact/',                      views.contact,             name='contact'),
    path('comment/',                      views.add_comment,         name='add_comment'),
    path('newsletter/subscribe/',         views.newsletter_subscribe, name='newsletter_subscribe'),

    # ── Post interactions ─────────────────────────────────────────────────────
    path('post/like/<int:post_id>/',      views.toggle_like,         name='toggle_like'),

    path('post/',                         views.post_detail,         name='post_detail'),
    path('posts/',                        views.posts_list,          name='posts_list'),

    # ── Cloudinary upload (admin only) ────────────────────────────────────────
    path('admin-upload/image/',           views.admin_upload_image,  name='admin_upload_image'),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path('admin-login/',                  views.admin_login,         name='admin_login'),
    path('admin-dashboard/',              views.admin_dashboard,     name='admin_dashboard'),
    path('admin-logout/',                 views.admin_logout,        name='admin_logout'),
    path('admin-post/create/',               views.admin_post_create,     name='admin_post_create'),
    path('admin-post/edit/<int:post_id>/',   views.admin_post_edit,       name='admin_post_edit'),
    path('admin-post/delete/<int:post_id>/', views.admin_post_delete,     name='admin_post_delete'),
    # User CRUD
    path('admin-user/create/',               views.admin_user_create,     name='admin_user_create'),
    path('admin-user/edit/<int:user_id>/',   views.admin_user_edit,       name='admin_user_edit'),
    path('admin-user/delete/<int:user_id>/', views.admin_user_delete,     name='admin_user_delete'),
    # Category CRUD
    path('admin-category/create/',               views.admin_category_create,   name='admin_category_create'),
    path('admin-category/edit/<int:cat_id>/',    views.admin_category_edit,     name='admin_category_edit'),
    path('admin-category/delete/<int:cat_id>/',  views.admin_category_delete,   name='admin_category_delete'),
]
