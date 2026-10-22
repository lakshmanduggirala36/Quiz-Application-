from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max
from django.db. models import F
from django.core.paginator import Paginator

import requests
import json

from .models import (
    Question,
    Player,
    Result,
    Quiz,
    UserAnswer,
    Subject
)

# =====================================================
# REGISTER PLAYER OR USER
# =====================================================
def register(request):

    if request.method == "POST":

        # QUICK QUIZ (Guest Player)
        if "quick_quiz" in request.POST:

            name = request.POST.get("name")

            if name:
                player = Player.objects.create(name=name)
                request.session["player_id"] = player.id

                return redirect("quiz_settings")

        # REGISTER USER
        if "register" in request.POST:

            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")

            if User.objects.filter(username=username).exists():

                return render(request, "quiz/register.html", {
                    "error": "Username already exists"
                })

            User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            return redirect("/accounts/login/")

    return render(request, "quiz/register.html")


# =====================================================
# DASHBOARD
# =====================================================
@login_required
def dashboard(request):

    results = Result.objects.filter(user=request.user).order_by("created_at")

    total_quizzes = results.count()

    # Database optimized calculations
    avg_score = results.aggregate(Avg("percentage"))["percentage__avg"] or 0
    best_score = results.aggregate(Max("percentage"))["percentage__max"] or 0

    latest = results.last()

    # Recent quizzes
    recent_quizzes = results.order_by("-created_at")[:5]

    # Chart Data
    chart_labels = [r.created_at.strftime("%d %b") for r in results]
    chart_scores = [r.percentage for r in results]

    # Incomplete quizzes
    incomplete = Quiz.objects.filter(
        user=request.user,
        status="in_progress"
    )

    context = {
        "total_quizzes": total_quizzes,
        "avg_score": round(avg_score, 2),
        "best_score": best_score,
        "latest": latest,
        "recent_quizzes": recent_quizzes,
        "chart_labels": chart_labels,
        "chart_scores": chart_scores,
        "incomplete": incomplete
    }

    return render(request, "quiz/dashboard.html", context)


# =====================================================
# QUIZ SETTINGS
# =====================================================
def quiz_settings(request):

    subjects = Subject.objects.all()

    return render(request, "quiz/quiz_settings.html", {
        "subjects": subjects
    })


# =====================================================
# AI QUESTION GENERATOR
# =====================================================
def generate_ai_questions(subject, difficulty, count):

    prompt = f"""
Generate {count} multiple choice quiz questions about {subject}.
Difficulty: {difficulty}

Return JSON format only:

[
 {{
  "question": "Question text",
  "options": ["A","B","C","D"],
  "answer": "Correct option"
 }}
]
"""

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        data = response.json()

        content = data.get("response", "").strip()

        content = content.replace("```json", "").replace("```", "")

        start = content.find("[")
        end = content.rfind("]")

        if start != -1 and end != -1:

            questions = json.loads(content[start:end+1])

            return questions

    except Exception as e:
        print("AI Question Error:", e)

    return []


# =====================================================
# AI EXPLANATION GENERATOR
# =====================================================
def generate_ai_explanation(question, answer):

    prompt = f"""
Explain why the correct answer is correct.

Question:
{question}

Correct Answer:
{answer}

Give a short explanation.
"""

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        data = response.json()

        explanation = data.get("response", "").strip()

        if explanation:
            return explanation

    except Exception as e:
        print("AI Explanation Error:", e)

    return "Explanation not available."


# =====================================================
# START QUIZ
# =====================================================
def quiz_start(request):

    if request.method == "POST":

        subject_id = request.POST.get("subject")
        difficulty = request.POST.get("difficulty")
        question_count = int(request.POST.get("question_count", 5))

        subject = Subject.objects.get(id=subject_id)

        questions = generate_ai_questions(
            subject.name,
            difficulty,
            question_count
        )

        # fallback questions
        if not questions:

            questions = [
                {
                    "question": "What is Python?",
                    "options": ["Snake", "Programming Language", "Car", "Game"],
                    "answer": "Programming Language"
                },
                {
                    "question": "What is Django?",
                    "options": ["Framework", "Database", "Browser", "OS"],
                    "answer": "Framework"
                }
            ]

        quiz = Quiz.objects.create(
            user=request.user if request.user.is_authenticated else None,
            player=Player.objects.filter(
                id=request.session.get("player_id")
            ).first(),
            subject=subject,
            difficulty=difficulty,
            duration=60
        )

        request.session["quiz_id"] = quiz.id
        request.session["questions"] = questions
        request.session["start_time"] = timezone.now().timestamp()

        return render(request, "quiz/quiz_start.html", {
            "questions": questions,
            "duration": 60
        })

    return redirect("quiz_settings")


