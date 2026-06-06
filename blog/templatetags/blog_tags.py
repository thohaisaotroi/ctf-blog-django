import re
import markdown as _md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag('_comment_thread.html')
def render_comment_thread(comments, depth=0):
    """Recursively render a nested comment thread."""
    return {'comments': comments, 'depth': min(depth, 4)}


@register.filter
def upper_underscore(value):
    """Convert 'Content Creation' → 'CONTENT_CREATION'."""
    return str(value).upper().replace(' ', '_')


@register.filter
def read_time(content):
    """Estimate reading time in minutes from HTML content."""
    text = re.sub(r'<[^>]+>', '', content or '')
    words = len(text.split())
    return max(1, words // 200 + 1)


@register.filter
def markdownify(value):
    """Render markdown text to safe HTML."""
    html = _md.markdown(value or '', extensions=['fenced_code', 'tables', 'nl2br'])
    return mark_safe(html)
