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
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        st.success("✅ Propozycja tekstu wygenerowana!")
        return response.text
    except Exception as e:
        st.error(f"Wystąpił błąd podczas komunikacji z API Gemini: {e}")
        return None

def generuj_audio(tekst, kod_jezyka='pl', nazwa_pliku="podsumowanie_audio.mp3"):
    """Konwertuje tekst na mowę i zapisuje jako plik MP3."""
    try:
        st.info("Krok 4: Tworzę plik audio...")
        tts = gTTS(text=tekst, lang=kod_jezyka)
        tts.save(nazwa_pliku)
        st.success(f"✅ Plik audio '{nazwa_pliku}' został pomyślnie zapisany!")
        return nazwa_pliku
    except Exception as e:
        st.error(f"Wystąpił błąd podczas tworzenia pliku audio: {e}")
        return None

# --- INTERFEJS GRAFICZNY APLIKACJI ---

st.set_page_config(page_title="Generator Audio", page_icon="🎙️")
st.title("🎙️ Generator Podsumowań Audio Produktów")
st.markdown("Wklej link do produktu, aby wygenerować propozycję tekstu do nagrania audio.")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.success("✅ Klucz API został pomyślnie wczytany.")
except (KeyError, FileNotFoundError):
    st.error("⚠️ Nie znaleziono klucza API. Jeśli uruchamiasz online, upewnij się, że dodałeś go do sekretów w Streamlit Cloud.")
    api_key = None

if 'summary_text' not in st.session_state:
    st.session_state.summary_text = ""

st.markdown("---")
st.subheader("Krok 1: Wygeneruj propozycję tekstu")
url = st.text_input("Wklej tutaj URL do strony produktu")
col1, col2 = st.columns(2)
with col1:
    jezyk_opcja = st.selectbox("Wybierz język podsumowania:", ("Polski", "Angielski", "Niemiecki"))
with col2:
    model_wybor = st.selectbox("Wybierz model AI:", ("Szybki (Flash 1.5)", "Zaawansowany (Pro 1.5)"))

mapowanie_modeli = {"Szybki (Flash 1.5)": "gemini-1.5-flash", "Zaawansowany (Pro 1.5)": "gemini-1.5-pro"}
wybrany_model = mapowanie_modeli[model_wybor]

# ZAKTUALIZOWANE POLECENIA Z ZAKOŃCZENIEM
mapowanie_jezykow = {
    "Polski": {
        "kod": "pl", 
        "polecenie": "Stwórz krótkie, chwytliwe podsumowanie produktu (3-4 zdania) w języku POLSKIM. WAŻNE: W wygenerowanym tekście wszystkie liczby i cyfry muszą być zapisane słownie (np. 'dwadzieścia mililitrów' zamiast '20 ml'). Zawsze zakończ tekst dokładnie tymi słowami: 'Kupisz go na helios-szklo.pl'."
    },
    "Angielski": {
        "kod": "en", 
        "polecenie": "Na podstawie poniższych danych w języku polskim, stwórz krótkie, chwytliwe podsumowanie produktu (3-4 zdania) w języku ANGIELSKIM. WAŻNE: W wygenerowanym tekście wszystkie liczby i cyfry muszą być zapisane słownie (np. 'twenty milliliters' zamiast '20 ml'). Zawsze zakończ tekst dokładnie tymi słowami: 'You can buy it at helios-szklo.pl'."
    },
    "Niemiecki": {
        "kod": "de", 
        "polecenie": "Na podstawie poniższych danych w języku polskim, stwórz krótkie, chwytliwe podsumowanie produktu (3-4 zdania) w języku NIEMIECKIM. WAŻNE: W wygenerowanym tekście wszystkie liczby i cyfry muszą być zapisane słownie (np. 'zwanzig Milliliter' statt '20 ml'). Zawsze zakończ tekst dokładnie tymi słowami: 'Sie können es auf helios-szklo.pl kaufen'."
    }
}
wybrany_jezyk_info = mapowanie_jezykow[jezyk_opcja]

if st.button("✍️ Generuj tekst"):
    if not api_key: st.warning("Klucz API nie został wczytany. Sprawdź konfigurację sekretów.")
    elif not url.startswith('http'): st.warning("Proszę wpisać poprawny adres URL.")
    else:
        with st.spinner(f"Generuję propozycję tekstu przy użyciu modelu {model_wybor}..."):
            tekst_produktu = pobierz_dane_produktu(url)
            if tekst_produktu:
                prompt_dla_ai = f"Polecenie: {wybrany_jezyk_info['polecenie']}. Dane wejściowe: '{tekst_produktu}'"
                podsumowanie = generuj_podsumowanie(prompt_dla_ai, api_key, wybrany_model)
                st.session_state.summary_text = podsumowanie

if st.session_state.summary_text:
    st.markdown("---")
    st.subheader("Krok 2: Zaakceptuj lub edytuj tekst")
    edited_text = st.text_area("Możesz teraz edytować tekst przed wygenerowaniem audio:", value=st.session_state.summary_text, height=150)
    if st.button("🎙️ Generuj plik audio z tego tekstu"):
        with st.spinner("Tworzę plik audio..."):
            if not edited_text.strip(): st.warning("Pole tekstowe jest puste. Nie można wygenerować audio.")
            else:
                plik_audio = generuj_audio(edited_text, kod_jezyka=wybrany_jezyk_info['kod'])
                if plik_audio:
                    st.subheader("Odsłuchaj i pobierz:")
                    with open(plik_audio, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format='audio/mpeg')
                    with open(plik_audio, "rb") as file_to_download:
                        st.download_button("Pobierz plik MP3", data=file_to_download, file_name="podsumowanie_audio.mp3", mime='audio/mpeg')