# =====================================================
# QUIZ RESULT
# =====================================================
def quiz_result(request):

    if request.method == "POST":

        questions = request.session.get("questions", [])
        quiz_id = request.session.get("quiz_id")

        if not quiz_id:
            return redirect("quiz_settings")

        quiz = Quiz.objects.get(id=quiz_id)

        score = 0
        wrong_answers = []

        start_time = request.session.get("start_time")

        time_taken = 0
        if start_time:
            time_taken = int(timezone.now().timestamp() - start_time)

        result = Result.objects.create(
            user=request.user if request.user.is_authenticated else None,
            player=quiz.player,
            quiz=quiz,
            score=0,
            total=len(questions),
            percentage=0,
            time_taken=time_taken
        )

        for i, q in enumerate(questions):

            selected = request.POST.get(f"q{i}")
            correct = q["answer"]

            is_correct = selected == correct

            explanation = ""

            if is_correct:
                score += 1

            else:

                explanation = generate_ai_explanation(
                    q["question"],
                    correct
                )

                wrong_answers.append({
                    "question": q["question"],
                    "correct_answer": correct,
                    "your_answer": selected,
                    "explanation": explanation
                })

            question_obj = Question.objects.create(
                subject=quiz.subject,
                difficulty=quiz.difficulty,
                question_text=q["question"],
                option1=q["options"][0],
                option2=q["options"][1],
                option3=q["options"][2],
                option4=q["options"][3],
                correct_answer=correct
            )

            UserAnswer.objects.create(
                result=result,
                question=question_obj,
                selected_answer=selected,
                is_correct=is_correct,
                explanation=explanation
            )

        total = len(questions)

        percentage = round((score / total) * 100, 2) if total else 0

        result.score = score
        result.percentage = percentage
        result.save()

        quiz.status = "completed"
        quiz.save()

        return render(request, "quiz/quiz_result.html", {
            "score": score,
            "total": total,
            "percentage": percentage,
            "wrong_answers": wrong_answers
        })

    return redirect("quiz_settings")


# =====================================================
# LEADERBOARD
# =====================================================
def leaderboard(request):

    results = Result.objects.order_by("-percentage", "-score")

    leaderboard_data = []

    rank = 1

    for r in results:

        leaderboard_data.append({
            "rank": rank,
            "name": r.user.username if r.user else r.player.name,
            "score": f"{r.score}/{r.total}",
            "percentage": r.percentage,
            "is_me": request.user.is_authenticated and r.user == request.user
        })

        rank += 1
        return render(request, "quiz/leaderboard.html", {
            "leaderboard": leaderboard_data
            })

# =====================================================
# QUIZ HISTORY
# =====================================================
from django.core.paginator import Paginator

@login_required
def quiz_history(request):

    results = Result.objects.filter(user=request.user).order_by("-created_at")

    # Search by subject
    search = request.GET.get("search")

    if search:
        results = results.filter(quiz__subject__name__icontains=search)

    # Sorting
    sort = request.GET.get("sort")

    if sort == "score":
        results = results.order_by("-percentage")

    elif sort == "date":
        results = results.order_by("-created_at")

    # Pagination
    paginator = Paginator(results, 5)  # 5 quizzes per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "quiz/history.html", {
        "page_obj": page_obj,
        "search": search,
        "sort": sort
    })
    
    
    from django.contrib.auth.decorators import login_required

@login_required
def profile(request):

    return render(request, "quiz/profile.html", {
        "user": request.user
    })
    
    
    
def categories(request):

    subjects = Subject.objects.all()

    return render(request, "quiz/categories.html", {
        "subjects": subjects
    })