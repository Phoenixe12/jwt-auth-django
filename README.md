# Django JWT Authentication API - README

Ce projet implémente une API Django avec authentification JWT à deux tokens (access token et refresh token), documentée avec Swagger.

## Sommaire
1. [Architecture du projet](#architecture-du-projet)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Fonctionnalités d'authentification](#fonctionnalités-dauthentification)
5. [Ajouter de nouvelles routes protégées](#ajouter-de-nouvelles-routes-protégées)
6. [Documentation Swagger](#documentation-swagger)
7. [Bonnes pratiques](#bonnes-pratiques)
8. [Déploiement](#déploiement)

## Architecture du projet

```
auth_project/
├── auth_project/          # Configuration du projet
│   ├── settings.py        # Paramètres du projet
│   ├── urls.py            # URLs du projet avec Swagger
│   └── wsgi.py            # Configuration WSGI
├── authentication/        # Application d'authentification
│   ├── middleware.py      # Middleware JWT pour Swagger
│   ├── serializers.py     # Sérialiseurs pour l'authentification
│   ├── urls.py            # URLs d'authentification
│   └── views.py           # Vues d'authentification
└── manage.py              # Script de gestion Django
```

## Installation

1. Clonez le dépôt
```bash
 git clone https://github.com/Phoenixe12/jwt-auth-django.git
```

2. Créez un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```
3. Installez les dépendances :
```bash
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers drf-yasg
```
4. Appliquez les migrations :
```bash
python manage.py migrate
```
5. Créez un superutilisateur :
```bash
python manage.py createsuperuser
```
6. Lancez le serveur :
```bash
python manage.py runserver
```

## Configuration

Les paramètres principaux se trouvent dans `settings.py` :

- `SIMPLE_JWT` : configuration des tokens JWT (durée de vie, algorithme, etc.)
- `REST_FRAMEWORK` : configuration de l'authentification par défaut
- `SWAGGER_SETTINGS` : configuration de la documentation Swagger

## Fonctionnalités d'authentification

| Endpoint | Méthode | Description | Authentification requise |
|----------|---------|-------------|--------------------------|
| `/api/register/` | POST | Création d'un compte | Non |
| `/api/login/` | POST | Connexion et obtention des tokens | Non |
| `/api/refresh/` | POST | Rafraîchissement de l'access token | Non |
| `/api/logout/` | POST | Déconnexion (blacklist du refresh token) | Oui |
| `/api/protected/` | GET | Exemple de ressource protégée | Oui |

## Ajouter de nouvelles routes protégées

Pour ajouter de nouvelles routes protégées à votre API, suivez ces étapes :

### 1. Créer une nouvelle application (optionnel)

Si votre nouvelle fonctionnalité est distincte de l'authentification, créez une nouvelle application :

```bash
python manage.py startapp my_new_app
```

Ajoutez l'application à `INSTALLED_APPS` dans `settings.py`.

### 2. Créer les modèles (si nécessaire)

Définissez vos modèles dans `my_new_app/models.py` :

```python
from django.db import models
from django.contrib.auth.models import User

class MyModel(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
```

Créez et appliquez les migrations :

```bash
python manage.py makemigrations my_new_app
python manage.py migrate
```

### 3. Créer les sérialiseurs

Créez un fichier `my_new_app/serializers.py` :

```python
from rest_framework import serializers
from .models import MyModel

class MyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = ('id', 'name', 'description', 'created_at')
        read_only_fields = ('created_at',)
    
    def create(self, validated_data):
        # Ajoutez automatiquement l'utilisateur courant comme propriétaire
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
```

### 4. Créer les vues

Créez ou modifiez `my_new_app/views.py` :

```python
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import MyModel
from .serializers import MyModelSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class MyModelViewSet(viewsets.ModelViewSet):
    serializer_class = MyModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Filtrer par utilisateur courant
        return MyModel.objects.filter(owner=self.request.user)
    
    @swagger_auto_schema(
        tags=['My Resources'],
        operation_description="Liste toutes vos ressources",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Format: Bearer {token}",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: MyModelSerializer(many=True),
            401: "Non authentifié"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['My Resources'],
        operation_description="Crée une nouvelle ressource",
        request_body=MyModelSerializer,
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Format: Bearer {token}",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: MyModelSerializer,
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    # Documentez de la même façon les autres méthodes (retrieve, update, delete)
```

Pour des vues plus simples, vous pouvez aussi utiliser `APIView` :

```python
from rest_framework.views import APIView

class CustomProtectedView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Custom'],
        operation_description="Exemple de ressource personnalisée protégée",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Format: Bearer {token}",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def get(self, request):
        return Response({
            'message': f'Bonjour {request.user.username}',
            'custom_data': 'Données personnalisées'
        })
```

### 5. Configurer les URLs

Créez `my_new_app/urls.py` :

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyModelViewSet, CustomProtectedView

router = DefaultRouter()
router.register(r'my-resources', MyModelViewSet, basename='my-resources')

urlpatterns = [
    path('', include(router.urls)),
    path('custom/', CustomProtectedView.as_view(), name='custom'),
]
```

### 6. Intégrer les URLs au projet principal

Modifiez `auth_project/urls.py` pour inclure vos nouvelles URLs :

```python
urlpatterns = [
    # ...
    path('api/', include('authentication.urls')),
    path('api/', include('my_new_app.urls')),  # Ajoutez cette ligne
    # ...
]
```

## Documentation Swagger

Toutes vos routes seront automatiquement documentées dans Swagger si vous les annotez correctement avec `@swagger_auto_schema`.

Accédez à la documentation à l'URL : `http://localhost:8000/swagger/`

### Authentification dans Swagger

1. Obtenez un token via l'endpoint `/api/login/`
2. Cliquez sur le bouton "Authorize" en haut de la page Swagger
3. Entrez votre token au format `Bearer votre_access_token`
4. Testez vos endpoints protégés

## Bonnes pratiques

### Sécurité

- Utilisez toujours `IsAuthenticated` pour les ressources protégées
- Filtrez les objets par l'utilisateur courant (`owner=request.user`)
- Stockez la clé secrète JWT dans les variables d'environnement
- Activez la blacklist pour les refresh tokens

### Performance

- Utilisez des `select_related()` et `prefetch_related()` pour optimiser les requêtes
- Implémentez la pagination pour les listes d'objets

### Gestion des permissions

Pour des permissions plus avancées, créez des classes personnalisées :

```python
from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
```

Utilisez-les dans vos vues :

```python
permission_classes = [permissions.IsAuthenticated, IsOwner]
```

## Déploiement

Pour un déploiement en production, assurez-vous de :

1. Changer `DEBUG = False` dans `settings.py`
2. Configurer `ALLOWED_HOSTS` correctement
3. Utiliser une base de données solide (PostgreSQL recommandé)
4. Configurer `CORS_ALLOWED_ORIGINS` au lieu de `CORS_ALLOW_ALL_ORIGINS`
5. Stocker les clés secrètes dans des variables d'environnement
6. Activer HTTPS avec des certificats valides
7. Configurer des limites de taux (rate limiting)

---

Ce README fournit une documentation complète pour étendre votre API Django avec authentification JWT. Vous pouvez l'adapter selon les besoins spécifiques de votre projet.
