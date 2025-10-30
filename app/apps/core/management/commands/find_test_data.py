"""
Management command to identify potential test/dummy data across all models.
"""
from django.core.management.base import BaseCommand
from django.apps import apps
from apps.blog.models import BlogPost, Category
from apps.projects.models import Project, ProjectCategory
from apps.comments.models import Comment


class Command(BaseCommand):
    help = 'Audit database to find potential test/dummy data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete identified test data (use with caution!)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== TEST DATA AUDIT REPORT ===\n'))

        total_found = 0
        delete_mode = options['delete']

        if delete_mode:
            self.stdout.write(self.style.WARNING('⚠️  DELETE MODE ENABLED - Will delete identified test data!\n'))

        # Check BlogPosts
        self.stdout.write(self.style.HTTP_INFO('📝 Blog Posts:'))
        test_posts = []

        # Known test entries
        known_test_names = ['fewest', 'test', 'dummy', 'sample', 'example', 'asdf', 'qwer']
        for post in BlogPost.objects.all():
            is_test = False
            reasons = []

            # Check for gibberish or single-word titles
            if len(post.title.split()) == 1 and len(post.title) < 10:
                is_test = True
                reasons.append('single-word title')

            # Check for known test names
            if any(test_name in post.title.lower() for test_name in known_test_names):
                is_test = True
                reasons.append('known test name')

            # Check for very short content
            if len(post.content) < 50:
                is_test = True
                reasons.append('very short content (<50 chars)')

            # Check if title is all lowercase gibberish
            if post.title.islower() and not ' ' in post.title and len(post.title) < 15:
                is_test = True
                reasons.append('lowercase gibberish')

            if is_test:
                test_posts.append((post, reasons))
                total_found += 1
                self.stdout.write(f'  ❌ "{post.title}" (ID: {post.id}) - {", ".join(reasons)}')
                if delete_mode:
                    post.delete()
                    self.stdout.write(self.style.ERROR(f'     DELETED!'))

        if not test_posts:
            self.stdout.write(self.style.SUCCESS('  ✅ No test posts found'))

        # Check Categories
        self.stdout.write(self.style.HTTP_INFO('\n📂 Blog Categories:'))
        test_categories = []

        for category in Category.objects.all():
            is_test = False
            reasons = []

            # Check for single-character or very short names
            if len(category.name) <= 3:
                is_test = True
                reasons.append('very short name (≤3 chars)')

            # Check for known test names
            if any(test_name in category.name.lower() for test_name in known_test_names):
                is_test = True
                reasons.append('known test name')

            # Check for gibberish (all lowercase, no spaces, short)
            if category.name.islower() and len(category.name) < 10:
                is_test = True
                reasons.append('lowercase gibberish')

            if is_test:
                test_categories.append((category, reasons))
                total_found += 1
                self.stdout.write(f'  ❌ "{category.name}" (ID: {category.id}) - {", ".join(reasons)}')
                if delete_mode:
                    category.delete()
                    self.stdout.write(self.style.ERROR(f'     DELETED!'))

        if not test_categories:
            self.stdout.write(self.style.SUCCESS('  ✅ No test categories found'))

        # Check Projects
        self.stdout.write(self.style.HTTP_INFO('\n🚀 Projects:'))
        test_projects = []

        for project in Project.objects.all():
            is_test = False
            reasons = []

            # Check for gibberish titles
            if not ' ' in project.title and len(project.title) < 15 and project.title.islower():
                is_test = True
                reasons.append('gibberish title')

            # Check for known test patterns
            if any(test_name in project.title.lower() for test_name in known_test_names + ['gjwkenlkn', 'fwefew', 'asdfgh', 'qwerty']):
                is_test = True
                reasons.append('known test pattern')

            # Check for very short description
            if len(project.short_description) < 20:
                is_test = True
                reasons.append('very short description (<20 chars)')

            # Check for empty/minimal content
            if len(project.description) < 30:
                is_test = True
                reasons.append('minimal content (<30 chars)')

            if is_test:
                test_projects.append((project, reasons))
                total_found += 1
                self.stdout.write(f'  ❌ "{project.title}" (ID: {project.id}) - {", ".join(reasons)}')
                if delete_mode:
                    project.delete()
                    self.stdout.write(self.style.ERROR(f'     DELETED!'))

        if not test_projects:
            self.stdout.write(self.style.SUCCESS('  ✅ No test projects found'))

        # Check Project Categories
        self.stdout.write(self.style.HTTP_INFO('\n📁 Project Categories:'))
        test_proj_categories = []

        for category in ProjectCategory.objects.all():
            is_test = False
            reasons = []

            # Check for very short names
            if len(category.name) <= 3:
                is_test = True
                reasons.append('very short name (≤3 chars)')

            # Check for known test names
            if any(test_name in category.name.lower() for test_name in known_test_names + ['fwefew', 'asdfgh']):
                is_test = True
                reasons.append('known test pattern')

            # Check for gibberish
            if category.name.islower() and not ' ' in category.name and len(category.name) < 10:
                is_test = True
                reasons.append('gibberish')

            if is_test:
                test_proj_categories.append((category, reasons))
                total_found += 1
                self.stdout.write(f'  ❌ "{category.name}" (ID: {category.id}) - {", ".join(reasons)}')
                if delete_mode:
                    category.delete()
                    self.stdout.write(self.style.ERROR(f'     DELETED!'))

        if not test_proj_categories:
            self.stdout.write(self.style.SUCCESS('  ✅ No test project categories found'))

        # Check for orphaned/test comments
        self.stdout.write(self.style.HTTP_INFO('\n💬 Comments:'))
        test_comments = []

        for comment in Comment.objects.all():
            is_test = False
            reasons = []

            # Check for very short content
            if len(comment.content) < 10:
                is_test = True
                reasons.append('very short (<10 chars)')

            # Check for test patterns
            if any(test_name in comment.content.lower() for test_name in ['test', 'asdf', 'qwer', 'dummy']):
                is_test = True
                reasons.append('test pattern in content')

            if is_test:
                test_comments.append((comment, reasons))
                total_found += 1
                self.stdout.write(f'  ❌ Comment ID {comment.id} by {comment.user.username} - {", ".join(reasons)}')
                if delete_mode:
                    comment.delete()
                    self.stdout.write(self.style.ERROR(f'     DELETED!'))

        if not test_comments:
            self.stdout.write(self.style.SUCCESS('  ✅ No test comments found'))

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n=== SUMMARY ==='))
        self.stdout.write(f'Total potential test entries found: {total_found}')

        if delete_mode:
            self.stdout.write(self.style.ERROR(f'\n🗑️  {total_found} test entries have been DELETED!'))
        else:
            self.stdout.write(self.style.WARNING(f'\n💡 Run with --delete flag to remove these entries'))
            self.stdout.write(self.style.WARNING('   Example: python manage.py find_test_data --delete'))

        self.stdout.write('')
