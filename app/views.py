from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from supabase import create_client
import uuid
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
# Create your views here.
def supabase_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            # Authenticate with Supabase
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})

            if user and user.user:  # Successful login
                user_id = user.user.id

                # Store session info
                request.session["user_id"] = user_id
                request.session["email"] = email

                # Fetch teacher record
                teacher = supabase.table("Teacher").select("*").eq("user_id", user_id).execute()

                if teacher.data and len(teacher.data) > 0:
                    request.session["teacher_name"] = teacher.data[0].get("name")

                # Redirect to home page after successful login
                return redirect("home_page")

            else:
                messages.error(request, "Invalid email or password")

        except Exception as e:
            messages.error(request, f"Login failed: {str(e)}")

    # If GET request or login fails, render login form again
    return render(request, "login.html")

def supabase_signup(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        teacher_id = request.POST.get("teacher_id").strip()

        try:
            # 1. Sign up user
            user_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
            })

            user = user_response.user
            session = user_response.session  # May be None if email confirmation is enabled

            if session is None:
                # Email confirmation required case
                # Render a page telling user to check email before login
                return render(request, "signup.html", {
                    "message": "Please check your email to confirm your account before logging in."
                })

            # 2. Set Supabase session for authenticated requests
            supabase.auth.set_session(session.access_token, session.refresh_token)

            user_id = user.id
            request.session["user_id"] = user_id
            request.session["email"] = email

            # 3. Check if teacher_id exists and is unlinked
            existing = supabase.table("Teacher") \
                .select("user_id") \
                .eq("teacher_id", teacher_id) \
                .execute()

            if not existing.data:
                return render(request, "signup.html", {"error": "Teacher not found"})

            if existing.data[0]["user_id"] is not None:
                return render(request, "signup.html", {"error": "This teacher is already linked to a user."})

            # 4. Update teacher row with user_id
            update_response = supabase.table("Teacher") \
                .update({"user_id": user_id}) \
                .eq("teacher_id", teacher_id) \
                .execute()

            if update_response.error:
                return render(request, "signup.html", {"error": f"Failed to link teacher: {update_response.error.message}"})

            # 5. Redirect to home on success
            return redirect("home")

        except Exception as e:
            print("Signup error:", e)
            return render(request, "signup.html", {"error": str(e)})

    return render(request, "signup.html")

def supabase_logout(request):
    request.session.flush()
    return redirect("login")

def home_page(request):
    user_id = request.session.get("user_id")  # UUID from Supabase Auth
    email = request.session.get("email")

    if not user_id:
        return redirect("login")

    teacher = None
    try:
        print("Looking for teacher with user_id:", user_id)

        response = (
            supabase.table("Teacher")  # lowercase table name if needed
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        if response.data:
            teacher = response.data[0]
        else:
            print("No teacher found with user_id:", user_id)

        print("Teacher query response:", response.data)

    except Exception as e:
        print("Error fetching teacher:", e)

    return render(
        request,
        "home.html",
        {
            "teacher": teacher,
            "email": email,
        },
    )

