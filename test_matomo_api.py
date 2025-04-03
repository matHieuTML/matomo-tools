import requests
import sys

def test_matomo_api(url):
    try:
        # Test with requests library
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print("\nResponse Headers:")
        for key, value in response.headers.items():
            print(f"{key}: {value}")
        
        print("\nResponse Content:")
        print(response.text)
        
        # Check for specific issues
        if response.status_code == 403:
            print("\nPossible issues:")
            print("- Token might be invalid")
            print("- CORS policy might be blocking the request")
            print("- IP might not be whitelisted")
        
    except requests.exceptions.SSLError as e:
        print("SSL Error:", e)
    except requests.exceptions.ConnectionError as e:
        print("Connection Error:", e)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    url = "https://cidj.matomo.cloud/index.php?module=API&method=VisitsSummary.getVisits&idSite=1&period=week&date=today&format=json&token_auth=0fa65b4bb61e9d2727a0ca9e20d638ce"
    test_matomo_api(url)
