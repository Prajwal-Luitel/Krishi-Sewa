from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import Group
from .models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import datetime
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        errors = {}

        # Validate email
        if not username:
            errors["username"] = "username is required"

        # Validate password
        if not password:
            errors["password"] = "Password is required"

        if errors:
            return render(request, "login.html", {"errors": errors})

        user = authenticate(request, username=username, password=password)
        print(user)

        if user is None:
            print("INvalid")
            errors["invalid"] = "Invalid email or password"
            return render(request, "login.html", {"errors": errors})
        print("Success")
        auth_login(request, user)
        return redirect("home")
    return render(request, "login.html")


def register(request):
    if request.method == "POST":
        errors = {}

        full_name = request.POST.get("fullName", "").strip()
        phone = request.POST.get("phone", "").strip()
        gender = request.POST.get("gender")
        dob = request.POST.get("dob")
        email = request.POST.get("email", "").strip()
        username = request.POST.get("username").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirmPassword")
        # profile_pic = request.FILES.get("profilePic")

        # VALIDATIONS

        if not full_name:
            errors["fullName"] = "Full name is required"

        if not phone.isdigit() or len(phone) != 10:
            errors["phone"] = "Phone number must be 10 digits"

        if User.objects.filter(phone=phone).exists():
            errors["phone"] = "phone number already exists"

        if not gender:
            errors["gender"] = "Please select gender"

        if not dob:
            errors["dob"] = "Date of birth is required"
        else:
            dob = datetime.datetime.strptime(dob, "%Y-%m-%d").date()
            if dob >= datetime.date.today():
                errors["dob"] = "Invalid date of birth"

        try:
            validate_email(email)
        except ValidationError:
            errors["email"] = "Invalid email address"

        if User.objects.filter(email=email).exists():
            errors["email"] = "Email already exists"

        if not username:
            errors["username"] = "Please enter username"

        if User.objects.filter(username=username).exists():
            errors["username"] = "username already exists"

        if len(password) < 8:
            errors["password"] = "Password must be at least 8 characters"

        if password != confirm_password:
            errors["confirmPassword"] = "Passwords do not match"

        # if profile_pic:
        #     if profile_pic.size > 5 * 1024 * 1024:
        #         errors["profilePic"] = "Image size must be under 5MB"

        # ---------- IF ERRORS EXIST ----------
        context = {"errors": errors, "old": request.POST}

        if errors:
            return render(request, "register.html", context=context)

        # ---------- CREATE USER ----------
        full_name_parts = full_name.strip().split()
        first_name = full_name_parts[0]
        last_name = " ".join(full_name_parts[1:]) if len(full_name_parts) > 1 else ""

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name = last_name,
            username=username,
            phone=phone,
            gender=gender,
            dob=dob,
        )
        group, _ = Group.objects.get_or_create(name="user")
        user.groups.add(group)

        messages.success(request, "Account created successfully")
        print("Account created successfully")
        return redirect("login")

    return render(request, "register.html")


def home(request):
    return render(request, "home.html")


def logout(request):
    auth_logout(request)
    return redirect('login')
