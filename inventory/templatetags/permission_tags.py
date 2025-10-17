from django import template

register = template.Library()

@register.filter(name='has_perm')
def has_perm(user, permission_type):
    """
    Template filter to check if user has a specific permission
    Usage: {% if user|has_perm:'inventory_read' %}
    """
    if hasattr(user, 'has_permission'):
        return user.has_permission(permission_type)
    return False
