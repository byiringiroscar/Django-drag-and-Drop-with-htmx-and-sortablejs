from django.http.response import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib.auth import get_user_model
from films.models import Film, UserFilms
from django.views.generic import ListView

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from films.utils import get_max_order
from django.contrib import messages

from films.forms import RegisterForm

# Create your views here.
class IndexView(TemplateView):
    template_name = 'index.html'
    
class Login(LoginView):
    template_name = 'registration/login.html'

class RegisterView(FormView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()  # save the user
        return super().form_valid(form)
    

def check_username(request):
    username  = request.POST.get('username')
    if username:
        if get_user_model().objects.filter(username=username).exists():
            return HttpResponse("<div id='username-error' class='error'>This username already exists</div>")
        else:
            return HttpResponse("<div id='username-success' class='success'>This username is available</div>")
    else:
        return HttpResponse("<div id='username-error' class='error'>Username is required</div>")
    



class FilmList(ListView):
    template_name = 'films.html'
    model = Film
    context_object_name = 'films'

    def get_queryset(self):
        return UserFilms.objects.filter(user=self.request.user)
    
@login_required
def add_film(request):
    name = request.POST.get('filmname')
    if name == '':
        return render(request, 'partials/film-list.html', {'films': request.user.films.all()})
    film = Film.objects.get_or_create(name=name)[0]

    if UserFilms.objects.filter(user=request.user, film=film).exists():
        UserFilms.objects.create(user=request.user, film=film, order=get_max_order(request.user))

    films = UserFilms.objects.filter(user=request.user)
    messages.success(request, f'Added {name} to list of films!')
    return render(request, 'partials/film-list.html', {'films': films})

@login_required
@require_http_methods(['DELETE'])
def delete_film(request, pk):
    UserFilms.objects.get(pk=pk).delete()
    films = UserFilms.objects.filter(user=request.user)
    return render(request, 'partials/film-list.html', {'films': films})



def search_film(request):
    search_text = request.POST.get('search')
    userfilms  = UserFilms.objects.filter(user=request.user)
    results = Film.objects.filter(name__icontains=search_text).exclude(
        name__in=userfilms.values_list('film__name', flat=True)
    )
    context = {
        'results': results
    }
    return render(request, 'partials/search-results.html', context)


def clear(request):
    return HttpResponse("")