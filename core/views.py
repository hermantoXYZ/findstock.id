from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from app.models import Article, Category, Page, UserAnggota, Topic, Saham
from django.db.models import Count, Q
from django.utils.text import slugify
from app.forms_anggota import formUserRegisterAnggota
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import yfinance as yf
from app.utils import get_realtime_prices

# tanggal_now = timezone.now()

def custom_404(request, exception):
    return render(request, "home/404.html", status=404)

def index(request):

    # filter_published = {'status': 'published', 'created_at__lte': tanggal_now}
    all_articles = Article.objects.filter( status='published', created_at__lte=timezone.now() ).order_by('-created_at')
    headline_articles = Article.objects.filter(is_headline=True, status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    news = Article.objects.filter(category__slug='news', status='published', created_at__lte=timezone.now()).order_by('-created_at')
    popular_articles = Article.objects.filter(status='published', created_at__lte=timezone.now()).order_by('-views_count')[:7]
    category_list_variabel = Category.objects.all()
    paginator = Paginator(all_articles, 6)
    page = request.GET.get('page')
    
    realtime_saham = get_realtime_prices()
    sektor_healthcare = [
    item for item in realtime_saham 
    if item.get('sektor', '').lower() == "healthcare"
]

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)
    
    featured_article = Article.objects.filter(status='published').order_by('-created_at').first()

    context = {
        'article_list': articles,
        'featured_article': featured_article,
        'paginator': paginator,
        'headline_articles': headline_articles,
        'news': news,
        'popular_articles': popular_articles,
        'category_list': category_list_variabel,
        'market_data': sektor_healthcare,
    }
    return render(request,'home/index.html', context) 


def article_detail(request, slug, category_slug, unique_id):
    article = get_object_or_404(Article, unique_id=unique_id, slug=slug, category__slug=category_slug)
    if article.status != 'published' or article.created_at > timezone.now():
        return render(request, 'home/404.html', status=404)

    category_list_variabel = Category.objects.all()
    popular_articles = Article.objects.filter(status='published', created_at__lte=timezone.now()).order_by('-views_count')[:7]
    article.views_count += 1
    article.save()
    category_list_variabel = Category.objects.annotate(article_count=Count('articles', filter=Q(articles__status='published')))
    related_articles = Article.objects.filter( topic__in=article.topic.all(), status='published', created_at__lte=timezone.now() ).exclude(id=article.id).distinct().order_by('-created_at')[:4]
    latest_articles_variabel = Article.objects.filter(status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    topics = article.topic.all()
    
    return render(request, 'home/article_detail.html', {'article': article, 'views': article.views_count, 'category_list': category_list_variabel, 'latest_articles': latest_articles_variabel, 'popular_articles': popular_articles, 'related_articles': related_articles, 'topics': topics})

def article_list(request):
    all_articles = Article.objects.filter(status='published').order_by('-created_at')
    category_filter = request.GET.get('category')
    if category_filter:
        all_articles = all_articles.filter(category__slug=category_filter)
    
    # Filter berdasarkan pencarian
    search_query = request.GET.get('search')
    if search_query:
        all_articles = all_articles.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(author__first_name__icontains=search_query) |
            Q(author__last_name__icontains=search_query)
        )
    per_page = request.GET.get('per_page', 12)
    
    if per_page == 'all':
        articles = all_articles
        paginator = None
    else:
        try:
            per_page = int(per_page)
            if per_page not in [6, 12, 24, 48]:
                per_page = 12
        except (ValueError, TypeError):
            per_page = 12
        
        paginator = Paginator(all_articles, per_page)
        page = request.GET.get('page')
        
        try:
            articles = paginator.page(page)
        except PageNotAnInteger:
            articles = paginator.page(1)
        except EmptyPage:
            articles = paginator.page(paginator.num_pages)
    categories = Category.objects.annotate(
        article_count=Count('articles', filter=Q(articles__status='published'))
    )
    
    context = {
        'articles': articles,
        'paginator': paginator,
        'categories': categories,
        'current_category': category_filter,
        'search_query': search_query,
    }
    return render(request, 'home/article_list.html', context)

