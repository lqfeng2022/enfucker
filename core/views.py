from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .useragent import save_user_agent_info
from .models import Profile
from .serializers import ProfileSerializer


# 1)'profile/'
class ProfileViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]  # admin can do anything
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    # 2)'profile/me/'
    # authenticated users can view/update their profiles
    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        # don't use get_or_create(), violate SRP, signal will handle create()
        profile = Profile.objects.get(user_id=request.user.id)
        if request.method == 'GET':
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = ProfileSerializer(
                profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


# 3)'login/'
# Wrap '/jwt/create' and store the token in httpOnly cookies
class CookieLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            # Call it right after successful authentication
            save_user_agent_info(request, user)

            refresh = RefreshToken.for_user(user)
            res = Response({'message': 'Login successful'},
                           status=status.HTTP_200_OK)
            res.set_cookie(
                key='access_token',
                value=str(refresh.access_token),
                httponly=True,
                samesite='None',  # or 'None' for cross-site
                secure=True,    # change to True in production
                domain='.clipwords.me',  # add domain
                max_age=60 * 60 * 24 * 5  # 5 days
            )

            return res

        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


# 4)'logout/'
class CookieLogoutView(APIView):
    def post(self, request):
        res = Response(
            {'message': 'Logged out'}, status=status.HTTP_200_OK
        )
        res.delete_cookie(
            key='access_token',
            path='/',
            samesite='None',
            domain='.clipwords.me',  # add domain
        )

        return res
