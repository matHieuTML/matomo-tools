from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import pandas as pd
from datetime import datetime
from .models import MatomoSite, AnalyticsResult

def index(request):
    return render(request, 'dashboard/index.html')

@csrf_exempt
def verify_token(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        if not token:
            return JsonResponse({'success': False, 'error': 'Token manquant'})

        matomo_url = 'https://cidj.matomo.cloud/index.php'
        site_id = 10  # ID du site CIDJ
        
        # Test simple avec une requête basique de métriques
        api_url = f'{matomo_url}?module=API&method=Actions.get'
        api_url += f'&idSite={site_id}&period=day&date=today&format=JSON&token_auth={token}'
        
        try:
            print(f'Tentative de connexion à Matomo avec l\'URL : {api_url}')
            response = requests.get(api_url)
            print(f'Statut de la réponse : {response.status_code}')
            print(f'Contenu de la réponse : {response.text[:500]}')
            
            if response.status_code == 200:
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
                    if 'message' in error_data:
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
            return JsonResponse({'success': False, 'error': 'No token found'})
            
        site_id = request.POST.get('site_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        metrics = request.POST.getlist('metrics[]')
        file = request.FILES.get('urls_file')
        
        if not all([site_id, start_date, end_date, metrics, file]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
            
        # Read URLs from Excel file
        try:
            df = pd.read_excel(file)
            urls = df.iloc[:, 0].tolist()
        except:
            return JsonResponse({'success': False, 'error': 'Invalid Excel file'})
            
        results = []
        matomo_url = 'https://cidj.matomo.cloud/index.php'
        
        for url in urls:
            api_url = f'{matomo_url}?module=API&method=Actions.getPageUrl'
            api_url += f'&idSite={site_id}&period=range&date={start_date},{end_date}'
            api_url += f'&pageUrl={url}&format=JSON&token_auth={token}'
            
            try:
                response = requests.get(api_url)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        page_data = data[0]
                        result = {
                            'url': url,
                            'visits': page_data.get('nb_visits', 0),
                            'pageviews': page_data.get('nb_hits', 0),
                            'bounce_rate': page_data.get('bounce_rate', '0%')
                        }
                        results.append(result)
            except:
                continue
                
        return JsonResponse({'success': True, 'results': results})
        
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
