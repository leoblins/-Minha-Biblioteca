from django.shortcuts import render, redirect, get_object_or_404
from .models import Livro
from .forms import LivroForm
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import urllib.request
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import os


@login_required
def home(request):
    termo = request.GET.get('q', '')
    autor_filtro = request.GET.get('autor', '')
    genero_filtro = request.GET.get('genero', '')

    locais = {}
    for local in ['Físico', 'Kindle', 'Play Livros', 'Lista de Desejos']:
        livros = Livro.objects.filter(local=local, usuario=request.user)

        if termo:
            livros = livros.filter(
                Q(nome__icontains=termo) |
                Q(autor__icontains=termo)
            )

        if autor_filtro:
            livros = livros.filter(autor=autor_filtro)

        if genero_filtro:
            livros = livros.filter(genero=genero_filtro)

        locais[local] = livros

    autores = Livro.objects.filter(usuario=request.user).values_list('autor', flat=True).distinct().order_by('autor')
    generos = Livro.objects.filter(usuario=request.user).values_list('genero', flat=True).distinct().order_by('genero')

    context = {
        'locais': locais,
        'termo': termo,
        'autor_filtro': autor_filtro,
        'genero_filtro': genero_filtro,
        'autores': autores,
        'generos': generos,
    }
    return render(request, 'livros/home.html', context)


@login_required
def adicionar_livro(request):
    if request.method == 'POST':
        form = LivroForm(request.POST, request.FILES)
        if form.is_valid():
            livro = form.save(commit=False)
            livro.usuario = request.user

            # Se o usuário não fez upload mas colou um link
            url_capa = form.cleaned_data.get('url_capa')
            if url_capa and not request.FILES.get('capa'):
                livro.capa.save('capa_baixada.jpg', baixar_imagem(url_capa))

            livro.save()
            messages.success(request, 'Livro adicionado com sucesso!')
            return redirect('home')
    else:
        form = LivroForm()
    return render(request, 'livros/adicionar_livro.html', {'form': form})




@login_required
def editar_livro(request, pk):
    livro = get_object_or_404(Livro, pk=pk, usuario=request.user)
    form = LivroForm(request.POST or None, request.FILES or None, instance=livro)

    if request.method == 'POST':
        if form.is_valid():
            livro = form.save(commit=False)
            nova_url = form.cleaned_data.get('url_capa')

            if nova_url:
                try:
                    if livro.capa:
                        livro.capa.delete(save=False)

                    img_temp = NamedTemporaryFile()  # ← aqui sem o 'delete=True'
                    with urllib.request.urlopen(nova_url) as u:
                        img_temp.write(u.read())
                    img_temp.flush()

                    livro.capa.save(os.path.basename(nova_url), File(img_temp), save=False)
                except Exception as e:
                    messages.error(request, f'Erro ao baixar imagem da URL: {e}')

            livro.usuario = request.user
            livro.save()
            messages.success(request, 'Livro editado com sucesso!')
            return redirect('home')

    return render(request, 'livros/editar_livro.html', {'form': form})


 





@login_required
def excluir_livro(request, id):
    livro = get_object_or_404(Livro, id=id, usuario=request.user)
    if request.method == 'POST':
        livro.delete()
        messages.success(request, 'Livro excluído com sucesso!')
        return redirect('home')
    return render(request, 'livros/excluir_livro.html', {'livro': livro})



@login_required
def detalhes_livro(request, livro_id):
    livro = get_object_or_404(Livro, id=livro_id, usuario=request.user)
    return render(request, 'livros/detalhes_livro.html', {'livro': livro})


def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'livros/registro.html', {'form': form})

def baixar_imagem(url):
    img_temp = NamedTemporaryFile()  # ✅ Corrigido
    with urllib.request.urlopen(url) as u:
        img_temp.write(u.read())
    img_temp.flush()
    return File(img_temp)
