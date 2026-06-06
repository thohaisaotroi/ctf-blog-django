"""
Management command: python manage.py seed_data
Idempotent — skips insertion if data already exists.
Uses Django ORM; BlogUser is now AbstractUser so passwords are properly hashed.
"""
from django.core.management.base import BaseCommand
from blog.models import BlogUser, Category, Post, Tag, PostTag, Comment


class Command(BaseCommand):
    help = 'Seed the database with initial data (idempotent).'

    def handle(self, *args, **options):
        if BlogUser.objects.exists():
            self.stdout.write(self.style.WARNING('Seed data already present — skipping.'))
            return
        self._seed()
        self.stdout.write(self.style.SUCCESS('Seed data inserted successfully.'))

    def _seed(self):
        # ── Users ────────────────────────────────────────────────────────────
        admin = BlogUser.objects.create_superuser(
            username='admin', email='admin@neural-feed.local',
            password='admin123', role='admin',
        )
        n30 = BlogUser.objects.create_user(
            username='n30_user', email='neo@matrix.local',
            password='12345', role='user',
        )
        ghost = BlogUser.objects.create_user(
            username='ghost', email='ghost@shell.local',
            password='54321', role='user',
        )

        # ── Categories ───────────────────────────────────────────────────────
        content_cat = Category.objects.create(
            name='Content Creation', slug='content-creation',
            description='Digital content and creative expression in the cyber age',
        )
        security_cat = Category.objects.create(
            name='Security', slug='security',
            description='Cybersecurity research, tools, and techniques',
        )
        Category.objects.create(
            name='Marketing', slug='marketing',
            description='Digital marketing strategies and growth hacks',
        )
        featured_cat = Category.objects.create(
            name='Featured', slug='featured',
            description='Editor picked featured transmissions',
        )

        # ── Published Posts ───────────────────────────────────────────────────
        p1 = Post.objects.create(
            title='The Art of Digital Infiltration',
            slug='art-of-digital-infiltration',
            content=(
                '<p>In the neon-lit alleyways of cyberspace, the line between art and hacking has never been thinner. '
                'Digital infiltration is not merely a technical exercise — it is an art form.</p>'
                '<h2>The Mindset</h2><p>Every great infiltrator starts with curiosity. '
                'Understanding a system at its deepest level is the prerequisite to mastery.</p>'
                '<h2>The Tools</h2><p>From port scanners to payload crafters, '
                'the modern digital artist has an arsenal unlike anything seen before.</p>'
                '<h2>Ethics &amp; Boundaries</h2><p>Always operate within legal and ethical boundaries.</p>'
            ),
            excerpt='In the neon-lit alleyways of cyberspace, the line between art and hacking has never been thinner.',
            author=admin, category=featured_cat, is_published=True, status='published',
            views=79,
            cover_image='https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80',
        )
        p2 = Post.objects.create(
            title='Best Tools for Network Analysis in 2024',
            slug='best-tools-network-analysis-2024',
            content=(
                '<p>Network analysis is the backbone of modern security research.</p>'
                '<h2>Wireshark</h2><p>Still the gold standard for packet-level inspection.</p>'
                '<h2>nmap &amp; masscan</h2><p>Port scanning at scale.</p>'
                '<h2>Burp Suite</h2><p>The essential web proxy for any security researcher.</p>'
            ),
            excerpt='Network analysis is the backbone of modern security research.',
            author=admin, category=security_cat, is_published=True, status='published',
            views=36,
            cover_image='https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80',
        )
        p3 = Post.objects.create(
            title='Top 5 Cyberpunk Anime That Predicted the Future',
            slug='top-5-cyberpunk-anime',
            content=(
                '<p>Long before "cyberpunk" went mainstream, Japanese animators were exploring dystopian futures.</p>'
                "<h2>Ghost in the Shell (1995)</h2><p>Masamune Shirow's masterpiece.</p>"
                '<h2>Serial Experiments Lain (1998)</h2><p>The dissolution of digital/physical worlds.</p>'
                '<h2>Psycho-Pass (2012)</h2><p>An omniscient AI predicts criminal intent.</p>'
            ),
            excerpt="Long before 'cyberpunk' went mainstream, Japanese animators explored dystopian futures.",
            author=n30, category=featured_cat, is_published=True, status='published',
            views=120,
            cover_image='https://images.unsplash.com/photo-1534972195531-d756b9bfa9f2?w=800&q=80',
        )
        p4 = Post.objects.create(
            title='Understanding Buffer Overflows: A Practical Guide',
            slug='understanding-buffer-overflows',
            content=(
                '<p>Buffer overflow vulnerabilities remain fundamental despite being well-understood for decades.</p>'
                '<h2>What is a Buffer?</h2><p>A contiguous block of memory allocated to hold data.</p>'
                '<h2>Modern Mitigations</h2><p>ASLR, stack canaries, NX/DEP make exploitation harder.</p>'
            ),
            excerpt='Buffer overflow vulnerabilities remain fundamental. A practical guide for security practitioners.',
            author=admin, category=security_cat, is_published=True, status='published',
            views=67,
            cover_image='https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80',
        )
        Post.objects.create(
            title='Neo-Tokyo Ramen: The Underground Bowls You Cannot Miss',
            slug='neo-tokyo-ramen-underground',
            content='<p>In the basement izakayas of Tokyo, a culinary revolution simmers.</p>',
            excerpt='In the basement izakayas of Tokyo, a culinary revolution has been quietly simmering.',
            author=ghost, category=content_cat, is_published=True, status='published',
            views=12,
            cover_image='https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=800&q=80',
        )

        # ── Private post ──────────────────────────────────────────────────────
        Post.objects.create(
            title='Q4 Admin Notes - CLASSIFIED',
            slug='admin-notes-q4-classified',
            content='<p>CLASSIFIED INTERNAL DOCUMENT — System audit results for Q4.</p>',
            excerpt='Internal admin notes — not for public access.',
            author=admin, category=security_cat,
            is_published=False, status='private',
            views=0,
            secret_flag='HTB{Dj4ng0_CVE_2021_35042}',
            cover_image='https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80',
        )

        # ── Draft post ────────────────────────────────────────────────────────
        Post.objects.create(
            title='[DRAFT] Pre-Launch Infrastructure Checklist',
            slug='draft-prelaunch-infra-checklist',
            content=(
                '<p><strong>ACTION REQUIRED — Do not publish</strong></p>'
                '<p>Items to resolve before production launch:</p>'
                '<ul>'
                '<li>Disable test MySQL account <code>pentestuser</code> on database server '
                '(currently has GRANT ALL on all databases, port 3306 exposed)</li>'
                '<li>Close MySQL port 3306 from external network</li>'
                '<li>Rotate <code>ctf_user</code> database password from default</li>'
                '<li>Remove hardcoded credentials from settings.py</li>'
                '</ul>'
                '<p>Assigned to: dev team. Deadline: before go-live.</p>'
            ),
            excerpt='Internal pre-launch checklist — not for public viewing.',
            author=admin, category=security_cat,
            is_published=False, status='draft',
            views=0,
        )

        # ── Tags ─────────────────────────────────────────────────────────────
        tag_data = [
            ('web','web'), ('security','security'), ('tutorial','tutorial'),
            ('hacking','hacking'), ('tools','tools'), ('culture','culture'), ('ctf','ctf'),
        ]
        tags = {slug: Tag.objects.create(name=name, slug=slug) for name, slug in tag_data}

        # ── Post Tags ─────────────────────────────────────────────────────────
        for post, tag_slugs in [
            (p1, ['hacking', 'security', 'ctf']),
            (p2, ['tools', 'security']),
            (p3, ['culture']),
            (p4, ['security', 'tutorial', 'ctf']),
        ]:
            for slug in tag_slugs:
                PostTag.objects.create(post=post, tag=tags[slug])

        # ── Comments ─────────────────────────────────────────────────────────
        for post, user, content in [
            (p1, n30,   'Absolutely mind-bending. The intersection of art and hacking is underexplored.'),
            (p1, ghost, 'Great writeup. Have you covered OSINT methodologies?'),
            (p3, n30,   'Ghost in the Shell changed my life. Pure philosophy disguised as fiction.'),
            (p4, admin, 'This helped me understand ret2libc. Finally clicked!'),
        ]:
            Comment.objects.create(
                post=post, author=user,
                author_name=user.username,
                content=content,
            )