def category_articles(request, slug):
    category = get_object_or_404(Category, slug=slug)
    articles = Article.objects.filter(category=category, status='published', created_at__lte=timezone.now()).order_by('-created_at')
    makassar_raya_articles = Article.objects.filter(category__slug='makassar-raya', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:4]
    celebes_voice_articles = Article.objects.filter(category__slug='celebes-voice', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    hukum_articles = Article.objects.filter(category__slug='hukum', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    inspirasi_nusantara_articles = Article.objects.filter(category__slug='inspirasi-nusantara', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    lensa_budaya_articles = Article.objects.filter(category__slug='lensa-budaya', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    sport_hiburan_articles = Article.objects.filter(category__slug='sport-hiburan', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    teknologi_articles = Article.objects.filter(category__slug='teknologi', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    daerah_articles = Article.objects.filter(category__slug='daerah', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    politik = Article.objects.filter(category__slug='politik', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    news = Article.objects.filter(category__slug='news', status='published', created_at__lte=timezone.now()).order_by('-created_at')
    popular_articles = Article.objects.filter(category=category, status='published', created_at__lte=timezone.now()).order_by('-views_count')[:3]
    popular_article = Article.objects.filter(status='published', created_at__lte=timezone.now()).order_by('-views_count')[:7]

    context = {
        'category': category,
        'articles': articles,
        'makassar_raya_articles': makassar_raya_articles,
        'celebes_voice_articles': celebes_voice_articles,
        'hukum_articles': hukum_articles,
        'inspirasi_nusantara_articles': inspirasi_nusantara_articles,
        'lensa_budaya_articles': lensa_budaya_articles,
        'sport_hiburan_articles': sport_hiburan_articles,
        'teknologi_articles': teknologi_articles,
        'daerah_articles': daerah_articles,
        'politik': politik,
        'news': news,
        'popular_articles': popular_articles,
        'popular_article': popular_article
    }


    return render(request, 'home/category_articles.html', context)

def topic_articles(request, slug):
    topic = get_object_or_404(Topic, slug=slug)
    articles = Article.objects.filter(
        topic=topic,
        status='published'
    ).order_by('-created_at')
    popular_articles = Article.objects.filter(topic=topic, status='published', created_at__lte=timezone.now()).order_by('-views_count')[:3]
    makassar_raya_articles = Article.objects.filter(category__slug='makassar-raya', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:4]
    celebes_voice_articles = Article.objects.filter(category__slug='celebes-voice', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    hukum_articles = Article.objects.filter(category__slug='hukum', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    inspirasi_nusantara_articles = Article.objects.filter(category__slug='inspirasi-nusantara', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    lensa_budaya_articles = Article.objects.filter(category__slug='lensa-budaya', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    sport_hiburan_articles = Article.objects.filter(category__slug='sport-hiburan', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    teknologi_articles = Article.objects.filter(category__slug='teknologi', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    daerah_articles = Article.objects.filter(category__slug='daerah', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    politik = Article.objects.filter(category__slug='politik', status='published', created_at__lte=timezone.now()).order_by('-created_at')[:6]
    news = Article.objects.filter(category__slug='news', status='published', created_at__lte=timezone.now()).order_by('-created_at')

    return render(request, 'home/topic_articles.html', {
        'topic': topic,
        'articles': articles,
        'popular_articles': popular_articles,
        'makassar_raya_articles': makassar_raya_articles,
        'celebes_voice_articles': celebes_voice_articles,
        'hukum_articles': hukum_articles,
        'inspirasi_nusantara_articles': inspirasi_nusantara_articles,
        'lensa_budaya_articles': lensa_budaya_articles,
        'sport_hiburan_articles': sport_hiburan_articles,
        'teknologi_articles': teknologi_articles,
        'daerah_articles': daerah_articles,
        'politik': politik,
        'news': news,
    })

def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug)

    context = {
        'page': page,
    }
    return render(request, 'home/page_detail.html', context)

def about(request):
    context = {
        'title' : 'About',
        'heading' : 'TENTANG APLIKASI' 
    }
    return render(request,'about.html', context) 


def saham_detail(request, symbol):
    saham = get_object_or_404(Saham, symbol=symbol.upper())
    

    context = {
        'saham': saham,
    }
    return render(request, 'home/saham_detail.html', context)


def loginView(request):
    context = {
        'title': 'Login',
        'heading': 'Login',
    }
    if request.method == "POST":
        print (request.POST)
        username_in = request.POST['username']
        password_in = request.POST['password']
        user = authenticate(request, username=username_in, password=password_in)        
        if user is not None:
            login(request, user)
            messages.success(request, 'Selamat Datang!')
            return redirect('/dashboard/')
        else:
            messages.warning(request, 'Periksa Kembali Username dan Password Anda!')
            return redirect('login')
    
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('index')
        else:
            return render(request,'home/login.html', context) 

@login_required
def LogoutView(request):
    context = {
        'title': 'Login',
        'heading': 'Login Gaes',
    }
    if request.method == "POST":
        if request.POST['logout']=='ya':
            logout(request)
        return redirect('login')    

    return render(request,'logout.html', context)


def registerView(request):
    if request.method == "POST":
        form = formUserRegisterAnggota(request.POST)
        
        if form.is_valid():
            user = form.save()  

            UserAnggota.objects.create(
                id_anggota=user,
                telp="-",
                gender="Laki-laki",  
                alamat="",
            )

            messages.success(request, 'Registrasi berhasil! Silakan login.')
            return redirect('login')
    else:
        form = formUserRegisterAnggota()
    
    context = {
        'form': form,
        'title': 'Register',
        'heading': 'Register User Anggota',
    }
    return render(request, 'home/register.html', context)