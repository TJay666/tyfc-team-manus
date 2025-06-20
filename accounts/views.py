from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import CustomUser

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_approved:
                login(request, user)
                messages.success(request, f'歡迎回來，{user.username}！')
                return redirect('/dashboard/')
            else:
                messages.error(request, '您的帳號尚未通過審核，請聯繫管理員。')
        else:
            messages.error(request, '帳號或密碼錯誤。')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, '您已成功登出。')
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        user_type = request.POST['user_type']
        
        if User.objects.filter(username=username).exists():
            messages.error(request, '此使用者名稱已存在。')
        elif User.objects.filter(email=email).exists():
            messages.error(request, '此電子郵件已被使用。')
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                user_type=user_type,
                is_approved=False
            )
            messages.success(request, '註冊成功！請等待管理員審核。')
            return redirect('login')
    
    return render(request, 'accounts/register.html')

@login_required
def approve_user(request, user_id):
    if request.user.user_type != 'admin':
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()
    messages.success(request, f'使用者 {user.username} 已審核通過。')
    return redirect('/dashboard/')

@login_required
def reject_user(request, user_id):
    if request.user.user_type != 'admin':
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, f'使用者 {user.username} 已被拒絕並刪除。')
    return redirect('/dashboard/')

@login_required
def user_management(request):
    if request.user.user_type != 'admin':
        messages.error(request, '您沒有權限查看此頁面。')
        return redirect('/dashboard/')
    
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_management.html', {'users': users})

@login_required
def edit_user(request, user_id):
    if request.user.user_type != 'admin':
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user_obj.username = request.POST.get('username')
        user_obj.email = request.POST.get('email')
        user_obj.user_type = request.POST.get('user_type')
        user_obj.is_approved = 'is_approved' in request.POST
        
        # 檢查使用者名稱是否重複（排除自己）
        if User.objects.filter(username=user_obj.username).exclude(id=user_obj.id).exists():
            messages.error(request, '此使用者名稱已存在。')
            return render(request, 'accounts/user_edit.html', {'user_obj': user_obj})
        
        # 檢查電子郵件是否重複（排除自己）
        if User.objects.filter(email=user_obj.email).exclude(id=user_obj.id).exists():
            messages.error(request, '此電子郵件已被使用。')
            return render(request, 'accounts/user_edit.html', {'user_obj': user_obj})
        
        user_obj.save()
        messages.success(request, f'使用者 {user_obj.username} 更新成功！')
        return redirect('/accounts/user-management/')
    
    return render(request, 'accounts/user_edit.html', {'user_obj': user_obj})

