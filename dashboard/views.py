from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import pandas as pd
from datetime import datetime
from .models import MatomoSite, AnalyticsResult
from django.core.cache import cache

def index(request):
    return render(request, 'dashboard/index.html')

@csrf_exempt
def verify_matomo_config(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        token = request.POST.get('token')
        
        print(f"Vérification de la configuration Matomo - URL: {url}")
        
        if not url or not token:
            print("Erreur: URL ou token manquant")
            return JsonResponse({'error': 'URL et token requis'}, status=400)
        
        # Nettoyer l'URL si nécessaire
        url = url.rstrip('/')
        if not url.startswith('http'):
            url = f'https://{url}'
        
        # Construire l'URL de l'API pour récupérer les sites
        api_url = f"{url}/index.php"
        params = {
            'module': 'API',
            'method': 'SitesManager.getSitesWithAtLeastViewAccess',
            'format': 'json'
        }
        data = {
            'token_auth': token
        }
        print(f"Tentative de connexion à l'API Matomo: {api_url}")
        
        try:
            response = requests.post(api_url, params=params, data=data, timeout=10)  # Timeout de 10 secondes
            print(f"Réponse de l'API - Status: {response.status_code}")
            print(f"Contenu de la réponse: {response.text[:500]}...")
            
            data = response.json()
            print(f"Type de données reçu: {type(data)}")
            
            # Vérifier si nous avons une erreur dans la réponse
            if isinstance(data, dict) and data.get('result') == 'error':
                error_msg = data.get('message', 'Erreur inconnue')
                print(f"Erreur de l'API: {error_msg}")
                return JsonResponse({'error': f'Erreur Matomo: {error_msg}'}, status=400)
            
            # Vérifier si nous avons une liste de sites ou un dictionnaire de sites
            sites_data = data if isinstance(data, list) else data.get('value', [])
            
            if not isinstance(sites_data, list):
                print(f"Format de réponse invalide: {data}")
                return JsonResponse({'error': 'Réponse invalide de lèAPI Matomo'}, status=400)
            
            # Stocker la configuration dans le cache Django
            cache.set('matomo_config', {
                'url': url,
                'token': token
            }, timeout=86400)  # Cache pour 24 heures
            
            # Convertir les données en liste de sites
            sites = [{'id': site.get('idsite'), 'name': site.get('name')} for site in sites_data if site.get('idsite')]
            print(f"Sites trouvés: {len(sites)}")
            
            return JsonResponse({
                'success': True,
                'sites': sites
            })
                
        except requests.exceptions.Timeout:
            print("Timeout de la requête API")
            return JsonResponse({'error': 'Timeout de la connexion à Matomo'}, status=500)
        except requests.exceptions.SSLError as e:
            print(f"Erreur SSL: {str(e)}")
            return JsonResponse({'error': 'Erreur de sécurité SSL'}, status=500)
        except requests.exceptions.ConnectionError as e:
            print(f"Erreur de connexion: {str(e)}")
            return JsonResponse({'error': 'Impossible de se connecter à Matomo'}, status=500)
        except requests.RequestException as e:
            print(f"Erreur de requête: {str(e)}")
            return JsonResponse({'error': f'Erreur de connexion : {str(e)}'}, status=500)
        except ValueError as e:
            print(f"Erreur de parsing JSON: {str(e)}")
            return JsonResponse({'error': 'Réponse invalide de Matomo'}, status=500)
        except Exception as e:
            print(f"Erreur inattendue: {str(e)}")
            return JsonResponse({'error': f'Erreur inattendue: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

def ai_assistant(request):
    return render(request, 'dashboard/ai_assistant.html')

@csrf_exempt
def proxy_matomo_api(request):
    if request.method == 'POST':
        try:
            api_url = request.POST.get('url')
            if not api_url:
                return JsonResponse({'error': 'URL manquante'}, status=400)

            response = requests.get(api_url)
            return JsonResponse(response.json(), safe=False)

        except requests.RequestException as e:
            return JsonResponse({'error': str(e)}, status=500)
        except ValueError as e:
            return JsonResponse({'error': 'Réponse invalide de Matomo'}, status=500)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

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
        matomo_url = request.POST.get('matomo_url')
        token = request.POST.get('token')
        site_id = request.POST.get('site_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if not all([matomo_url, token, site_id, start_date, end_date]):
            return JsonResponse({'success': False, 'error': 'Paramètres manquants'})
        
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
        api_url = f'{matomo_url}/index.php'
        
        for url in urls_list:
            # Formater l'URL pour qu'elle corresponde au format Matomo
            try:
                if not url.startswith('http'):
                    url = f'https://{url}'
            except Exception as e:
                print(f'Erreur lors du parsing de l\'URL {url}: {str(e)}')

            # Récupérer les métriques pour une URL spécifique
            params = {
                'module': 'API',
                'method': 'Actions.getPageUrl',
                'idSite': site_id,
                'period': 'range',
                'date': f'{start_date},{end_date}',
                'pageUrl': url,
                'format': 'json',
                'token_auth': token,
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
