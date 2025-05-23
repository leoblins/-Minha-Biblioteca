#!/bin/bash

echo "Aplicando migrações..."
python manage.py migrate --noinput

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "Criando superusuário, se não existir..."
echo "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='leoblins').exists():
    User.objects.create_superuser('leoblins', 'leoblins@gmail.com', 'Sardinha221405@')
" | python manage.py shell

echo "Iniciando Gunicorn..."
exec gunicorn biblioteca_pai.wsgi:application
