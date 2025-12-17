from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from app.models import Article, Category, Page, UserAnggota, Topic, Saham, Dividend
from django.db.models import Count, Q
from django.utils.text import slugify
from app.forms_anggota import formUserRegisterAnggota
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import F, FloatField, ExpressionWrapper

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
    saham_healthcare = Saham.objects.filter(sektor="healthcare")
    saham_basic_materials = Saham.objects.filter(sektor="basic materials")
    sahan_financials = Saham.objects.filter(sektor="financials")
    saham_transportation_logistic = Saham.objects.filter(sektor="transportation logistic")
    saham_technology = Saham.objects.filter(sektor="technology")
    saham_non_cyclicals = Saham.objects.filter(sektor="non cyclicals")
    saham_industrials = Saham.objects.filter(sektor="industrials")
    saham_energy = Saham.objects.filter(sektor="energy")
    saham_cyclicals = Saham.objects.filter(sektor="cyclicals")
    saham_infrastructures = Saham.objects.filter(sektor="infrastructures")
    saham_properties = Saham.objects.filter(sektor="properties")
    top_volumes = ( Saham.objects .filter(volume__isnull=False) .order_by('-volume')[:7] )
    top_gainers = ( Saham.objects .filter(volume__isnull=False) .order_by('-change_pct')[:7] )
    top_losers = ( Saham.objects .filter(change_pct__isnull=False) .order_by('change_pct')[:7])
    top_saham = Saham.objects .filter(volume__isnull=False, market_cap__isnull=False) .order_by('-volume', '-market_cap')[:25] 
    
    paginator = Paginator(all_articles, 6)
    page = request.GET.get('page')
    
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
        'saham_healthcare': saham_healthcare,
        'saham_basic_materials': saham_basic_materials,
        'sahan_financials': sahan_financials,
        'saham_transportation_logistic': saham_transportation_logistic,
        'saham_technology': saham_technology,
        'saham_non_cyclicals': saham_non_cyclicals,
        'saham_industrials': saham_industrials,
        'saham_energy': saham_energy,
        'saham_cyclicals': saham_cyclicals,
        'saham_infrastructures': saham_infrastructures,
        'saham_properties': saham_properties,
        'top_volumes': top_volumes,
        'top_saham': top_saham,
        'top_gainers': top_gainers,
        'top_losers': top_losers
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

def kalkulator_investasi(request):
    context = {
        'title' : 'Kalkulator Investasi',
        'heading' : 'KALKULATOR INVESTASI' 
    }
    return render(request,'home/kalkulator_investasi.html', context)

def saham_detail(request, symbol):
    saham = get_object_or_404(Saham, symbol=symbol.upper())
    dividends = saham.dividends.order_by('-period')
    top_volumes = ( Saham.objects .filter(volume__isnull=False) .order_by('-volume')[:15] )

    context = {
        'saham': saham,
        'dividends': dividends,
        'top_volumes': top_volumes
    }
    return render(request, 'home/saham_detail.html', context)

def devidends_list(request):
    saham = Saham.objects.all().order_by('-volume')

    for s in saham:
            s.div_yield_percent = s.div_yield * 100 if s.div_yield else None

    context = {
        'title': 'Daftar Dividen Saham',
        'sahams': saham,
    }
    return render(request, 'home/dividends_list.html', context)

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


