from django.utils import translation
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class AutoLanguageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Only switch language if it hasn't been set in the session
        if not request.session.get('language_set') and 'HTTP_ACCEPT_LANGUAGE' in request.META:
            browser_language = request.META['HTTP_ACCEPT_LANGUAGE'].split(',')[0]
            
            # Handle both language codes with and without region (e.g., 'en-US' or 'en')
            language_code = browser_language.split('-')[0]
            
            # Check if the exact browser language is supported
            supported_languages = [lang[0] for lang in settings.LANGUAGES]
            
            if browser_language in supported_languages:
                language_to_use = browser_language
            elif language_code in supported_languages:
                language_to_use = language_code
            else:
                language_to_use = settings.LANGUAGE_CODE
            
            translation.activate(language_to_use)
            request.LANGUAGE_CODE = language_to_use
            request.session['django_language'] = language_to_use
            request.session['language_set'] = True