from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import pandas as pd
from datetime import datetime
from .models import MatomoSite, AnalyticsResult

def index(request):
    return render(request, 'dashboard/index.html')

def url_analyzer(request):
    return render(request, 'dashboard/url_analyzer.html')

def export_excel(request):
    if 'metrics_data' not in request.session:
        return JsonResponse({'error': 'Aucune donnée à exporter'}, status=400)
    
    metrics = request.session['metrics_data']
    df = pd.DataFrame(metrics)
    
    # Créer le fichier Excel en mémoire
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=matomo_metrics.xlsx'
    
    # Écrire les données dans le fichier Excel
    df.to_excel(response, index=False, sheet_name='Métriques')
    
    return response

@csrf_exempt
def verify_token(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        if not token:
            return JsonResponse({'success': False, 'error': 'Token manquant'})

        matomo_url = 'https://cidj.matomo.cloud/index.php'
        site_id = 10  # ID du site CIDJ
        
        # Vérifier l'accès avec une requête simple sur les métriques du site CIDJ
        test_url = f'{matomo_url}?module=API&method=VisitsSummary.get'
        test_url += f'&idSite={site_id}&period=day&date=today&format=JSON&token_auth={token}'
        
        try:
            print(f'Vérification du token avec l\'URL : {test_url}')
            response = requests.get(test_url)
            print(f'Statut de la réponse : {response.status_code}')
            print(f'Contenu de la réponse : {response.text[:500]}')
            
            if response.status_code == 200:
                # Le token est valide pour le site CIDJ
                request.session['matomo_token'] = token
                sites_data = [{
                    'id': site_id,
                    'name': 'CIDJ'
                }]
                return JsonResponse({'success': True, 'sites': sites_data})
            else:
                error_msg = 'Token invalide ou accès refusé'
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict) and 'message' in error_data:
                        error_msg = error_data['message']
                except:
                    pass
                return JsonResponse({'success': False, 'error': error_msg})
                
        except requests.RequestException as e:
            return JsonResponse({'success': False, 'error': f'Erreur de connexion : {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Méthode invalide'})

@csrf_exempt
def fetch_metrics(request):
    if request.method == 'POST':
        token = request.session.get('matomo_token')
        if not token:
            return JsonResponse({'success': False, 'error': 'Token manquant'})
            
        site_id = request.POST.get('site_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if not all([site_id, start_date, end_date]):
            return JsonResponse({'success': False, 'error': 'Dates ou site manquants'})
        
        # Récupération des URLs soit depuis le texte, soit depuis le fichier Excel
        urls_list = []
        if 'urls' in request.POST:
            urls = request.POST.get('urls')
            if urls:
                urls_list = [url.strip() for url in urls.split('\n') if url.strip()]
        elif 'excel_file' in request.FILES:
            try:
                excel_file = request.FILES['excel_file']
                df = pd.read_excel(excel_file)
                
                # Vérifie si le fichier a au moins une colonne
                if df.empty or len(df.columns) == 0:
                    return JsonResponse({'success': False, 'error': 'Le fichier Excel est vide'})
                
                # Prend la première colonne comme liste d'URLs
                urls_list = df.iloc[:, 0].dropna().tolist()
                urls_list = [str(url).strip() for url in urls_list if str(url).strip()]
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Erreur lors de la lecture du fichier Excel : {str(e)}'})
        
        if not urls_list:
            return JsonResponse({'success': False, 'error': 'Aucune URL fournie'})
            
        results = []
        matomo_url = 'https://cidj.matomo.cloud/index.php'
        
        for url in urls_list:
            # Formater l'URL pour qu'elle corresponde au format Matomo
            try:
                parsed_url = requests.utils.urlparse(url)
                path_url = parsed_url.path
                if not path_url:
                    path_url = '/'
            except Exception as e:
                print(f'Erreur lors du parsing de l\'URL {url}: {str(e)}')
                path_url = url

            # Récupérer les métriques pour une URL spécifique
            api_url = f'{matomo_url}'
            params = {
                'module': 'API',
                'method': 'Actions.getPageUrl',
                'idSite': site_id,
                'period': 'range',
                'date': f'{start_date},{end_date}',
                'pageUrl': path_url,
                'format': 'json',
                'token_auth': token,
                'expanded': 1,
                'filter_limit': -1
            }
            
            # Afficher l'URL complète pour le débogage
            full_url = requests.Request('GET', api_url, params=params).prepare().url
            print(f'\nURL complète de l\'API: {full_url}')
            
            try:
                response = requests.get(api_url, params=params)
                print(f'\nTraitement de l\'URL: {url}')
                print(f'Status code: {response.status_code}')
                print(f'Response content: {response.text}')
                
                if response.status_code == 200:
                    data = response.json()
                    print(f'Données JSON reçues: {data}')
                    
                    # Vérifier si nous avons des données valides
                    if isinstance(data, dict) and 'result' in data and data['result'] == 'error':
                        print(f'Erreur API pour {url}: {data.get("message")}')
                        page_data = None
                    else:
                        # L'API retourne une liste, prendre le premier élément s'il existe
                        page_data = data[0] if isinstance(data, list) and len(data) > 0 else None
                    
                    if page_data:
                        # Extraire les métriques de la réponse
                        metrics = {
                            'url': url,
                            'visits': page_data['nb_visits'],
                            'unique_pageviews': page_data['sum_daily_nb_uniq_visitors'],  # Utiliser le bon champ
                            'bounce_rate': page_data['bounce_rate'],  # Déjà formaté avec %
                            'avg_time': f"{page_data['avg_time_on_page']}s"
                        }
                    else:
                        metrics = {
                            'url': url,
                            'visits': 0,
                            'unique_pageviews': 0,
                            'bounce_rate': '-',
                            'avg_time': '-'
                        }
                    
                    print(f'Métriques extraites: {metrics}')
                    results.append(metrics)
                else:
                    print(f'Erreur API pour {url}: {response.status_code}')
                    results.append({
                        'url': url,
                        'visits': 0,
                        'unique_pageviews': 0,
                        'bounce_rate': '-',
                        'avg_time': '-',
                        'error': f'Erreur API: {response.status_code}'
                    })
            except Exception as e:
                print(f'Exception pour {url}: {str(e)}')
                results.append({
                    'url': url,
                    'visits': 0,
                    'unique_pageviews': 0,
                    'bounce_rate': '-',
                    'avg_time': '-',
                    'error': str(e)
                })
        
        # Stocker les résultats dans la session
        request.session['metrics_data'] = results
        return JsonResponse({'success': True, 'metrics': results})
    
    return JsonResponse({'success': False, 'error': 'Méthode invalide'})

