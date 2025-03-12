from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import json
from .reader import fetch_html, extract_content, categorize_with_gemini
from .models import Bookmark, Category, Tag, Collection
from django.db import models
from collections import Counter
from django.contrib import messages

# Create your views here.

# Kullanıcı Kimlik Doğrulama Görünümleri
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('tagwiseapp:index')
        else:
            return render(request, 'auth/login.html', {'error': 'Geçersiz kullanıcı adı veya şifre'})
    
    return render(request, 'auth/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            return render(request, 'auth/register.html', {'error': 'Şifreler eşleşmiyor'})
        
        if User.objects.filter(username=username).exists():
            return render(request, 'auth/register.html', {'error': 'Bu kullanıcı adı zaten kullanılıyor'})
        
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('tagwiseapp:index')
    
    return render(request, 'auth/register.html')

def logout_view(request):
    logout(request)
    return redirect('tagwiseapp:login')

# Ana Sayfa
@login_required(login_url='tagwiseapp:login')
def index(request):
    # Kullanıcıya ait bookmark'ları getir
    bookmarks = Bookmark.objects.filter(user=request.user).order_by('-created_at')
    
    # Ana kategorileri getir
    main_categories = Category.objects.filter(parent=None)
    
    # NOT: Varsayılan kategorileri otomatik oluşturmayı kaldırdık
    # Kategoriler artık sadece bookmark eklendiğinde, gerçekten kullanıldıklarında oluşturulacak
    
    return render(request, 'home/main.html', {
        'bookmarks': bookmarks,
        'main_categories': main_categories
    })

def categories(request):
    print("categories")
    return render(request, 'Categories/categories.html')

def tags(request):
    # Get all tags with bookmark count
    tags = Tag.objects.annotate(bookmark_count=models.Count('bookmark'))
    
    # Get recent tags (those with bookmarks added in the last 7 days)
    from django.utils import timezone
    from datetime import timedelta
    recent_date = timezone.now() - timedelta(days=7)
    
    # Get tags that have bookmarks added in the last 7 days
    recent_bookmarks = Bookmark.objects.filter(
        user=request.user, 
        created_at__gte=recent_date
    )
    recent_tag_ids = []
    for bookmark in recent_bookmarks:
        recent_tag_ids.extend(bookmark.tags.values_list('id', flat=True))
    
    recent_tags = Tag.objects.filter(id__in=recent_tag_ids).annotate(
        bookmark_count=models.Count('bookmark')
    )
    
    # Group tags by first letter for organization
    for tag in tags:
        if tag.name:
            tag.group = tag.name[0].upper()
        else:
            tag.group = '#'
    
    return render(request, 'tags/tags.html', {
        'tags': tags,
        'recent_tags': recent_tags
    })

@login_required(login_url='tagwiseapp:login')
def collections(request):
    # Get user's collections
    user_collections = Collection.objects.filter(user=request.user).order_by('-updated_at')
    
    # Get user's bookmarks for the collection creation modal
    user_bookmarks = Bookmark.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'collections/collections.html', {
        'collections': user_collections,
        'bookmarks': user_bookmarks
    })

def subcategories(request):
    print("subcategories")
    return render(request, 'Categories/Subcategories/subcategories.html')

def topics(request):
    category_name = request.GET.get('category')
    subcategory_name = request.GET.get('subcategory')
    
    if subcategory_name:
        subcategory = Category.objects.filter(name=subcategory_name).first()
        if subcategory:
            bookmarks = Bookmark.objects.filter(user=request.user, subcategories=subcategory).order_by('-created_at')
            return render(request, 'topics/topics.html', {'subcategory': subcategory, 'bookmarks': bookmarks})
    
    return redirect('tagwiseapp:categories')

def tagged_bookmarks(request):
    print("tagged_bookmarks")
    return render(request, 'Tagged-Bookmarks/tagged-bookmarks.html')

