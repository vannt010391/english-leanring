from datetime import timedelta
from django.utils import timezone
from django.db.models import Count

from .models import (
    LearningPlan, LearningPlanVocabulary, LearningProgress,
    PracticeSession, LearnerAnalytics, Notification
)


class AnalyticsService:
    """Service for calculating and managing learner analytics."""

    @staticmethod
    def get_or_create_analytics(user, learning_plan=None):
        """Get or create analytics for a user, optionally for a specific plan."""
        analytics, created = LearnerAnalytics.objects.get_or_create(
            user=user,
            learning_plan=learning_plan
        )

        # Recalculate if stale (older than 1 hour)
        if created or (timezone.now() - analytics.updated_at).total_seconds() > 3600:
            AnalyticsService.calculate_analytics(analytics)

        return analytics

    @staticmethod
    def calculate_analytics(analytics):
        """Calculate all analytics metrics for a user/plan."""
        user = analytics.user
        plan = analytics.learning_plan
        today = timezone.now().date()

        # Calculate study streak
        streak, longest = AnalyticsService._calculate_streak(user, plan)
        analytics.study_streak = streak
        analytics.longest_streak = max(longest, analytics.longest_streak)

        # Calculate mastery rate
        if plan:
            total = LearningPlanVocabulary.objects.filter(learning_plan=plan).count()
            mastered = LearningPlanVocabulary.objects.filter(
                learning_plan=plan, status='mastered'
            ).count()
        else:
            total = LearningPlanVocabulary.objects.filter(
                learning_plan__user=user
            ).count()
            mastered = LearningPlanVocabulary.objects.filter(
                learning_plan__user=user, status='mastered'
            ).count()

        analytics.mastery_rate = (mastered / total * 100) if total > 0 else 0
        analytics.total_words_mastered = mastered

        # Calculate review frequency
        if plan:
            reviews = LearningPlanVocabulary.objects.filter(
                learning_plan=plan
            ).aggregate(total_reviews=Count('review_count'))
            vocab_count = LearningPlanVocabulary.objects.filter(learning_plan=plan).count()
        else:
            reviews = LearningPlanVocabulary.objects.filter(
                learning_plan__user=user
            ).aggregate(total_reviews=Count('review_count'))
            vocab_count = LearningPlanVocabulary.objects.filter(
                learning_plan__user=user
            ).count()

        total_reviews = reviews['total_reviews'] or 0
        analytics.review_frequency = (total_reviews / vocab_count) if vocab_count > 0 else 0

        # Count practice sessions
        if plan:
            analytics.total_practice_sessions = PracticeSession.objects.filter(
                user=user, learning_plan=plan
            ).count()
        else:
            analytics.total_practice_sessions = PracticeSession.objects.filter(
                user=user
            ).count()

        # Get last study date
        last_progress = LearningProgress.objects.filter(
            user=user,
            words_studied__gt=0
        )
        if plan:
            last_progress = last_progress.filter(learning_plan=plan)

        last_progress = last_progress.order_by('-date').first()
        analytics.last_study_date = last_progress.date if last_progress else None

        # Assess risk
        risk_level, risk_factors = AnalyticsService._assess_risk(
            analytics.study_streak,
            analytics.mastery_rate,
            analytics.last_study_date,
            user,
            plan
        )
        analytics.risk_level = risk_level
        analytics.risk_factors = risk_factors

        analytics.save()

        # Generate notifications if needed
        if risk_level in ['medium', 'high']:
            AnalyticsService._maybe_create_notification(user, plan, risk_level, risk_factors)

        return analytics

    @staticmethod
    def _calculate_streak(user, plan=None):
        """Calculate current and longest study streak."""
        today = timezone.now().date()

        progress_query = LearningProgress.objects.filter(
            user=user,
            words_studied__gt=0
        )
        if plan:
            progress_query = progress_query.filter(learning_plan=plan)

        progress_dates = set(
            progress_query.values_list('date', flat=True)
        )

        if not progress_dates:
            return 0, 0

        # Calculate current streak
        current_streak = 0
        check_date = today

        # Check if studied today or yesterday
        if check_date not in progress_dates:
            check_date = today - timedelta(days=1)
            if check_date not in progress_dates:
                # No recent study, streak is 0
                return 0, AnalyticsService._calculate_longest_streak(progress_dates)

        while check_date in progress_dates:
            current_streak += 1
            check_date -= timedelta(days=1)

        longest = AnalyticsService._calculate_longest_streak(progress_dates)
        return current_streak, max(current_streak, longest)

    @staticmethod
    def _calculate_longest_streak(dates):
        """Calculate the longest streak from a set of dates."""
        if not dates:
            return 0

        sorted_dates = sorted(dates)
        longest = 1
        current = 1

        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1

        return longest

    @staticmethod
    def _assess_risk(streak, mastery_rate, last_study_date, user, plan):
        """Determine risk level based on multiple factors."""
        risk_factors = []
        risk_score = 0
        today = timezone.now().date()

        # Check for missed days
        if last_study_date:
            days_missed = (today - last_study_date).days
            if days_missed >= 7:
                risk_factors.append(f'missed_{days_missed}_days')
                risk_score += 3
            elif days_missed >= 3:
                risk_factors.append(f'missed_{days_missed}_days')
                risk_score += 2
            elif days_missed >= 1:
                risk_factors.append(f'missed_{days_missed}_days')
                risk_score += 1

        # Check streak
        if streak == 0:
            risk_factors.append('no_current_streak')
            risk_score += 1

        # Check mastery rate
        if mastery_rate < 20:
            risk_factors.append('low_mastery_rate')
            risk_score += 2
        elif mastery_rate < 40:
            risk_factors.append('moderate_mastery_rate')
            risk_score += 1

        # Check review ratio
        if plan:
            total = LearningPlanVocabulary.objects.filter(learning_plan=plan).count()
            review_required = LearningPlanVocabulary.objects.filter(
                learning_plan=plan, status='review_required'
            ).count()
        else:
            total = LearningPlanVocabulary.objects.filter(
                learning_plan__user=user
            ).count()
            review_required = LearningPlanVocabulary.objects.filter(
                learning_plan__user=user, status='review_required'
            ).count()

        if total > 0:
            review_ratio = review_required / total
            if review_ratio > 0.5:
                risk_factors.append('high_review_ratio')
                risk_score += 2
            elif review_ratio > 0.3:
                risk_factors.append('moderate_review_ratio')
                risk_score += 1

        # Determine risk level
        if risk_score >= 4:
            return 'high', risk_factors
        elif risk_score >= 2:
            return 'medium', risk_factors
        return 'low', risk_factors

    @staticmethod
    def _maybe_create_notification(user, plan, risk_level, risk_factors):
        """Create a notification if one hasn't been sent recently."""
        today = timezone.now().date()

        # Check if notification already sent today
        existing = Notification.objects.filter(
            user=user,
            notification_type='risk_alert',
            created_at__date=today
        )
        if plan:
            existing = existing.filter(learning_plan=plan)

        if existing.exists():
            return

        # Create notification based on risk level
        if risk_level == 'high':
            title = "Time to get back on track!"
            message = "You haven't studied in a while. A quick review session can help reinforce what you've learned. Let's get started!"
        else:
            title = "Keep up the momentum!"
            message = "Don't let your progress slip. Take a few minutes to review some vocabulary today."

        Notification.objects.create(
            user=user,
            notification_type='risk_alert',
            title=title,
            message=message,
            learning_plan=plan
        )

    @staticmethod
    def get_recommendations(analytics):
        """Generate recommendations based on analytics."""
        recommendations = []

        if 'missed' in str(analytics.risk_factors):
            recommendations.append({
                'type': 'study_reminder',
                'message': 'Try to study at least a few words every day to maintain your streak.',
                'action': 'Start a quick study session'
            })

        if 'low_mastery' in str(analytics.risk_factors) or 'moderate_mastery' in str(analytics.risk_factors):
            recommendations.append({
                'type': 'practice_suggestion',
                'message': 'Practice more to improve your mastery rate.',
                'action': 'Start a practice session'
            })

        if 'review' in str(analytics.risk_factors):
            recommendations.append({
                'type': 'review_suggestion',
                'message': 'You have words that need review. Focus on these to solidify your learning.',
                'action': 'Review flagged words'
            })

        if analytics.study_streak >= 7:
            recommendations.append({
                'type': 'encouragement',
                'message': f'Great job! You have a {analytics.study_streak}-day streak. Keep it up!',
                'action': None
            })

        if not recommendations:
            recommendations.append({
                'type': 'encouragement',
                'message': 'You\'re doing well! Keep up the consistent practice.',
                'action': None
            })

        return recommendations

    @staticmethod
    def create_streak_notification(user, streak):
        """Create notification for streak achievements."""
        milestones = [7, 14, 30, 50, 100]

        if streak in milestones:
            Notification.objects.create(
                user=user,
                notification_type='streak_achievement',
                title=f'{streak}-Day Streak!',
                message=f'Congratulations! You\'ve maintained a {streak}-day study streak. Keep up the amazing work!'
            )
