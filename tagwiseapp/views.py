from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import json
import os
from .reader.html_fetcher import fetch_html
from .reader.content_extractor import extract_content
from .reader.content_analyzer import categorize_content
from .reader.screenshot import capture_screenshot
from .reader.content_analyzer import analyze_screenshot
from .models import Bookmark, Category, Tag, Collection, Profile
from django.db import models
from collections import Counter
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import base64
import time
import traceback
from django.db.models import Q, Count
from django.utils import timezone
from .reader.youtube_analyzer import is_youtube_url, analyze_youtube_video, extract_youtube_video_id, fetch_youtube_thumbnail
from django.views.decorators.http import require_POST
from django.utils import translation

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
    
    # Bookmarks için ekran görüntüsü bilgisini ekle
    for bookmark in bookmarks:
        bookmark.has_screenshot = bool(bookmark.screenshot_data)
        # Ekran görüntüsü yolu tanımla
        if bookmark.screenshot_data:
            bookmark.screenshot_path = normalize_thumbnail_path(bookmark.screenshot_data)
    
    # Ana kategorileri getir (kullanıcıya özgü ve genel kategoriler)
    main_categories = Category.objects.filter(
        parent=None,
        user__in=[request.user, None]
    )
    
    # NOT: Varsayılan kategorileri otomatik oluşturmayı kaldırdık
    # Kategoriler artık sadece bookmark eklendiğinde, gerçekten kullanıldıklarında oluşturulacak
    
    # MEDIA_URL'i context'e ekle
    from django.conf import settings
    
    return render(request, 'home/main.html', {
        'bookmarks': bookmarks,
        'main_categories': main_categories,
        'MEDIA_URL': settings.MEDIA_URL
    })

def tags(request):
    # Get all tags with bookmark count (both user's tags and general tags)
    tags = Tag.objects.filter(
        user__in=[request.user, None]
    ).annotate(
        bookmark_count=models.Count('bookmark', filter=models.Q(bookmark__user=request.user))
    ).order_by(models.functions.Lower('name'))  # Use Lower function for case-insensitive sorting
    
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
    
    recent_tags = Tag.objects.filter(
        id__in=recent_tag_ids, 
        user__in=[request.user, None]
    ).annotate(
        bookmark_count=models.Count('bookmark', filter=models.Q(bookmark__user=request.user))
    ).order_by(models.functions.Lower('name'))  # Use Lower function for case-insensitive sorting
    
    # Group tags by first letter for organization
    for tag in tags:
        if tag.name:
            # Use normalized first letter for proper grouping
            first_char = tag.name[0].upper()
            # Check if the first character is a letter
            if first_char.isalpha():
                tag.group = first_char
            else:
                tag.group = '#'  # Non-alphabetic characters go to # group
        else:
            tag.group = '#'
    
    # Sort tags by group for consistent display
    from itertools import groupby
    from operator import attrgetter
    
    # Sort tags by group first, then by name
    sorted_tags = sorted(tags, key=lambda t: (t.group, t.name.lower()))
    
    # Group by letter
    grouped_tags = []
    for k, g in groupby(sorted_tags, key=attrgetter('group')):
        grouped_tags.append({'grouper': k, 'list': list(g)})
    
    return render(request, 'tags/tags.html', {
        'tags': grouped_tags,
        'recent_tags': recent_tags
    })

@login_required(login_url='tagwiseapp:login')
def collections(request):
    """Kullanıcının koleksiyonlarını görüntüler."""
    collections = Collection.objects.filter(user=request.user).order_by('-created_at')
    # Kullanıcının tüm bookmarklarını getir
    bookmarks = Bookmark.objects.filter(user=request.user).order_by('-created_at')
    
    # Debug için bookmark sayısını ve ilk birkaç bookmark'ı yazdır
    bookmark_count = bookmarks.count()
    print(f"DEBUG: Collections - Toplam bookmark sayısı: {bookmark_count}")
    if bookmark_count > 0:
        first_bookmarks = bookmarks[:3]  # İlk 3 bookmark
        for idx, bm in enumerate(first_bookmarks):
            print(f"DEBUG: Collections - Bookmark {idx+1} - ID: {bm.id}, Başlık: {bm.title}")
    else:
        print("DEBUG: Collections - Hiç bookmark bulunamadı!")
    
    return render(request, 'collections/collections.html', {
        'collections': collections,
        'bookmarks': bookmarks
    })

@login_required(login_url='tagwiseapp:login')
def topics(request):
    category_name = request.GET.get('category')
    subcategory_name = request.GET.get('subcategory')
    
    if not category_name or not subcategory_name:
        return redirect('tagwiseapp:categories')
    
    # Önce kullanıcıya özgü kategori ve alt kategorileri ara, yoksa genel olanlara bak
    category = Category.objects.filter(name=category_name, user=request.user).first() or \
               Category.objects.filter(name=category_name, user=None).first()
               
    if category:
        subcategory = Category.objects.filter(
            name=subcategory_name, 
            parent=category,
            user__in=[request.user, None]
        ).first()
    else:
        subcategory = None
    
    if not category or not subcategory:
        return redirect('tagwiseapp:categories')
    
    # Get bookmarks for this subcategory
    bookmarks = Bookmark.objects.filter(
        user=request.user, 
        subcategories=subcategory
    ).order_by('-created_at')
    
    # Bookmarks için ekran görüntüsü bilgisini ekle
    for bookmark in bookmarks:
        bookmark.has_screenshot = bool(bookmark.screenshot_data)
        # Ekran görüntüsü yolu tanımla
        if bookmark.screenshot_data:
            bookmark.screenshot_path = normalize_thumbnail_path(bookmark.screenshot_data)
    
    # Get other subcategories in the same category for navigation
    related_subcategories = Category.objects.filter(
        parent=category,
        user__in=[request.user, None]
    )
    
    # MEDIA_URL'i context'e ekle
    from django.conf import settings
    
    return render(request, 'topics/topics.html', {
        'category': category,
        'subcategory': subcategory,
        'bookmarks': bookmarks,
        'related_subcategories': related_subcategories,
        'MEDIA_URL': settings.MEDIA_URL
    })