@csrf_exempt
@login_required(login_url='tagwiseapp:login')
def analyze_url(request):
    if request.method == 'POST':
        try:
            print("POST isteği alındı")
            data = json.loads(request.body)
            url = data.get('url')
            
            print(f"Alınan URL: {url}")
            
            if not url:
                return JsonResponse({'error': 'URL gereklidir'}, status=400)
            
            # URL formatını kontrol et
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                print(f"URL düzeltildi: {url}")
            
            # Fetch HTML content
            print("HTML içeriği alınıyor...")
            html = fetch_html(url)
            if not html:
                return JsonResponse({'error': 'HTML içeriği alınamadı. URL doğru mu?'}, status=400)
            
            print("HTML içeriği alındı, içerik çıkarılıyor...")
            # Extract main content
            content = extract_content(html)
            if not content:
                return JsonResponse({'error': 'İçerik çıkarılamadı'}, status=400)
            
            print("İçerik çıkarıldı, kategorize ediliyor...")
            # Categorize content
            category_json = categorize_with_gemini(content, url)
            
            print(f"Kategori JSON: {category_json}")
            
            # Parse the JSON string to a Python dictionary
            try:
                # Gemini'nin döndürdüğü JSON formatını işle
                # Bazen birden fazla JSON objesi dönebilir
                category_data = []
                
                # JSON formatını kontrol et
                if category_json.startswith('{') and category_json.endswith('}'):
                    # Tek bir JSON objesi
                    parsed_json = json.loads(category_json)
                    if 'categories' in parsed_json:
                        category_data = parsed_json.get('categories', [])
                else:
                    # Birden fazla JSON objesi olabilir
                    import re
                    json_matches = re.findall(r'\{[\s\S]*?"categories"[\s\S]*?\}', category_json)
                    
                    if json_matches:
                        for json_str in json_matches:
                            try:
                                parsed_json = json.loads(json_str)
                                if 'categories' in parsed_json:
                                    category_data.extend(parsed_json.get('categories', []))
                            except json.JSONDecodeError:
                                continue
                
                print(f"İşlenen kategori verisi: {category_data}")
                
                if not category_data:
                    print("Kategori verisi bulunamadı, ham yanıtı gönderiyoruz")
                    # Kategori verisi bulunamadıysa, ham yanıtı gönder
                    category_data = {"raw_response": category_json}
            except json.JSONDecodeError as e:
                print(f"JSON ayrıştırma hatası: {e}")
                # JSON ayrıştırma hatası durumunda ham yanıtı gönder
                category_data = {"raw_response": category_json}
            
            # Extract title from HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.title.string if soup.title else ""
            
            # Extract description from meta tags
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '')
            
            # Get all available main categories
            main_categories = list(Category.objects.filter(parent=None).values_list('name', flat=True))
            
            # NOT: Varsayılan kategorileri otomatik oluşturmayı kaldırdık
            # Kategoriler artık sadece bookmark eklendiğinde, gerçekten kullanıldıklarında oluşturulacak
            
            # Prepare response
            response_data = {
                'url': url,
                'title': title,
                'description': description,
                'categories': category_data,
                'available_main_categories': main_categories,
                'success': True,
                'raw_response': category_json  # Ham yanıtı da ekle
            }
            
            print("İşlem başarılı, yanıt gönderiliyor")
            return JsonResponse(response_data)
            
        except Exception as e:
            import traceback
            print("Hata oluştu:")
            print(traceback.format_exc())  # Detaylı hata mesajını konsola yazdır
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Sadece POST metodu kabul edilir'}, status=405)

