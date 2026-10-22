from django.urls import path
from . import views

urlpatterns = [

    # Registration Page
    path("", views.register, name="register"),

    # Quiz Settings
    path("settings/", views.quiz_settings, name="quiz_settings"),

    # Start Quiz
    path("start/", views.quiz_start, name="quiz_start"),

    # Submit Quiz / Result
    path("result/", views.quiz_result, name="quiz_result"),

    # Leaderboard
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    
    path("dashboard/", views.dashboard, name="dashboard"),
    
    path("history/", views.quiz_history, name="quiz_history"),
    
    path("profile/", views.profile, name="profile"),
    
    path("categories/", views.categories, name="categories"),

]