@login_required(login_url='tagwiseapp:login')
def tagged_bookmarks(request):
    tag_name = request.GET.get('tag')
    if tag_name:
        # Önce kullanıcıya özgü etiket ara, yoksa genel etikete bak
        tag = Tag.objects.filter(name=tag_name, user=request.user).first() or \
              Tag.objects.filter(name=tag_name, user=None).first()
        
        if tag:
            bookmarks = Bookmark.objects.filter(user=request.user, tags=tag).order_by('-created_at')
            
            # Bookmarks için ekran görüntüsü bilgisini ekle
            for bookmark in bookmarks:
                bookmark.has_screenshot = bool(bookmark.screenshot_data)
                # Ekran görüntüsü yolu tanımla
                if bookmark.screenshot_data:
                    bookmark.screenshot_path = normalize_thumbnail_path(bookmark.screenshot_data)
            
            # MEDIA_URL'i context'e ekle
            from django.conf import settings
            
            return render(request, 'bookmarks/tagged_bookmarks.html', {
                'tag': tag, 
                'bookmarks': bookmarks,
                'MEDIA_URL': settings.MEDIA_URL
            })
    
    return redirect('tagwiseapp:tags')

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
            
            # Thumbnails dizininin varlığını kontrol et ve yoksa oluştur
            thumbnails_dir = os.path.join('media', 'thumbnails')
            if not os.path.exists(thumbnails_dir):
                os.makedirs(thumbnails_dir, exist_ok=True)
                print(f"Thumbnails dizini oluşturuldu: {thumbnails_dir}")
            
            # YouTube URL kontrolü yap
            if is_youtube_url(url):
                print(f"YouTube URL'i tespit edildi, YouTube analizörü kullanılıyor: {url}")
                
                # YouTube video ID'sini çıkar
                video_id = extract_youtube_video_id(url)
                
                if video_id:
                    # YouTube thumbnail'ini indir
                    print(f"YouTube thumbnail indiriliyor: {video_id}")
                    thumbnail_data = fetch_youtube_thumbnail(video_id)
                    
                    if thumbnail_data:
                        # Benzersiz dosya adı oluştur
                        import uuid
                        filename = f"youtube_{video_id}_{uuid.uuid4()}.jpg"
                        thumbnail_path = os.path.join('media', 'thumbnails', filename)
                        
                        # Thumbnail'i kaydet
                        with open(thumbnail_path, 'wb') as f:
                            f.write(thumbnail_data)
                        
                        # Thumbnail yolu için normalize et
                        screenshot_path = normalize_thumbnail_path(thumbnail_path)
                        print(f"YouTube thumbnail kaydedildi: {screenshot_path}")
                
                # YouTube analizini yap - kullanıcıyı analize ilet
                result = analyze_youtube_video(url, user=request.user)
                
                if result:
                    print(f"YouTube analizi tamamlandı: {result}")
                    
                    # Eğer thumbnail kaydedildiyse, sonuca ekle
                    if 'screenshot_path' in locals():
                        result['screenshot_data'] = screenshot_path
                        result['screenshot_used'] = False  # Ekran görüntüsü değil, orijinal thumbnail
                    
                    # YouTube analizinden gelen sonucu döndür
                    converted_result = convert_api_format_for_frontend(result)
                    return JsonResponse(converted_result)
                else:
                    print("YouTube analizi başarısız oldu, standart analiz deneniyor...")
            
            # YouTube analizi yapılmadıysa veya başarısız olduysa, standart analizi devam ettir
            
            # Fetch HTML content
            print("HTML içeriği alınıyor...")
            html = fetch_html(url)
            content = None
            category_json = None
            screenshot_path = None
            screenshot_used = False
            screenshot = None  # Initialize screenshot variable to avoid reference error
            
            if html:
                print("HTML içeriği alındı, içerik çıkarılıyor...")
                # Extract main content
                content = extract_content(html)
                
                # HTML'den thumbnail almayı dene
                from .reader.utils import extract_thumbnail_from_html
                thumbnail = extract_thumbnail_from_html(html, url)
                
                if thumbnail:
                    print("HTML'den thumbnail alındı")
                    # Generate a unique filename for the thumbnail
                    import uuid
                    filename = f"{uuid.uuid4()}.png"
                    
                    # Ensure the path exists
                    thumbnails_dir = os.path.join('media', 'thumbnails')
                    if not os.path.exists(thumbnails_dir):
                        os.makedirs(thumbnails_dir, exist_ok=True)
                        print(f"Thumbnails dizini oluşturuldu: {thumbnails_dir}")
                    
                    thumbnail_path = os.path.join('media', 'thumbnails', filename)
                    
                    # Save the thumbnail
                    with open(thumbnail_path, 'wb') as f:
                        f.write(thumbnail)
                    
                    # Store the relative path in screenshot_path - normalize the path
                    screenshot_path = normalize_thumbnail_path(thumbnail_path)
                    screenshot_used = False
                else:
                    print("HTML'den thumbnail alınamadı, ekran görüntüsü alınıyor...")
                    # Take screenshot as fallback
                    screenshot = capture_screenshot(url)
                    
                    if screenshot:
                        # Generate a unique filename for the screenshot
                        import uuid
                        filename = f"{uuid.uuid4()}.png"
                        
                        # Ensure the path exists
                        thumbnails_dir = os.path.join('media', 'thumbnails')
                        if not os.path.exists(thumbnails_dir):
                            os.makedirs(thumbnails_dir, exist_ok=True)
                            print(f"Thumbnails dizini oluşturuldu: {thumbnails_dir}")
                        
                        thumbnail_path = os.path.join('media', 'thumbnails', filename)
                        
                        # Save the screenshot
                        with open(thumbnail_path, 'wb') as f:
                            f.write(screenshot)
                        
                        # Store the relative path in screenshot_path - normalize the path
                        screenshot_path = normalize_thumbnail_path(thumbnail_path)
                        screenshot_used = True
            
            # HTML içeriği alınamadıysa veya içerik çıkarılamazsa, ekran görüntüsünden kategorize et
            if not html or not content or len(content.strip()) < 50:
                print("HTML içeriği alınamadı veya içerik yetersiz, ekran görüntüsünden analiz yapılıyor...")
                
                # Eğer halihazırda bir ekran görüntüsü yoksa, şimdi al
                if not screenshot:
                    screenshot = capture_screenshot(url)
                
                if screenshot:
                    # Convert binary screenshot to base64 for analysis
                    screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
                    # Ekran görüntüsünü Gemini ile analiz et ve kategorize et
                    # Kullanıcıyı analize ilet
                    category_json = analyze_screenshot(screenshot_base64, url, user=request.user)
                    screenshot_used = True
            
            # Eğer ekran görüntüsü analizi yapılmadıysa veya başarısız olduysa, HTML içeriğini kategorize et
            if not category_json and content:
                print("İçerik çıkarıldı, kategorize ediliyor...")
                # Kategorize içerik - kullanıcıyı analize ilet
                category_json = categorize_content(content, url, user=request.user)
            
            if not content and not category_json:
                return JsonResponse({'error': 'İçerik alınamadı veya analiz edilemedi'}, status=400)
            
            print(f"Kategori JSON: {category_json}")
            
            # Parse JSON string to dict
            try:
                if isinstance(category_json, str):
                    result = json.loads(category_json)
                else:
                    result = category_json
                
                # Add screenshot_used flag and screenshot path to result
                if isinstance(result, dict):
                    result['screenshot_used'] = screenshot_used
                    if screenshot_path:
                        result['screenshot_data'] = screenshot_path
                    
                    # Tags kısmını kontrol et
                    if 'tags' in result:
                        print(f"Result'ta tags var. Tags: {result['tags']}")
                    else:
                        print("Result'ta tags yok.")
                
                # Frontend'in beklediği formata dönüştür
                converted_result = convert_api_format_for_frontend(result)
                return JsonResponse(converted_result)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to use the corrected JSON from the categorization function
                print("JSON ayrıştırma hatası: Hata düzeltme mekanizması deneniyor...")
                try:
                    from .reader.utils import ensure_correct_json_structure
                    
                    # Fallback JSON oluştur
                    fallback_json = ensure_correct_json_structure({}, url)
                    
                    # Add screenshot_used flag and screenshot path to result
                    fallback_json['screenshot_used'] = screenshot_used
                    if screenshot_path:
                        fallback_json['screenshot_data'] = screenshot_path
                    
                    # Tags kısmını kontrol et
                    if 'tags' in fallback_json:
                        print(f"Fallback JSON'da tags var. Tags: {fallback_json['tags']}")
                    else:
                        print("Fallback JSON'da tags yok. Boş dizi ekleniyor.")
                        fallback_json['tags'] = []
                    
                    print(f"Düzeltilmiş fallback JSON: {fallback_json}")
                    converted_fallback = convert_api_format_for_frontend(fallback_json)
                    return JsonResponse(converted_fallback)
                except Exception as fallback_error:
                    print(f"Fallback JSON hatası: {fallback_error}")
                    # If everything fails, return the raw string
                    return JsonResponse({
                        'raw_result': category_json,
                        'screenshot_used': screenshot_used,
                        'screenshot_data': screenshot_path
                    })
            
        except Exception as e:
            print(f"Hata: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Geçersiz istek'}, status=400)

def convert_api_format_for_frontend(data):
    """
    API'dan gelen veri formatını frontend'in beklediği formata dönüştürür.
    
    Args:
        data (dict): API'dan gelen veri
        
    Returns:
        dict: Frontend için dönüştürülmüş veri
    """
    if not isinstance(data, dict):
        return data
    
    result = data.copy()
    
    # Kategorileri dönüştür
    if 'categories' in result and isinstance(result['categories'], list):
        categories_frontend = []
        
        for cat in result['categories']:
            if isinstance(cat, dict) and 'main' in cat and 'sub' in cat:
                # Yeni formattan eski formata dönüşüm
                categories_frontend.append({
                    'main_category': cat['main'],
                    'subcategory': cat['sub']
                })
        
        # Eğer dönüşüm yapıldıysa, orijinal categories'i koru ve yeni format ekle
        if categories_frontend:
            result['categories_original'] = result['categories']
            result['categories'] = categories_frontend
    
    # Etiketleri dönüştür
    if 'tags' in result and isinstance(result['tags'], list):
        tags_frontend = []
        
        for tag in result['tags']:
            if isinstance(tag, dict) and 'name' in tag:
                # Kompleks etiket formatından string formatına dönüşüm
                tags_frontend.append(tag['name'])
            elif isinstance(tag, str):
                # Zaten string ise direkt ekle
                tags_frontend.append(tag)
        
        # Eğer dönüşüm yapıldıysa, orijinal tags'i koru ve yeni format ekle
        if tags_frontend:
            result['tags_original'] = result['tags']
            result['tags'] = tags_frontend
    
    return result

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
            categories = data.get('categories', [])  # Yeni format: [{"main": "...", "sub": "..."}, ...]
            tags = data.get('tags', [])  # Yeni format: [{"name": "..."}, ...]
            screenshot_data = data.get('screenshot_data')
            custom_screenshot = data.get('custom_screenshot')  # Base64 encoded custom screenshot
            
            # Backward compatibility for old format
            main_categories = data.get('main_categories', [])
            subcategories = data.get('subcategories', [])
            category_subcategory_map = data.get('category_subcategory_map', {})
            old_tags = data.get('tags_old', [])  # Eski format taglarını ayrı bir değişkene alıyoruz
            
            # Yeni ve eski formatların birleştirilmesi
            if not categories and main_categories:
                # Eski format kullanılmış, bunu yeni formata dönüştür
                for main_cat in main_categories:
                    sub_cats = category_subcategory_map.get(main_cat, [])
                    if not sub_cats:
                        # Alt kategori yoksa ana kategoriye "Diğer" ekle
                        categories.append({"main": main_cat, "sub": "Diğer"})
                    else:
                        # Her alt kategori için bir kayıt ekle
                        for sub_cat in sub_cats:
                            categories.append({"main": main_cat, "sub": sub_cat})
            
            # Eski format etiketler kullanılmışsa, yeni formata dönüştür
            if not tags and old_tags:
                for tag_name in old_tags:
                    tags.append({"name": tag_name})
            
            # Validate required fields
            if not url or not title or not categories:
                return JsonResponse({'error': 'URL, title, and at least one category are required'}, status=400)
            
            # Process custom screenshot if provided
            if custom_screenshot and screenshot_data:
                try:
                    # Convert base64 to binary
                    screenshot_binary = base64.b64decode(custom_screenshot)
                    
                    # Ensure thumbnails directory exists
                    thumbnails_dir = os.path.join('media', 'thumbnails')
                    if not os.path.exists(thumbnails_dir):
                        os.makedirs(thumbnails_dir, exist_ok=True)
                        print(f"Thumbnails dizini oluşturuldu: {thumbnails_dir}")
                    
                    # Save to file system
                    thumbnail_path = os.path.join('media', 'thumbnails', os.path.basename(screenshot_data))
                    
                    with open(thumbnail_path, 'wb') as f:
                        f.write(screenshot_binary)
                    
                    # Update screenshot_data to use normalized path
                    screenshot_data = normalize_thumbnail_path(thumbnail_path)
                except Exception as e:
                    print(f"Error processing custom screenshot: {str(e)}")
                    # Continue without the custom screenshot if it fails
            
            # Create the bookmark
            bookmark = Bookmark.objects.create(
                url=url,
                title=title,
                description=description,
                user=request.user,
                screenshot_data=screenshot_data
            )
            
            # Kullanılan ana kategorileri ve alt kategorileri takip et
            used_main_categories = []
            used_subcategories = []
            
            # Kategori listeleri için dictionary'ler oluştur
            main_category_dict = {}  # Ana kategori adı -> Category objesi
            
            # Kategorileri ekle - yeni format
            for category_item in categories:
                main_category_name = category_item.get('main')
                sub_category_name = category_item.get('sub')
                
                if not main_category_name:
                    continue  # Ana kategori adı yoksa, bu kategoriyi atla
                
                # Ana kategoriyi işle
                if main_category_name in main_category_dict:
                    # Bu ana kategori daha önce işlendi
                    main_category = main_category_dict[main_category_name]
                else:
                    # Ana kategoriyi bul veya oluştur
                    main_category = Category.objects.filter(name=main_category_name, user=request.user).first() or \
                                    Category.objects.filter(name=main_category_name, user=None).first()
                    
                    if not main_category:
                        # Ana kategori yoksa oluştur
                        main_category = Category.objects.create(name=main_category_name, user=request.user)
                    
                    # Bookmark'a ana kategori ekle
                    bookmark.main_categories.add(main_category)
                    used_main_categories.append(main_category)
                    main_category_dict[main_category_name] = main_category
                
                # Alt kategoriyi işle
                if sub_category_name and sub_category_name != "Diğer":
                    # Alt kategoriyi bul veya oluştur
                    subcategory = Category.objects.filter(name=sub_category_name, user=request.user).first() or \
                                  Category.objects.filter(name=sub_category_name, user=None).first()
                    
                    if not subcategory:
                        # Alt kategori yoksa oluştur
                        subcategory = Category.objects.create(
                            name=sub_category_name, 
                            parent=main_category, 
                            user=request.user
                        )
                    elif not subcategory.parent:
                        # Alt kategorinin parent'ı yoksa ekle
                        subcategory.parent = main_category
                        subcategory.save()
                    
                    # Bookmark'a alt kategori ekle
                    bookmark.subcategories.add(subcategory)
                    used_subcategories.append(sub_category_name)
            
            # Etiketleri ekle - yeni format
            for tag_item in tags:
                # Etiket formatını kontrol et - string veya dict olabilir
                if isinstance(tag_item, dict):
                    tag_name = tag_item.get('name')
                elif isinstance(tag_item, str):
                    tag_name = tag_item
                else:
                    continue  # Geçersiz format
                
                if not tag_name:
                    continue  # Etiket adı yoksa, bu etiketi atla
                
                # Etiketi bul veya oluştur
                tag = Tag.objects.filter(name=tag_name, user=request.user).first() or \
                      Tag.objects.filter(name=tag_name, user=None).first()
                      
                if not tag:
                    # Etiket yoksa oluştur
                    tag = Tag.objects.create(name=tag_name, user=request.user)
                
                # Bookmark'a etiket ekle
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
        category = Category.objects.filter(name=category_name, user=request.user).first() or Category.objects.filter(name=category_name, user=None).first()
        if category:
            bookmarks = Bookmark.objects.filter(user=request.user, main_categories=category).order_by('-created_at')
            return render(request, 'categories/categories.html', {'category': category, 'bookmarks': bookmarks})
    
    # Get all main categories (those without a parent)
    categories = Category.objects.filter(
        parent=None,
        user__in=[request.user, None]  # Kullanıcının kendi kategorileri ve genel kategoriler
    )
    
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
    recent_categories = Category.objects.filter(id__in=recent_category_ids, user__in=[request.user, None])
    
    return render(request, 'categories/categories.html', {
        'categories': categories,
        'recent_categories': recent_categories
    })

@login_required(login_url='tagwiseapp:login')
def subcategories(request):
    category_name = request.GET.get('category')
    if category_name:
        # Önce kullanıcıya özgü kategori ara, yoksa genel kategoriye bak
        category = Category.objects.filter(name=category_name, user=request.user).first() or \
                  Category.objects.filter(name=category_name, user=None).first()
                  
        if category:
            # Kullanıcıya özgü ve genel alt kategorileri getir
            subcategories = Category.objects.filter(parent=category, user__in=[request.user, None])
            return render(request, 'categories/subcategories.html', {'category': category, 'subcategories': subcategories})
    
    return redirect('tagwiseapp:categories')

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
    
    # Tüm bookmarkları sil
    if request.method == 'POST' and 'delete_all_bookmarks' in request.POST:
        # Kullanıcıya ait tüm bookmarkları sayalım
        bookmark_count = Bookmark.objects.filter(user=request.user).count()
        
        # Bookmarkları silme işlemi
        Bookmark.objects.filter(user=request.user).delete()
        
        messages.success(request, f"Tüm bookmarklar başarıyla silindi. Toplam {bookmark_count} bookmark silindi.")
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
    orphan_tags = Tag.objects.annotate(bookmark_count=models.Count('bookmark')).filter(bookmark_count=0, user=user)
    deleted_counts['tags'] = orphan_tags.count()
    for tag in orphan_tags:
        print(f"Orphan tag siliniyor: {tag.name} (user: {tag.user})")
    orphan_tags.delete()
    
    # Orphan alt kategorileri temizle (önce alt kategorileri temizle)
    orphan_subcategories = Category.objects.exclude(parent=None).annotate(
        main_bookmark_count=models.Count('main_bookmarks'),
        sub_bookmark_count=models.Count('sub_bookmarks')
    ).filter(main_bookmark_count=0, sub_bookmark_count=0, user=user)
    
    deleted_counts['subcategories'] = orphan_subcategories.count()
    for subcategory in orphan_subcategories:
        print(f"Orphan alt kategori siliniyor: {subcategory.name} (user: {subcategory.user})")
    orphan_subcategories.delete()
    
    # Orphan ana kategorileri temizle
    orphan_main_categories = Category.objects.filter(parent=None).annotate(
        main_bookmark_count=models.Count('main_bookmarks'),
        sub_bookmark_count=models.Count('sub_bookmarks'),
        children_count=models.Count('children')
    ).filter(main_bookmark_count=0, sub_bookmark_count=0, children_count=0, user=user)
    
    deleted_counts['main_categories'] = orphan_main_categories.count()
    for category in orphan_main_categories:
        print(f"Orphan ana kategori siliniyor: {category.name} (user: {category.user})")
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
        # Get the tag (user's or general)
        tag = Tag.objects.filter(name=tag_name, user=request.user).first() or \
              Tag.objects.filter(name=tag_name, user=None).first()
              
        if not tag:
            return JsonResponse({'success': False, 'error': 'Tag not found'})
        
        # Get bookmarks with this tag
        bookmarks = Bookmark.objects.filter(tags=tag, user=request.user)
        
        # Get all tags from these bookmarks except the current tag
        related_tag_ids = []
        for bookmark in bookmarks:
            related_tag_ids.extend(bookmark.tags.exclude(id=tag.id).values_list('id', flat=True))
        
        # Get unique tags and sort by frequency
        tag_counter = Counter(related_tag_ids)
        most_common_tag_ids = [tag_id for tag_id, _ in tag_counter.most_common(10)]
        
        # Get related tags and order them alphabetically
        related_tags = Tag.objects.filter(
            id__in=most_common_tag_ids,
            user__in=[request.user, None]
        ).order_by('name').values_list('name', flat=True)
        
        return JsonResponse({
            'success': True,
            'related_tags': list(related_tags)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required(login_url='tagwiseapp:login')
def api_tagged_bookmarks(request):
    tag_name = request.GET.get('tag')
    if not tag_name:
        return JsonResponse({'success': False, 'error': 'Tag name is required'})
    
    try:
        # Get the tag (user's or general)
        tag = Tag.objects.filter(name=tag_name, user=request.user).first() or \
              Tag.objects.filter(name=tag_name, user=None).first()
              
        if not tag:
            return JsonResponse({'success': False, 'error': 'Tag not found'})
        
        # Get bookmarks with this tag
        bookmarks = Bookmark.objects.filter(tags=tag, user=request.user).order_by('-created_at')
        
        # Prepare bookmark data
        bookmark_data = []
        for bookmark in bookmarks:
            # Determine thumbnail - use screenshot if available, otherwise placeholder
            has_screenshot = bool(bookmark.screenshot_data)
            screenshot_path = None
            
            if has_screenshot:
                screenshot_path = normalize_thumbnail_path(bookmark.screenshot_data)
            
            bookmark_data.append({
                'id': bookmark.id,
                'url': bookmark.url,
                'title': bookmark.title,
                'description': bookmark.description,
                'has_screenshot': has_screenshot,
                'screenshot_path': screenshot_path,
                'created_at': bookmark.created_at.isoformat(),
                'tags': list(bookmark.tags.values_list('name', flat=True))
            })
        
        return JsonResponse({
            'success': True,
            'bookmarks': bookmark_data
        })
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
            screenshot_data = data.get('screenshot_data')
            custom_screenshot = data.get('custom_screenshot')  # Base64 encoded custom screenshot
            
            # Validate required fields
            if not bookmark_id or not title or not main_categories:
                return JsonResponse({'error': 'Bookmark ID, title, and at least one category are required'}, status=400)
            
            # Get the bookmark
            try:
                bookmark = Bookmark.objects.get(id=bookmark_id, user=request.user)
            except Bookmark.DoesNotExist:
                return JsonResponse({'error': 'Bookmark not found'}, status=404)
            
            # Process custom screenshot if provided
            if custom_screenshot and screenshot_data:
                try:
                    # Convert base64 to binary
                    screenshot_binary = base64.b64decode(custom_screenshot)
                    
                    # Ensure thumbnails directory exists
                    thumbnails_dir = os.path.join('media', 'thumbnails')
                    if not os.path.exists(thumbnails_dir):
                        os.makedirs(thumbnails_dir, exist_ok=True)
                        print(f"Thumbnails dizini oluşturuldu: {thumbnails_dir}")
                    
                    # Save to file system
                    thumbnail_path = os.path.join('media', 'thumbnails', os.path.basename(screenshot_data))
                    
                    with open(thumbnail_path, 'wb') as f:
                        f.write(screenshot_binary)
                    
                    # Update screenshot_data to use normalized path
                    screenshot_data = normalize_thumbnail_path(thumbnail_path)
                except Exception as e:
                    print(f"Error processing custom screenshot: {str(e)}")
                    # Continue without the custom screenshot if it fails
            
            # Update basic fields
            bookmark.title = title
            bookmark.description = description
            
            # Only update screenshot_data if provided
            if screenshot_data:
                bookmark.screenshot_data = screenshot_data
                
            bookmark.save()
            
            # Kullanılan ana kategorileri ve alt kategorileri takip et
            used_main_categories = []
            used_subcategories = []
            
            # Update main categories
            bookmark.main_categories.clear()
            for main_category_name in main_categories:
                # Try to find existing category first (önce kullanıcının kendi kategorisi, sonra genel)
                main_category = Category.objects.filter(name=main_category_name, user=request.user).first() or \
                                Category.objects.filter(name=main_category_name, user=None).first()
                
                if not main_category:
                    # Create new if not exists (kullanıcının kendi kategorisi olarak oluştur)
                    main_category = Category.objects.create(name=main_category_name, user=request.user)
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
                        subcategory = Category.objects.filter(name=subcategory_name, user=request.user).first() or \
                                      Category.objects.filter(name=subcategory_name, user=None).first()
                                      
                        if not subcategory:
                            # Create new if not exists
                            subcategory = Category.objects.create(name=subcategory_name, parent=main_category, user=request.user)
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
                    subcategory = Category.objects.filter(name=subcategory_name, user=request.user).first() or \
                                  Category.objects.filter(name=subcategory_name, user=None).first()
                                  
                    if not subcategory:
                        # Create new if not exists
                        subcategory = Category.objects.create(name=subcategory_name, parent=main_category, user=request.user)
                    elif not subcategory.parent:
                        # Update parent if not set
                        subcategory.parent = main_category
                        subcategory.save()
                    
                    # Add to bookmark
                    bookmark.subcategories.add(subcategory)
                    used_subcategories.append(subcategory_name)
            
            # Update tags
            bookmark.tags.clear()
            for tag_item in tags:
                # Etiket formatını kontrol et - string veya dict olabilir
                if isinstance(tag_item, dict):
                    tag_name = tag_item.get('name')
                elif isinstance(tag_item, str):
                    tag_name = tag_item
                else:
                    continue  # Geçersiz format
                
                if not tag_name:
                    continue  # Etiket adı yoksa, bu etiketi atla
                
                # Etiketi bul veya oluştur
                tag = Tag.objects.filter(name=tag_name, user=request.user).first() or \
                      Tag.objects.filter(name=tag_name, user=None).first()
                      
                if not tag:
                    # Etiket yoksa oluştur
                    tag = Tag.objects.create(name=tag_name, user=request.user)
                
                # Bookmark'a etiket ekle
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
        
        # Get all user bookmarks for the add bookmark modal
        # Artık koleksiyonda olanları hariç tutmuyoruz - bir bookmark birden fazla koleksiyonda olabilir
        all_bookmarks = Bookmark.objects.filter(user=request.user).order_by('-created_at')
        
        # Print for debugging
        print(f"Collection: {collection.name}, Bookmarks count: {bookmarks.count()}, Available bookmarks: {all_bookmarks.count()}")
        
        return render(request, 'collections/collection_detail.html', {
            'collection': collection,
            'bookmarks': bookmarks,
            'all_bookmarks': all_bookmarks
        })
    except Collection.DoesNotExist:
        return redirect('tagwiseapp:collections')

@csrf_protect
@login_required(login_url='tagwiseapp:login')
def update_collection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract data
            collection_id = data.get('id')
            name = data.get('name')
            description = data.get('description', '')
            icon = data.get('icon', 'collections_bookmark')
            
            # Validate required fields
            if not collection_id or not name:
                return JsonResponse({'error': 'Collection ID and name are required'}, status=400)
            
            # Get the collection
            try:
                collection = Collection.objects.get(id=collection_id, user=request.user)
            except Collection.DoesNotExist:
                return JsonResponse({'error': 'Collection not found'}, status=404)
            
            # Update the collection
            collection.name = name
            collection.description = description
            collection.icon = icon
            collection.save()
            
            # Return success response with updated collection data
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

@csrf_protect
@login_required(login_url='tagwiseapp:login')
def delete_collection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract collection ID
            collection_id = data.get('id')
            
            # Validate required fields
            if not collection_id:
                return JsonResponse({'error': 'Collection ID is required'}, status=400)
            
            # Get the collection
            try:
                collection = Collection.objects.get(id=collection_id, user=request.user)
            except Collection.DoesNotExist:
                return JsonResponse({'error': 'Collection not found'}, status=404)
            
            # Delete the collection
            collection.delete()
            
            # Return success response
            return JsonResponse({
                'success': True,
                'message': 'Collection deleted successfully'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

@csrf_protect
@login_required(login_url='tagwiseapp:login')
def add_bookmarks_to_collection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract data
            collection_id = data.get('collection_id')
            bookmark_ids = data.get('bookmark_ids', [])
            
            # Validate required fields
            if not collection_id or not bookmark_ids:
                return JsonResponse({'error': 'Collection ID and bookmark IDs are required'}, status=400)
            
            # Get the collection
            try:
                collection = Collection.objects.get(id=collection_id, user=request.user)
            except Collection.DoesNotExist:
                return JsonResponse({'error': 'Collection not found'}, status=404)
            
            # Get the bookmarks
            bookmarks = Bookmark.objects.filter(id__in=bookmark_ids, user=request.user)
            
            # Add bookmarks to the collection
            collection.bookmarks.add(*bookmarks)
            
            # Return success response
            return JsonResponse({
                'success': True,
                'message': f'{bookmarks.count()} bookmarks added to collection',
                'bookmark_count': collection.bookmarks.count()
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

@csrf_protect
@login_required(login_url='tagwiseapp:login')
def remove_bookmark_from_collection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract data
            collection_id = data.get('collection_id')
            bookmark_id = data.get('bookmark_id')
            
            # Validate required fields
            if not collection_id or not bookmark_id:
                return JsonResponse({'error': 'Collection ID and bookmark ID are required'}, status=400)
            
            # Get the collection
            try:
                collection = Collection.objects.get(id=collection_id, user=request.user)
            except Collection.DoesNotExist:
                return JsonResponse({'error': 'Collection not found'}, status=404)
            
            # Get the bookmark
            try:
                bookmark = Bookmark.objects.get(id=bookmark_id, user=request.user)
            except Bookmark.DoesNotExist:
                return JsonResponse({'error': 'Bookmark not found'}, status=404)
            
            # Remove bookmark from the collection
            collection.bookmarks.remove(bookmark)
            
            # Return success response
            return JsonResponse({
                'success': True,
                'message': 'Bookmark removed from collection',
                'bookmark_count': collection.bookmarks.count()
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

# Login Gerektiren Servisler
@login_required(login_url='tagwiseapp:login')
def profile_settings(request):
    """Kullanıcı profil ayarları sayfasını gösterir."""
    success_message = request.session.pop('success_message', None)
    error_message = request.session.pop('error_message', None)
    
    context = {
        'success_message': success_message,
        'error_message': error_message
    }
    
    return render(request, 'settings/profile.html', context)

@login_required(login_url='tagwiseapp:login')
def update_profile_photo(request):
    """Kullanıcı profil fotoğrafını günceller."""
    if request.method == 'POST':
        try:
            # Base64 formatında gelen profil fotoğrafını al
            base64_image = request.POST.get('profile_photo')
            
            if not base64_image:
                request.session['error_message'] = 'Lütfen bir profil fotoğrafı seçin.'
                return redirect('tagwiseapp:profile_settings')
            
            # Make sure user has a profile
            if not hasattr(request.user, 'profile'):
                Profile.objects.create(user=request.user)
                print(f"Yeni profil oluşturuldu - {request.user.username}")
            
            # Delete old photo if exists
            if request.user.profile.profile_photo:
                try:
                    old_photo_path = request.user.profile.profile_photo.path
                    if os.path.exists(old_photo_path):
                        os.remove(old_photo_path)
                        print(f"Eski profil fotoğrafı silindi: {old_photo_path}")
                except Exception as e:
                    print(f"Eski fotoğraf silinirken hata: {str(e)}")
            
            # Base64 formatındaki görüntüyü işle
            # Format: "data:image/jpeg;base64,/9j/4AAQSkZJRgABA..."
            if ',' in base64_image:
                format, imgstr = base64_image.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr))
                
                # Dosya adını oluştur
                filename = f'profile_{request.user.username}_{int(time.time())}.{ext}'
                
                # Profil fotoğrafını kaydet
                request.user.profile.profile_photo.save(filename, data, save=True)
                print(f"Yeni profil fotoğrafı kaydedildi: {request.user.profile.profile_photo.url}")
                
                request.session['success_message'] = 'Profil fotoğrafınız başarıyla güncellendi.'
            else:
                request.session['error_message'] = 'Geçersiz görüntü formatı.'
                
            return redirect('tagwiseapp:profile_settings')
        except Exception as e:
            import traceback
            print(f"Profil fotoğrafı güncellenirken hata: {str(e)}")
            print(traceback.format_exc())
            request.session['error_message'] = f'Profil fotoğrafı güncellenirken bir hata oluştu: {str(e)}'
            return redirect('tagwiseapp:profile_settings')
    
    return redirect('tagwiseapp:profile_settings')

@login_required(login_url='tagwiseapp:login')
def update_profile(request):
    """Kullanıcı profil bilgilerini günceller."""
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            name = request.POST.get('name').strip()
            
            if not email:
                request.session['error_message'] = 'E-posta adresi gereklidir.'
                return redirect('tagwiseapp:profile_settings')
            
            # E-posta adresini güncelle
            request.user.email = email
            
            # Ad Soyad'ı güncelle
            if name:
                # Ad ve soyadı ayır
                name_parts = name.split(' ', 1)
                request.user.first_name = name_parts[0]
                request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            request.user.save()
            
            request.session['success_message'] = 'Profil bilgileriniz başarıyla güncellendi.'
            return redirect('tagwiseapp:profile_settings')
        except Exception as e:
            request.session['error_message'] = f'Profil bilgileri güncellenirken bir hata oluştu: {str(e)}'
            return redirect('tagwiseapp:profile_settings')
    
    return redirect('tagwiseapp:profile_settings')

@login_required(login_url='tagwiseapp:login')
def change_password(request):
    """Kullanıcı şifresini değiştirir."""
    if request.method == 'POST':
        try:
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Şifreleri kontrol et
            if not current_password or not new_password or not confirm_password:
                request.session['error_message'] = 'Tüm alanlar doldurulmalıdır.'
                return redirect('tagwiseapp:profile_settings')
            
            if new_password != confirm_password:
                request.session['error_message'] = 'Yeni şifreler eşleşmiyor.'
                return redirect('tagwiseapp:profile_settings')
            
            # Mevcut şifreyi doğrula
            if not request.user.check_password(current_password):
                request.session['error_message'] = 'Mevcut şifre yanlış.'
                return redirect('tagwiseapp:profile_settings')
            
            # Yeni şifreyi ayarla
            request.user.set_password(new_password)
            request.user.save()
            
            # Kullanıcıyı yeniden giriş yaptır
            user = authenticate(username=request.user.username, password=new_password)
            login(request, user)
            
            request.session['success_message'] = 'Şifreniz başarıyla değiştirildi.'
            return redirect('tagwiseapp:profile_settings')
        except Exception as e:
            request.session['error_message'] = f'Şifre değiştirilirken bir hata oluştu: {str(e)}'
            return redirect('tagwiseapp:profile_settings')
    
    return redirect('tagwiseapp:profile_settings')

@login_required(login_url='tagwiseapp:login')
def update_notifications(request):
    """Kullanıcı bildirim tercihlerini günceller."""
    if request.method == 'POST':
        try:
            # Check if the request is JSON (AJAX) or form data
            if request.content_type == 'application/json':
                # Parse JSON data
                data = json.loads(request.body)
                email_notifications = data.get('email_notifications', False)
                new_features = data.get('new_features', False)
            else:
                # Process form data
                email_notifications = 'email_notifications' in request.POST
                new_features = 'new_features' in request.POST
            
            # Kullanıcının profil modeli yoksa oluştur
            if not hasattr(request.user, 'profile'):
                Profile.objects.create(user=request.user)
            
            # Bildirim tercihlerini güncelle
            request.user.profile.email_notifications = email_notifications
            request.user.profile.new_features = new_features
            request.user.profile.save()
            
            # Return JSON response for AJAX requests
            if request.content_type == 'application/json':
                return JsonResponse({'status': 'success'})
            
            # Return redirect for form submissions
            request.session['success_message'] = 'Bildirim tercihleriniz başarıyla güncellendi.'
            return redirect('tagwiseapp:profile_settings')
        except Exception as e:
            if request.content_type == 'application/json':
                return JsonResponse({'status': 'error', 'message': str(e)})
            
            request.session['error_message'] = f'Bildirim tercihleri güncellenirken bir hata oluştu: {str(e)}'
            return redirect('tagwiseapp:profile_settings')
    
    return redirect('tagwiseapp:profile_settings')

@login_required(login_url='tagwiseapp:login')
def search_bookmarks(request):
    query = request.GET.get('query', '')
    filter_title = request.GET.get('filter_title', 'on')
    filter_url = request.GET.get('filter_url', 'on')
    filter_tags = request.GET.get('filter_tags', 'on')
    
    if not query:
        return redirect('tagwiseapp:index')
    
    # Get bookmarks for the logged-in user
    bookmarks = Bookmark.objects.filter(user=request.user)
    
    # Apply filters
    filter_conditions = Q()
    if filter_title == 'on':
        filter_conditions |= Q(title__icontains=query)
    if filter_url == 'on':
        filter_conditions |= Q(url__icontains=query)
    if filter_tags == 'on':
        filter_conditions |= Q(tags__name__icontains=query)
    
    bookmarks = bookmarks.filter(filter_conditions).distinct()
    
    # Get main categories for filter dropdown
    main_categories = Category.objects.filter(parent=None)
    
    context = {
        'bookmarks': bookmarks,
        'main_categories': main_categories,
        'search_query': query,
        'is_search': True,
        'filter_title': filter_title,
        'filter_url': filter_url,
        'filter_tags': filter_tags,
    }
    
    return render(request, 'home/main.html', context)

@login_required(login_url='tagwiseapp:login')
def search_categories(request):
    query = request.GET.get('query', '')
    
    if not query:
        return redirect('tagwiseapp:categories')
    
    # Search in main categories
    main_categories = Category.objects.filter(
        Q(name__icontains=query),
        parent=None
    )
    
    # Add bookmark count and icon to categories
    for category in main_categories:
        category.bookmark_count = Bookmark.objects.filter(main_categories=category, user=request.user).count()
        category.icon_name = 'category'  # Default icon
        category.color = '#2196F3'  # Default color
    
    # Get recent categories for adding to search results
    recent_categories = Category.objects.filter(
        parent=None,
        main_bookmarks__user=request.user
    ).annotate(
        bookmark_count=Count('main_bookmarks', filter=Q(main_bookmarks__user=request.user))
    ).order_by('-main_bookmarks__created_at')[:5]
    
    # Add icon and color to recent categories
    for category in recent_categories:
        category.icon_name = 'category'  # Default icon
        category.color = '#2196F3'  # Default color
    
    context = {
        'main_categories': main_categories,
        'recent_categories': recent_categories,
        'search_query': query,
        'is_search': True
    }
    
    return render(request, 'categories/search_results.html', context)

@login_required(login_url='tagwiseapp:login')
def search_tags(request):
    query = request.GET.get('query', '')
    
    if not query:
        return redirect('tagwiseapp:tags')
    
    # Search in tags (both user's tags and general tags)
    tags = Tag.objects.filter(
        name__icontains=query,
        user__in=[request.user, None]
    ).order_by('name')
    
    # Get bookmark count for each tag
    for tag in tags:
        tag.bookmark_count = Bookmark.objects.filter(tags=tag, user=request.user).count()
    
    # Group tags by first letter
    grouped_tags = {}
    for tag in tags:
        first_letter = tag.name[0].upper()
        if first_letter not in grouped_tags:
            grouped_tags[first_letter] = []
        grouped_tags[first_letter].append(tag)
    
    # Sort the groups by letter
    grouped_tags = dict(sorted(grouped_tags.items()))
    
    # Sort tags within each group alphabetically
    for letter in grouped_tags:
        grouped_tags[letter] = sorted(grouped_tags[letter], key=lambda x: x.name)
    
    # Get recent tags
    recent_tags = Tag.objects.filter(
        bookmark__user=request.user,
        user__in=[request.user, None]
    ).annotate(
        bookmark_count=Count('bookmark', filter=Q(bookmark__user=request.user))
    ).order_by('name')[:10]
    
    context = {
        'grouped_tags': grouped_tags,
        'recent_tags': recent_tags,
        'search_query': query,
        'is_search': True
    }
    
    return render(request, 'tags/search_results.html', context)

def normalize_thumbnail_path(screenshot_data):
    """
    Standardize thumbnail path handling.
    Returns path relative to MEDIA_ROOT, starting with 'thumbnails/'
    For external URLs (starting with http), returns the original URL.
    """
    if not screenshot_data:
        return None
    
    # Direct external URL case (starting with http or https)
    if screenshot_data.startswith(('http://', 'https://')):
        return screenshot_data
    
    # Backward compatibility for external: prefix
    if screenshot_data.startswith('external:'):
        return screenshot_data[9:]  # Remove "external:" prefix
        
    # If already starts with thumbnails/, use as is
    if screenshot_data.startswith('thumbnails/'):
        return screenshot_data
    # If starts with media/, remove media/ prefix
    elif screenshot_data.startswith('media/'):
        path = screenshot_data[6:]  # Remove "media/" prefix
        # Ensure it starts with thumbnails/
        return f"thumbnails/{path.split('thumbnails/')[-1]}" if 'thumbnails/' in path else f"thumbnails/{path}"
    # Otherwise add thumbnails/ prefix
    else:
        return f"thumbnails/{screenshot_data}"

@login_required
def get_bookmark_details(request):
    """
    Bookmark detaylarını döndüren API endpoint'i
    """
    if request.method == 'GET':
        bookmark_id = request.GET.get('id')
        
        if not bookmark_id:
            return JsonResponse({'success': False, 'error': 'Bookmark ID is required'})
        
        try:
            # Bookmark'u ve ilişkili verileri al
            bookmark = Bookmark.objects.filter(id=bookmark_id, user=request.user).first()
            
            if not bookmark:
                return JsonResponse({'success': False, 'error': 'Bookmark not found or not authorized'})
            
            # Ana kategorileri ve alt kategorileri al
            main_categories = list(bookmark.main_categories.all().values('id', 'name'))
            subcategories = list(bookmark.subcategories.all().values('id', 'name', 'parent'))
            
            # Etiketleri al
            tags = list(bookmark.tags.all().values('id', 'name'))
            
            # Kategori ilişkilerini hazırla
            category_subcategory_map = {}
            
            # Her ana kategori için, bu kategoriye ait alt kategorileri bul
            for main_category in main_categories:
                category_subcategory_map[main_category['name']] = []
                
                # Bu ana kategoriye ait alt kategorileri bul
                for subcategory in subcategories:
                    # Eğer alt kategorinin parent_id'si bu ana kategorinin id'sine eşitse veya
                    # alt kategorinin adı ana kategorinin adı ile başlıyorsa, bu alt kategoriyi
                    # ana kategoriye bağla
                    if subcategory.get('parent') == main_category['id']:
                        category_subcategory_map[main_category['name']].append(subcategory['name'])
            
            # Response data
            bookmark_data = {
                'id': bookmark.id,
                'url': bookmark.url,
                'title': bookmark.title,
                'description': bookmark.description,
                'main_categories': main_categories,
                'subcategories': subcategories,
                'tags': tags,
                'category_subcategory_map': category_subcategory_map
            }
            
            return JsonResponse({
                'success': True,
                'bookmark': bookmark_data
            })
            
        except Exception as e:
            import traceback
            print(f"Error getting bookmark details: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@require_POST
@login_required
def update_language(request):
    """Update the language preference for a user"""
    try:
        # Check content type
        if request.content_type != 'application/json':
            return JsonResponse({
                'status': 'error', 
                'message': 'Invalid content type. Expected application/json'
            }, status=400)
            
        # Parse the JSON body
        data = json.loads(request.body)
        language = data.get('language')
        
        # Check if language is provided
        if not language:
            return JsonResponse({
                'status': 'error', 
                'message': 'Language parameter is required'
            }, status=400)
            
        # Validate language
        valid_languages = [lang[0] for lang in settings.LANGUAGES]
        if language not in valid_languages:
            return JsonResponse({
                'status': 'error', 
                'message': f'Invalid language selection. Valid options are: {", ".join(valid_languages)}'
            }, status=400)
            
        # Update user's profile with new language preference
        request.user.profile.language = language
        request.user.profile.save()
        
        # Update the session language
        translation.activate(language)
        request.session[translation.LANGUAGE_SESSION_KEY] = language
        
        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error', 
            'message': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        import traceback
        print(f"Error updating language: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'status': 'error', 
            'message': 'An unexpected error occurred while updating language setting'
        }, status=500)