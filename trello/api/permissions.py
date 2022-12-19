from rest_framework.permissions import BasePermission, SAFE_METHODS
from trello.models import MemberDesk


class IsDeskOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return obj.author
        return obj.author == request.user

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsDeskOwnerOrMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        is_member = obj.members.filter(member=request.user).exists()
        return obj.author == request.user or is_member

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