def saham_filter_view(request):
    saham_list = Saham.objects.all()
    
    # Filter berdasarkan search (symbol atau nama)
    search = request.GET.get('search', '')
    if search:
        saham_list = saham_list.filter(
            Q(symbol__icontains=search) |
            Q(short_name__icontains=search) |
            Q(long_name__icontains=search)
        )
    
    # Filter berdasarkan sektor
    sektor = request.GET.get('sektor', '')
    if sektor:
        saham_list = saham_list.filter(sektor=sektor)
    
    # Filter berdasarkan papan pencatatan
    papan = request.GET.get('papan', '')
    if papan:
        saham_list = saham_list.filter(papan_pencatatan=papan)
    
    # Filter harga
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    if price_min:
        saham_list = saham_list.filter(price__gte=float(price_min))
    if price_max:
        saham_list = saham_list.filter(price__lte=float(price_max))
    
    # Filter perubahan harga
    change_pct_min = request.GET.get('change_pct_min', '')
    change_pct_max = request.GET.get('change_pct_max', '')
    if change_pct_min:
        saham_list = saham_list.filter(change_pct__gte=float(change_pct_min))
    if change_pct_max:
        saham_list = saham_list.filter(change_pct__lte=float(change_pct_max))
    
    # Filter market cap
    market_cap_min = request.GET.get('market_cap_min', '')
    market_cap_max = request.GET.get('market_cap_max', '')
    if market_cap_min:
        saham_list = saham_list.filter(market_cap__gte=int(market_cap_min))
    if market_cap_max:
        saham_list = saham_list.filter(market_cap__lte=int(market_cap_max))
    
    # Filter PE Ratio
    pe_min = request.GET.get('pe_min', '')
    pe_max = request.GET.get('pe_max', '')
    if pe_min:
        saham_list = saham_list.filter(pe__gte=float(pe_min))
    if pe_max:
        saham_list = saham_list.filter(pe__lte=float(pe_max))
    
    # Filter PBV
    pbv_min = request.GET.get('pbv_min', '')
    pbv_max = request.GET.get('pbv_max', '')
    if pbv_min:
        saham_list = saham_list.filter(pbv__gte=float(pbv_min))
    if pbv_max:
        saham_list = saham_list.filter(pbv__lte=float(pbv_max))
    
    # Filter dividend yield
    div_yield_min = request.GET.get('div_yield_min', '')
    div_yield_max = request.GET.get('div_yield_max', '')

    if div_yield_min:
        saham_list = saham_list.filter(
            div_yield__gte=float(div_yield_min) / 100
        )

    if div_yield_max:
        saham_list = saham_list.filter(
            div_yield__lte=float(div_yield_max) / 100
        )

    saham_list = saham_list.annotate(
        div_yield_display=ExpressionWrapper(
            F('div_yield') * 100,
            output_field=FloatField()
        )
    )

    # Filter volume
    volume_min = request.GET.get('volume_min', '')
    volume_max = request.GET.get('volume_max', '')
    if volume_min:
        saham_list = saham_list.filter(volume__gte=int(volume_min))
    if volume_max:
        saham_list = saham_list.filter(volume__lte=int(volume_max))
    
    # Sorting
    sort_by = request.GET.get('sort', '-price')
    if sort_by:
        saham_list = saham_list.order_by(sort_by)
    
    # Ambil daftar unik untuk dropdown filter
    sektor_list = Saham.objects.values_list('sektor', flat=True).distinct().exclude(sektor__isnull=True)
    papan_list = Saham.objects.values_list('papan_pencatatan', flat=True).distinct().exclude(papan_pencatatan__isnull=True)
    
    context = {
        'saham_list': saham_list,
        'sektor_list': sektor_list,
        'papan_list': papan_list,
        # Pertahankan nilai filter untuk form
        'search': search,
        'sektor': sektor,
        'papan': papan,
        'price_min': price_min,
        'price_max': price_max,
        'change_pct_min': change_pct_min,
        'change_pct_max': change_pct_max,
        'market_cap_min': market_cap_min,
        'market_cap_max': market_cap_max,
        'pe_min': pe_min,
        'pe_max': pe_max,
        'pbv_min': pbv_min,
        'pbv_max': pbv_max,
        'div_yield_min': div_yield_min,
        'div_yield_max': div_yield_max,
        'volume_min': volume_min,
        'volume_max': volume_max,
        'sort': sort_by,
    }
    
    return render(request, 'home/saham.html', context)