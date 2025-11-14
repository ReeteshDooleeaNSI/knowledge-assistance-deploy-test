#!/usr/bin/env python3
"""
Script pour obtenir un refresh token Zoho Desk.

Étapes:
1. Configurez vos credentials dans ce script ou via variables d'environnement
2. Exécutez le script pour obtenir l'URL d'autorisation
3. Visitez l'URL dans votre navigateur et autorisez l'application
4. Copiez le code depuis l'URL de redirection
5. Le script échangera le code contre un refresh token
"""

import os
import sys
from urllib.parse import parse_qs, urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

# Configuration - Remplissez ces valeurs ou utilisez des variables d'environnement
CLIENT_ID = os.getenv("ZOHO_CLIENT_ID") or input("Entrez votre ZOHO_CLIENT_ID: ").strip()
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET") or input("Entrez votre ZOHO_CLIENT_SECRET: ").strip()

# IMPORTANT: Le REDIRECT_URI doit correspondre EXACTEMENT à celui configuré dans Zoho Developer Console
# Options communes: http://localhost:8080/callback, http://localhost/callback, https://yourdomain.com/callback
REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI")

# Scopes nécessaires pour Zoho Desk
SCOPES = "Desk.search.READ,Desk.tickets.READ,Desk.contacts.READ,Desk.tasks.READ"

# URL d'autorisation Zoho
AUTH_URL = "https://accounts.zoho.eu/oauth/v2/auth"
TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"


def get_authorization_url() -> str:
    """Génère l'URL d'autorisation OAuth."""
    from urllib.parse import urlencode
    
    params = {
        "scope": SCOPES,
        "client_id": CLIENT_ID,
        "response_type": "code",
        "access_type": "offline",  # CRITIQUE: doit être "offline" pour obtenir un refresh_token
        "redirect_uri": REDIRECT_URI,
    }
    
    query_string = urlencode(params)
    return f"{AUTH_URL}?{query_string}"


def exchange_code_for_token(authorization_code: str) -> dict:
    """Échange le code d'autorisation contre un refresh token."""
    async def _exchange():
        async with httpx.AsyncClient() as client:
            # Essayer d'abord avec form data (méthode standard OAuth)
            request_data = {
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": authorization_code,
            }
            
            print("📤 Requête envoyée à Zoho (POST avec form data):")
            print(f"   URL: {TOKEN_URL}")
            print(f"   grant_type: authorization_code")
            print(f"   client_id: {CLIENT_ID[:10]}...")
            print(f"   redirect_uri: {REDIRECT_URI}")
            print(f"   code: {authorization_code[:20]}...")
            print()
            
            try:
                response = await client.post(
                    TOKEN_URL,
                    data=request_data,
                )
                
                print(f"📥 Réponse de Zoho:")
                print(f"   Status: {response.status_code}")
                print()
                
                if response.status_code == 200:
                    response_data = response.json()
                    print(f"   Response JSON: {response_data}")
                    print()
                    return response_data
                else:
                    print(f"❌ Erreur HTTP {response.status_code}")
                    print(f"   Réponse: {response.text}")
                    print()
                    print("🔄 Tentative avec query params (comme dans la doc Zoho)...")
                    
                    # Essayer avec query params comme dans la documentation
                    from urllib.parse import urlencode
                    params = {
                        "code": authorization_code,
                        "grant_type": "authorization_code",
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "redirect_uri": REDIRECT_URI,
                    }
                    url_with_params = f"{TOKEN_URL}?{urlencode(params)}"
                    
                    response2 = await client.post(url_with_params)
                    
                    print(f"📥 Réponse (avec query params):")
                    print(f"   Status: {response2.status_code}")
                    print()
                    
                    if response2.status_code == 200:
                        response2_data = response2.json()
                        print(f"   Response JSON: {response2_data}")
                        print()
                        return response2_data
                    else:
                        print(f"❌ Erreur HTTP {response2.status_code}")
                        print(f"   Réponse: {response2.text}")
                        response2.raise_for_status()
                        return {}
            except httpx.HTTPStatusError as e:
                print(f"❌ Erreur HTTP: {e.response.status_code}")
                try:
                    error_text = e.response.text
                    print(f"   Réponse: {error_text}")
                except:
                    print(f"   Impossible de lire la réponse")
                raise
            except Exception as e:
                print(f"❌ Erreur inattendue: {e}")
                import traceback
                traceback.print_exc()
                raise
    
    import asyncio
    return asyncio.run(_exchange())


