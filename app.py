import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from gtts import gTTS

# --- FUNKCJE APLIKACJI ---

def pobierz_dane_produktu(url):
    """Pobiera i parsuje dane ze strony produktu."""
    try:
        st.info("Krok 1: Pobieram dane ze strony produktu...")
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Dostosowane selektory dla sklepu helios-szklo.pl
        nazwa_produktu_tag = soup.find('h1')
        opis_produktu_tag = soup.find('div', id='opis')
        
        nazwa_produktu = nazwa_produktu_tag.get_text(strip=True) if nazwa_produktu_tag else "Nie znaleziono nazwy produktu."
        opis_produktu = opis_produktu_tag.get_text(strip=True) if opis_produktu_tag else "Nie znaleziono opisu produktu."
        
        tekst_do_podsumowania = f"Nazwa produktu: {nazwa_produktu}. Opis: {opis_produktu}"
        st.success("✅ Dane produktu pobrane!")
        return tekst_do_podsumowania
    except Exception as e:
        st.error(f"Wystąpił błąd podczas pobierania danych: {e}")
        return None

def generuj_podsumowanie(prompt, api_key, model_name):
    """Wysyła tekst do wybranego modelu Gemini i zwraca podsumowanie."""
    try:
        st.info(f"Krok 2: Generuję podsumowanie (model: {model_name})...")
        genai.configure(api_key=api_key)
        # Używamy nazwy modelu przekazanej jako argument
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        st.success("✅ Propozycja tekstu wygenerowana!")
        return response.text
    except Exception