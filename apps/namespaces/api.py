from django.db.models import Q
from django.utils.translation import ugettext as _

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from rbac.models import RoleNamespaceBinding, RoleOrgBinding
from namespaces.models import Namespace
from namespaces.serializers import NamespaceSerializer


class NamespaceViewSet(ModelViewSet):

    permission_classes = (IsAuthenticated,)

    filter_fields = ('name',)
    search_fields = filter_fields
    ordering_fields = ('name', 'date_created')

    model = Namespace
    queryset = Namespace.objects.all()
    serializer_class = NamespaceSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_build_in:
            return self.filter_queryset(self.queryset)
        namespace_ids = RoleNamespaceBinding.objects.filter(user=user).values_list('namespace').distinct()
        org_ids = RoleOrgBinding.objects.filter(user=user).values_list('org').distinct()
        return self.filter_queryset(self.queryset).\
            filter(Q(id__in=namespace_ids) | Q(org_id__in=org_ids)).distinct()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.account_set.all().exists():
            return Response({'msg': _('Please delete the sub items first')},
                            status=status.HTTP_400_BAD_REQUEST)
        return super(NamespaceViewSet, self).destroy(request, *args, **kwargs)


class NamespaceUserView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        namespace_id = request.query_params.get('namespace_id')
        bindings = RoleNamespaceBinding.objects.filter(namespaces=namespace_id)
        data = [{'username': b.user.username, 'role': b.role.name} for b in bindings]
        return Response(data, status=status.HTTP_200_OK)