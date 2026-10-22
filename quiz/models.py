from django.db import models
from django.contrib.auth.models import User


# ==================================
# PLAYER MODEL (Optional Guest User)
# ==================================
class Player(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# ==================================
# SUBJECT MODEL
# ==================================
class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# ==================================
# QUESTION MODEL
# ==================================
class Question(models.Model):

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    difficulty = models.CharField(
        max_length=20,
        choices=[
            ("easy", "Easy"),
            ("medium", "Medium"),
            ("hard", "Hard")
        ]
    )

    question_text = models.TextField()

    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)

    correct_answer = models.CharField(max_length=200)

    explanation = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def get_options(self):
        return [
            self.option1,
            self.option2,
            self.option3,
            self.option4
        ]

    def __str__(self):
        return self.question_text[:50]


# ==================================
# QUIZ SESSION MODEL
# ==================================
class Quiz(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )

    difficulty = models.CharField(max_length=20)

    duration = models.IntegerField()  # seconds

    status = models.CharField(
        max_length=20,
        choices=[
            ("in_progress", "In Progress"),
            ("completed", "Completed")
        ],
        default="in_progress"
    )

    current_question = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.subject.name}"
        elif self.player:
            return f"{self.player.name} - {self.subject.name}"
        return "Quiz Session"


# ==================================
# RESULT MODEL
# ==================================
class Result(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE
    )

    score = models.IntegerField()

    total = models.IntegerField()

    percentage = models.FloatField()

    time_taken = models.IntegerField()  # seconds

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.percentage}%"
        elif self.player:
            return f"{self.player.name} - {self.percentage}%"
        return "Result"


# ==================================
# USER ANSWER MODEL
# ==================================
class UserAnswer(models.Model):

    result = models.ForeignKey(
        Result,
        on_delete=models.CASCADE
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )

    selected_answer = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    is_correct = models.BooleanField()

    explanation = models.TextField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.question.question_text[:30]}"