import os
import requests
from flask import current_app

class AIService:
    """AI model servisleri için ana sınıf"""
    
    def __init__(self, model='openai'):
        self.model = model
    
    def generate_report(self, prompt, title='Rapor'):
        """AI ile rapor oluştur"""
        if self.model == 'openai':
            return self._generate_with_openai(prompt, title)
        elif self.model == 'anthropic':
            return self._generate_with_anthropic(prompt, title)
        elif self.model == 'google':
            return self._generate_with_google(prompt, title)
        else:
            raise ValueError(f'Desteklenmeyen AI modeli: {self.model}')
    
    def _generate_with_openai(self, prompt, title):
        """OpenAI ile rapor oluştur"""
        try:
            import openai
            
            api_key = current_app.config.get('OPENAI_API_KEY')
            if not api_key:
                return None, 'OpenAI API anahtarı yapılandırılmamış.'
            
            openai.api_key = api_key
            
            system_prompt = """Sen profesyonel bir rapor yazarısın. Kullanıcının verdiği konuya göre detaylı, 
            akademik ve profesyonel bir rapor oluştur. Rapor aşağıdaki yapıda olmalı:
            
            # Başlık
            ## Giriş
            ## Ana Bölümler
            ## Sonuç
            ## Kaynaklar
            
            Markdown formatında yaz. Tablolar, listeler ve başlıkları uygun şekilde kullan."""
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Başlık: {title}\n\n{prompt}"}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            return content, None
            
        except Exception as e:
            return None, f'OpenAI hatası: {str(e)}'
    
    def _generate_with_anthropic(self, prompt, title):
        """Anthropic Claude ile rapor oluştur"""
        try:
            import anthropic
            
            api_key = current_app.config.get('ANTHROPIC_API_KEY')
            if not api_key:
                return None, 'Anthropic API anahtarı yapılandırılmamış.'
            
            client = anthropic.Anthropic(api_key=api_key)
            
            system_prompt = """Sen profesyonel bir rapor yazarısın. Kullanıcının verdiği konuya göre detaylı, 
            akademik ve profesyonel bir rapor oluştur. Markdown formatında yaz."""
            
            message = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Başlık: {title}\n\n{prompt}"}
                ]
            )
            
            content = message.content[0].text
            return content, None
            
        except Exception as e:
            return None, f'Anthropic hatası: {str(e)}'
    
    def _generate_with_google(self, prompt, title):
        """Google Gemini ile rapor oluştur"""
        try:
            import google.generativeai as genai
            
            api_key = current_app.config.get('GOOGLE_API_KEY')
            if not api_key:
                return None, 'Google API anahtarı yapılandırılmamış.'
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            system_prompt = """Sen profesyonel bir rapor yazarısın. Kullanıcının verdiği konuya göre detaylı, 
            akademik ve profesyonel bir rapor oluştur. Markdown formatında yaz."""
            
            full_prompt = f"{system_prompt}\n\nBaşlık: {title}\n\n{prompt}"
            response = model.generate_content(full_prompt)
            
            return response.text, None
            
        except Exception as e:
            return None, f'Google hatası: {str(e)}'