@csrf_protect
@login_required(login_url='tagwiseapp:login')
def save_bookmark(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract data
            url = data.get('url')
            title = data.get('title')
            description = data.get('description')
            main_categories = data.get('main_categories', [])
            subcategories = data.get('subcategories', [])
            tags = data.get('tags', [])
            
            # Backward compatibility for old format
            if 'main_category' in data and not main_categories:
                main_categories = [data.get('main_category')]
            
            # Validate required fields
            if not url or not title or not main_categories:
                return JsonResponse({'error': 'URL, title, and at least one main category are required'}, status=400)
            
            # Create the bookmark
            bookmark = Bookmark.objects.create(
                url=url,
                title=title,
                description=description,
                user=request.user
            )
            
            # Kullanılan ana kategorileri ve alt kategorileri takip et
            used_main_categories = []
            used_subcategories = []
            
            # Add main categories - only those that are actually used
            for main_category_name in main_categories:
                # Try to find existing category first
                main_category = Category.objects.filter(name=main_category_name).first()
                if not main_category:
                    # Create new if not exists
                    main_category = Category.objects.create(name=main_category_name)
                bookmark.main_categories.add(main_category)
                used_main_categories.append(main_category)
            
            # Alt kategorileri ve ana kategorileri eşleştirmek için kategori-alt kategori ilişkilerini al
            category_subcategory_map = {}
            
            # JavaScript'ten gelen kategori-alt kategori ilişkilerini analiz et
            if 'category_subcategory_map' in data:
                category_subcategory_map = data.get('category_subcategory_map', {})
            else:
                # Eski format için geriye dönük uyumluluk - her alt kategoriyi tüm ana kategorilere ekle
                for subcategory_name in subcategories:
                    for main_category in used_main_categories:
                        if main_category.name not in category_subcategory_map:
                            category_subcategory_map[main_category.name] = []
                        category_subcategory_map[main_category.name].append(subcategory_name)
            
            # Add subcategories - only once for each subcategory and only if they have a parent
            for subcategory_name in subcategories:
                # Her alt kategori için doğru ana kategoriyi bul
                parent_found = False
                
                # Kategori-alt kategori haritasını kullan
                for main_category in used_main_categories:
                    if main_category.name in category_subcategory_map and subcategory_name in category_subcategory_map[main_category.name]:
                        # Try to find existing subcategory first
                        subcategory = Category.objects.filter(name=subcategory_name).first()
                        if not subcategory:
                            # Create new if not exists
                            subcategory = Category.objects.create(name=subcategory_name, parent=main_category)
                        elif not subcategory.parent:
                            # Update parent if not set
                            subcategory.parent = main_category
                            subcategory.save()
                        
                        # Add to bookmark
                        bookmark.subcategories.add(subcategory)
                        used_subcategories.append(subcategory_name)
                        parent_found = True
                        break
                
                # Eğer haritada bulunamazsa, ilk ana kategoriyi kullan (geriye dönük uyumluluk)
                if not parent_found and used_main_categories:
                    main_category = used_main_categories[0]
                    # Try to find existing subcategory first
                    subcategory = Category.objects.filter(name=subcategory_name).first()
                    if not subcategory:
                        # Create new if not exists
                        subcategory = Category.objects.create(name=subcategory_name, parent=main_category)
                    elif not subcategory.parent:
                        # Update parent if not set
                        subcategory.parent = main_category
                        subcategory.save()
                    
                    # Add to bookmark
                    bookmark.subcategories.add(subcategory)
                    used_subcategories.append(subcategory_name)
            
            # Add tags - only those that are actually used
            for tag_name in tags:
                # Try to find existing tag first
                tag = Tag.objects.filter(name=tag_name).first()
                if not tag:
                    # Create new if not exists
                    tag = Tag.objects.create(name=tag_name)
                bookmark.tags.add(tag)
            
            return JsonResponse({'success': True, 'bookmark_id': bookmark.id})
            
        except Exception as e:
            import traceback
            print("Error saving bookmark:", traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

@csrf_exempt
def test_url(request):
    """Basit bir test fonksiyonu"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            url = data.get('url', 'Belirtilmedi')
            return JsonResponse({
                'success': True,
                'message': 'Test başarılı',
                'received_url': url
            })
        except Exception as e:
            return JsonResponse({'error': str(e)})
    return JsonResponse({'message': 'GET isteği alındı'})

# Kategori ve Etiket Görünümleri
@login_required(login_url='tagwiseapp:login')
def categories(request):
    category_name = request.GET.get('category')
    if category_name:
        category = Category.objects.filter(name=category_name).first()
        if category:
            bookmarks = Bookmark.objects.filter(user=request.user, main_categories=category).order_by('-created_at')
            return render(request, 'categories/categories.html', {'category': category, 'bookmarks': bookmarks})
    
    # Get all main categories (those without a parent)
    categories = Category.objects.filter(parent=None)
    
    # Get recent categories (those with bookmarks added in the last 7 days)
    from django.utils import timezone
    from datetime import timedelta
    recent_date = timezone.now() - timedelta(days=7)
    
    # Get categories that have bookmarks added in the last 7 days
    recent_bookmarks = Bookmark.objects.filter(
        user=request.user, 
        created_at__gte=recent_date
    )
    # ManyToManyField için values_list kullanırken _id eki kullanılmaz
    recent_category_ids = []
    for bookmark in recent_bookmarks:
        recent_category_ids.extend(bookmark.main_categories.values_list('id', flat=True))
    recent_category_ids = list(set(recent_category_ids))  # Duplicate'leri kaldır
    recent_categories = Category.objects.filter(id__in=recent_category_ids)
    
    return render(request, 'categories/categories.html', {
        'categories': categories,
        'recent_categories': recent_categories
    })

@login_required(login_url='tagwiseapp:login')
def subcategories(request):
    category_name = request.GET.get('category')
    if category_name:
        category = Category.objects.filter(name=category_name).first()
        if category:
            subcategories = Category.objects.filter(parent=category)
            return render(request, 'categories/subcategories.html', {'category': category, 'subcategories': subcategories})
    
    return redirect('tagwiseapp:categories')

@login_required(login_url='tagwiseapp:login')
def tagged_bookmarks(request):
    tag_name = request.GET.get('tag')
    if tag_name:
        tag = Tag.objects.filter(name=tag_name).first()
        if tag:
            bookmarks = Bookmark.objects.filter(user=request.user, tags=tag).order_by('-created_at')
            return render(request, 'bookmarks/tagged_bookmarks.html', {'tag': tag, 'bookmarks': bookmarks})
    
    return redirect('tagwiseapp:tags')

@login_required(login_url='tagwiseapp:login')
def collections(request):
    return render(request, 'collections/collections.html')

# Admin Görünümleri
@login_required(login_url='tagwiseapp:login')
def admin_panel(request):
    # Kullanıcı admin mi kontrol et
    if not request.user.is_superuser:
        return redirect('tagwiseapp:index')
    
    # Orphan tag ve kategorileri temizle
    if request.method == 'POST' and 'clean_orphans' in request.POST:
        cleaned_data = clean_orphan_data(request.user)
        messages.success(request, f"Temizleme tamamlandı: {cleaned_data['tags']} tag, {cleaned_data['main_categories']} ana kategori, {cleaned_data['subcategories']} alt kategori silindi.")
        return redirect('tagwiseapp:admin_panel')
    
    # Admin paneli için gerekli verileri hazırla
    total_bookmarks = Bookmark.objects.filter(user=request.user).count()
    total_tags = Tag.objects.count()
    total_categories = Category.objects.count()
    
    # Orphan tag ve kategorileri say
    orphan_tags = Tag.objects.annotate(bookmark_count=models.Count('bookmark')).filter(bookmark_count=0).count()
    orphan_main_categories = Category.objects.filter(parent=None).annotate(
        main_bookmark_count=models.Count('main_bookmarks'),
        sub_bookmark_count=models.Count('sub_bookmarks'),
        children_count=models.Count('children')
    ).filter(main_bookmark_count=0, sub_bookmark_count=0, children_count=0).count()
    
    orphan_subcategories = Category.objects.exclude(parent=None).annotate(
        main_bookmark_count=models.Count('main_bookmarks'),
        sub_bookmark_count=models.Count('sub_bookmarks')
    ).filter(main_bookmark_count=0, sub_bookmark_count=0).count()
    
    context = {
        'total_bookmarks': total_bookmarks,
        'total_tags': total_tags,
        'total_categories': total_categories,
        'orphan_tags': orphan_tags,
        'orphan_categories': orphan_main_categories + orphan_subcategories
    }
    
    return render(request, 'admin/admin_panel.html', context)

def clean_orphan_data(user):
    """Kullanılmayan (orphan) tag ve kategorileri temizler."""
    # Silinen öğeleri say
    deleted_counts = {
        'tags': 0,
        'main_categories': 0,
        'subcategories': 0
    }
    
    # Orphan tag'leri temizle
    orphan_tags = Tag.objects.annotate(bookmark_count=models.Count('bookmark')).filter(bookmark_count=0)
    deleted_counts['tags'] = orphan_tags.count()
    for tag in orphan_tags:
        print(f"Orphan tag siliniyor: {tag.name}")
    orphan_tags.delete()
    
    # Orphan alt kategorileri temizle (önce alt kategorileri temizle)
    orphan_subcategories = Category.objects.exclude(parent=None).annotate(
        main_bookmark_count=models.Count('main_bookmarks'),
        sub_bookmark_count=models.Count('sub_bookmarks')
    ).filter(main_bookmark_count=0, sub_bookmark_count=0)
    
    deleted_counts['subcategories'] = orphan_subcategories.count()
    for subcategory in orphan_subcategories:
        print(f"Orphan alt kategori siliniyor: {subcategory.name}")
    orphan_subcategories.delete()
    
    # Orphan ana kategorileri temizle
    orphan_main_categories = Category.objects.filter(parent=None).annotate(
        main_bookmark_count=models.Count('main_bookmarks'),
        sub_bookmark_count=models.Count('sub_bookmarks'),
        children_count=models.Count('children')
    ).filter(main_bookmark_count=0, sub_bookmark_count=0, children_count=0)
    
    deleted_counts['main_categories'] = orphan_main_categories.count()
    for category in orphan_main_categories:
        print(f"Orphan ana kategori siliniyor: {category.name}")
    orphan_main_categories.delete()
    
    return deleted_counts

@login_required
def delete_bookmark(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            bookmark_id = data.get('id')
            
            if not bookmark_id:
                return JsonResponse({'success': False, 'error': 'Bookmark ID is required'})
            
            # Bookmark'u bul ve kullanıcıya ait olduğunu kontrol et
            bookmark = Bookmark.objects.filter(id=bookmark_id, user=request.user).first()
            
            if not bookmark:
                return JsonResponse({'success': False, 'error': 'Bookmark not found or not authorized'})
            
            # Silinmeden önce bookmark'un tag ve kategorilerini kaydet
            tags_to_check = list(bookmark.tags.all())
            main_categories_to_check = list(bookmark.main_categories.all())
            subcategories_to_check = list(bookmark.subcategories.all())
            
            # Bookmark'u sil
            bookmark.delete()
            
            # Orphan verileri temizle
            clean_orphan_data(request.user)
            
            return JsonResponse({'success': True})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            import traceback
            print("Error deleting bookmark:", traceback.format_exc())
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required(login_url='tagwiseapp:login')
def api_related_tags(request):
    tag_name = request.GET.get('tag')
    if not tag_name:
        return JsonResponse({'success': False, 'error': 'Tag name is required'})
    
    try:
        # Get the tag
        tag = Tag.objects.get(name=tag_name)
        
        # Get bookmarks with this tag
        bookmarks = Bookmark.objects.filter(tags=tag, user=request.user)
        
        # Get all tags from these bookmarks except the current tag
        related_tag_ids = []
        for bookmark in bookmarks:
            related_tag_ids.extend(bookmark.tags.exclude(id=tag.id).values_list('id', flat=True))
        
        # Get unique tags and sort by frequency
        tag_counter = Counter(related_tag_ids)
        most_common_tag_ids = [tag_id for tag_id, _ in tag_counter.most_common(10)]
        
        related_tags = Tag.objects.filter(id__in=most_common_tag_ids).values_list('name', flat=True)
        
        return JsonResponse({
            'success': True,
            'related_tags': list(related_tags)
        })
    except Tag.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tag not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required(login_url='tagwiseapp:login')
def api_tagged_bookmarks(request):
    tag_name = request.GET.get('tag')
    if not tag_name:
        return JsonResponse({'success': False, 'error': 'Tag name is required'})
    
    try:
        # Get the tag
        tag = Tag.objects.get(name=tag_name)
        
        # Get bookmarks with this tag
        bookmarks = Bookmark.objects.filter(tags=tag, user=request.user).order_by('-created_at')
        
        # Prepare bookmark data
        bookmark_data = []
        for bookmark in bookmarks:
            bookmark_data.append({
                'id': bookmark.id,
                'url': bookmark.url,
                'title': bookmark.title,
                'description': bookmark.description,
                'thumbnail': '/static/images/placeholder.jpg',  # Replace with actual thumbnail if available
                'created_at': bookmark.created_at.isoformat(),
                'tags': list(bookmark.tags.values_list('name', flat=True))
            })
        
        return JsonResponse({
            'success': True,
            'bookmarks': bookmark_data
        })
    except Tag.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tag not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required(login_url='tagwiseapp:login')
def test_page(request):
    """A simple test page to verify that the header and navigation are working"""
    return render(request, 'test.html')

@csrf_protect
@login_required(login_url='tagwiseapp:login')
def update_bookmark(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract data
            bookmark_id = data.get('id')
            title = data.get('title')
            description = data.get('description')
            main_categories = data.get('main_categories', [])
            subcategories = data.get('subcategories', [])
            tags = data.get('tags', [])
            
            # Validate required fields
            if not bookmark_id or not title or not main_categories:
                return JsonResponse({'error': 'Bookmark ID, title, and at least one category are required'}, status=400)
            
            # Get the bookmark
            try:
                bookmark = Bookmark.objects.get(id=bookmark_id, user=request.user)
            except Bookmark.DoesNotExist:
                return JsonResponse({'error': 'Bookmark not found'}, status=404)
            
            # Update basic fields
            bookmark.title = title
            bookmark.description = description
            bookmark.save()
            
            # Kullanılan ana kategorileri ve alt kategorileri takip et
            used_main_categories = []
            used_subcategories = []
            
            # Update main categories
            bookmark.main_categories.clear()
            for main_category_name in main_categories:
                # Try to find existing category first
                main_category = Category.objects.filter(name=main_category_name).first()
                if not main_category:
                    # Create new if not exists
                    main_category = Category.objects.create(name=main_category_name)
                bookmark.main_categories.add(main_category)
                used_main_categories.append(main_category)
            
            # Alt kategorileri ve ana kategorileri eşleştirmek için kategori-alt kategori ilişkilerini al
            category_subcategory_map = {}
            
            # JavaScript'ten gelen kategori-alt kategori ilişkilerini analiz et
            if 'category_subcategory_map' in data:
                category_subcategory_map = data.get('category_subcategory_map', {})
            else:
                # Eski format için geriye dönük uyumluluk - her alt kategoriyi tüm ana kategorilere ekle
                for subcategory_name in subcategories:
                    for main_category in used_main_categories:
                        if main_category.name not in category_subcategory_map:
                            category_subcategory_map[main_category.name] = []
                        category_subcategory_map[main_category.name].append(subcategory_name)
            
            # Update subcategories
            bookmark.subcategories.clear()
            for subcategory_name in subcategories:
                # Her alt kategori için doğru ana kategoriyi bul
                parent_found = False
                
                # Kategori-alt kategori haritasını kullan
                for main_category in used_main_categories:
                    if main_category.name in category_subcategory_map and subcategory_name in category_subcategory_map[main_category.name]:
                        # Try to find existing subcategory first
                        subcategory = Category.objects.filter(name=subcategory_name).first()
                        if not subcategory:
                            # Create new if not exists
                            subcategory = Category.objects.create(name=subcategory_name, parent=main_category)
                        elif not subcategory.parent:
                            # Update parent if not set
                            subcategory.parent = main_category
                            subcategory.save()
                        
                        # Add to bookmark
                        bookmark.subcategories.add(subcategory)
                        used_subcategories.append(subcategory_name)
                        parent_found = True
                        break
                
                # Eğer haritada bulunamazsa, ilk ana kategoriyi kullan (geriye dönük uyumluluk)
                if not parent_found and used_main_categories:
                    main_category = used_main_categories[0]
                    # Try to find existing subcategory first
                    subcategory = Category.objects.filter(name=subcategory_name).first()
                    if not subcategory:
                        # Create new if not exists
                        subcategory = Category.objects.create(name=subcategory_name, parent=main_category)
                    elif not subcategory.parent:
                        # Update parent if not set
                        subcategory.parent = main_category
                        subcategory.save()
                    
                    # Add to bookmark
                    bookmark.subcategories.add(subcategory)
                    used_subcategories.append(subcategory_name)
            
            # Update tags
            bookmark.tags.clear()
            for tag_name in tags:
                # Try to find existing tag first
                tag = Tag.objects.filter(name=tag_name).first()
                if not tag:
                    # Create new if not exists
                    tag = Tag.objects.create(name=tag_name)
                bookmark.tags.add(tag)
            
            return JsonResponse({'success': True, 'bookmark_id': bookmark.id})
            
        except Exception as e:
            import traceback
            print("Error updating bookmark:", traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

@csrf_protect
@login_required(login_url='tagwiseapp:login')
def create_collection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract data
            name = data.get('name')
            description = data.get('description', '')
            icon = data.get('icon', 'collections_bookmark')
            bookmark_ids = data.get('bookmarks', [])
            
            # Validate required fields
            if not name:
                return JsonResponse({'error': 'Collection name is required'}, status=400)
            
            # Create the collection
            collection = Collection.objects.create(
                name=name,
                description=description,
                icon=icon,
                user=request.user
            )
            
            # Add bookmarks to the collection
            if bookmark_ids:
                bookmarks = Bookmark.objects.filter(id__in=bookmark_ids, user=request.user)
                collection.bookmarks.add(*bookmarks)
            
            # Return success response with collection data
            return JsonResponse({
                'success': True,
                'collection': {
                    'id': collection.id,
                    'name': collection.name,
                    'description': collection.description,
                    'icon': collection.icon,
                    'bookmark_count': collection.bookmarks.count(),
                    'updated_at': collection.updated_at.isoformat()
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

@login_required(login_url='tagwiseapp:login')
def collection_detail(request, collection_id):
    try:
        # Get the collection
        collection = Collection.objects.get(id=collection_id, user=request.user)
        
        # Get bookmarks in this collection
        bookmarks = collection.bookmarks.all().order_by('-created_at')
        
        return render(request, 'collections/collection_detail.html', {
            'collection': collection,
            'bookmarks': bookmarks
        })
    except Collection.DoesNotExist:
        return redirect('tagwiseapp:collections')