def extract_code_from_url(url: str) -> str | None:
    """Extrait le code d'autorisation depuis l'URL de redirection."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    if "code" in query_params:
        return query_params["code"][0]
    
    if "error" in query_params:
        error = query_params["error"][0]
        error_desc = query_params.get("error_description", [""])[0]
        print(f"❌ Erreur: {error}")
        if error_desc:
            print(f"   Description: {error_desc}")
        return None
    
    return None


def main():
    print("=" * 60)
    print("Obtention d'un Refresh Token Zoho Desk (Europe)")
    print("=" * 60)
    print()
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Erreur: CLIENT_ID et CLIENT_SECRET sont requis")
        sys.exit(1)
    
    # Gérer le redirect URI
    global REDIRECT_URI
    
    redirect_uri = REDIRECT_URI
    if not redirect_uri:
        print("📋 Configuration du Redirect URI")
        print()
        print("⚠️  IMPORTANT: Le Redirect URI doit correspondre EXACTEMENT")
        print("   (caractère par caractère) à celui configuré dans:")
        print("   https://api-console.zoho.eu/ > Votre Application > Client Details")
        print()
        print("Options communes:")
        print("  1. http://localhost:8080/callback")
        print("  2. http://localhost/callback")
        print("  3. https://yourdomain.com/callback")
        print()
        redirect_uri = input("Entrez le Redirect URI configuré dans Zoho: ").strip()
        
        if not redirect_uri:
            print("❌ Redirect URI requis!")
            sys.exit(1)
    
    # Mettre à jour la variable globale
    REDIRECT_URI = redirect_uri
    
    print()
    print(f"✅ Client ID: {CLIENT_ID[:10]}...")
    print(f"✅ Redirect URI: {REDIRECT_URI}")
    print()
    print("⚠️  Vérifiez que ce Redirect URI correspond EXACTEMENT à celui")
    print("   dans Zoho Developer Console (https://api-console.zoho.eu/)")
    print()
    
    # Étape 1: Générer l'URL d'autorisation
    auth_url = get_authorization_url()
    print("📋 ÉTAPE 1: Visitez cette URL dans votre navigateur:")
    print()
    print(auth_url)
    print()
    
    # Vérifier que access_type=offline est présent
    if "access_type=offline" not in auth_url:
        print("=" * 60)
        print("❌ ERREUR CRITIQUE: access_type=offline n'est pas dans l'URL!")
        print("=" * 60)
        print()
        print("⚠️  SANS access_type=offline, Zoho NE RETOURNERA PAS de refresh_token!")
        print()
        print("Selon la documentation Zoho:")
        print("'Refresh token can be obtained only when access_type is set")
        print("to offline while creating the access token.'")
        print()
        print("🔧 Solution: Le script devrait automatiquement ajouter")
        print("   access_type=offline. Si ce n'est pas le cas, il y a un bug.")
        print()
        sys.exit(1)
    
    print("✅ Vérifications importantes:")
    print(f"   - access_type=offline: {'✅ PRÉSENT' if 'access_type=offline' in auth_url else '❌ ABSENT'}")
    print(f"   - redirect_uri: {REDIRECT_URI}")
    print()
    print("📖 Selon la doc Zoho:")
    print("   'Refresh token can be obtained only when access_type is set")
    print("   to offline while creating the access token.'")
    print()
    print("🔐 Après autorisation, vous serez redirigé vers une URL qui ressemble à:")
    print(f"   {REDIRECT_URI}?code=1000.xxxxx.xxxxx")
    print()
    print("⚠️  IMPORTANT:")
    print("   1. Copiez le code IMMÉDIATEMENT (les codes expirent rapidement)")
    print("   2. Utilisez-le UNE SEULE FOIS (les codes sont à usage unique)")
    print("   3. Si vous avez déjà utilisé ce code, vous devez en générer un nouveau")
    print()
    
    # Étape 2: Demander le code ou l'URL complète
    print("📋 ÉTAPE 2: Après autorisation, vous avez deux options:")
    print("   Option A: Copiez l'URL complète de redirection")
    print("   Option B: Copiez uniquement le code (la partie après ?code=)")
    print()
    
    user_input = input("Collez l'URL complète ou le code: ").strip()
    
    # Extraire le code
    if user_input.startswith("http"):
        code = extract_code_from_url(user_input)
    else:
        code = user_input
    
    if not code:
        print("❌ Impossible d'extraire le code d'autorisation")
        sys.exit(1)
    
    print()
    print("🔄 Échange du code contre un refresh token...")
    print()
    
    try:
        # Étape 3: Échanger le code contre un token
        print(f"🔄 Utilisation du code: {code[:20]}...")
        print(f"🔄 Redirect URI utilisé: {REDIRECT_URI}")
        print()
        
        token_response = exchange_code_for_token(code)
        
        # Vérifier que nous avons bien reçu une réponse
        if not token_response:
            print("❌ Aucune réponse reçue de Zoho!")
            sys.exit(1)
        
        # Afficher la réponse complète pour debug
        print("=" * 60)
        print("📋 Réponse complète de Zoho (format JSON):")
        print("=" * 60)
        import json
        print(json.dumps(token_response, indent=2))
        print()
        
        # Vérifier les clés présentes
        print("🔍 Clés présentes dans la réponse:")
        for key in token_response.keys():
            value = token_response[key]
            if key == 'refresh_token':
                if value and value != "None" and (not isinstance(value, str) or value.strip().lower() != "none"):
                    print(f"   ✅ {key}: PRÉSENT = {str(value)[:50]}...")
                else:
                    print(f"   ❌ {key}: ABSENT ou None (valeur: {repr(value)})")
            elif key == 'access_token':
                print(f"   ✅ {key}: {'PRÉSENT' if value else 'ABSENT/VIDE'}")
            else:
                print(f"   ℹ️  {key}: {str(value)[:50]}...")
        print()
        
        refresh_token = token_response.get('refresh_token')
        
        # Vérifier si refresh_token est valide (pas None, pas vide, pas la chaîne "None")
        is_valid_token = (
            refresh_token is not None and
            refresh_token != "" and
            refresh_token != "None" and
            not (isinstance(refresh_token, str) and refresh_token.strip().lower() == "none")
        )
        
        if not is_valid_token:
            print("=" * 60)
            print("⚠️  ATTENTION: Aucun refresh_token dans la réponse!")
            print("=" * 60)
            print()
            print("Causes possibles:")
            print("1. Le code a déjà été utilisé (les codes OAuth sont à usage unique)")
            print("2. L'application n'a pas été configurée avec 'access_type=offline'")
            print("3. Le redirect_uri ne correspond pas exactement")
            print()
            print("Solution:")
            print("1. Régénérez un nouveau code d'autorisation")
            print("2. Assurez-vous que l'URL d'autorisation contient 'access_type=offline'")
            print("3. Vérifiez que le redirect_uri est identique dans:")
            print("   - L'URL d'autorisation")
            print("   - La requête d'échange de token")
            print("   - Zoho Developer Console")
            print()
            
            if token_response.get('access_token'):
                print("ℹ️  Vous avez reçu un access_token mais pas de refresh_token.")
                print("   Vous devrez refaire le processus pour obtenir un refresh_token.")
            
            sys.exit(1)
        
        print()
        print("=" * 60)
        print("✅ SUCCÈS! Voici vos tokens:")
        print("=" * 60)
        print()
        print("📝 Ajoutez ces lignes à votre fichier .env:")
        print()
        print(f"ZOHO_REFRESH_TOKEN={refresh_token}")
        if token_response.get('access_token'):
            print(f"# Access Token (optionnel, sera rafraîchi automatiquement):")
            print(f"# ZOHO_ACCESS_TOKEN={token_response.get('access_token')}")
        print()
        print("⚠️  IMPORTANT: Gardez votre refresh_token en sécurité!")
        print("   Il ne sera plus affiché après cette étape.")
        print()
        
        # Sauvegarder dans un fichier temporaire (optionnel)
        save = input("Voulez-vous sauvegarder dans un fichier .env.tmp? (o/n): ").strip().lower()
        if save == "o":
            with open(".env.tmp", "w") as f:
                f.write(f"ZOHO_REFRESH_TOKEN={refresh_token}\n")
            print("✅ Sauvegardé dans .env.tmp")
        
    except httpx.HTTPStatusError as e:
        print(f"❌ Erreur HTTP: {e.response.status_code}")
        print(f"   Réponse complète: {e.response.text}")
        print()
        print("Causes possibles:")
        print("- Le code a déjà été utilisé")
        print("- Le redirect_uri ne correspond pas")
        print("- Le client_id ou client_secret est incorrect")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

