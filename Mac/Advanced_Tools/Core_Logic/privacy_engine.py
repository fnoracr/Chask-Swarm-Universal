import os
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

class PrivacyEngine:
    """
    Motor de desidentificación Global (195 Países).
    Utiliza Microsoft Presidio con un Reconocedor Universal de Identidad.
    """
    
    def __init__(self, country_code="ES"):
        self.country_code = country_code.upper()
        
        # 1. Configurar Motor NLP de Microsoft Presidio (Modelos pesados)
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "es", "model_name": "es_core_news_md"},
                {"lang_code": "en", "model_name": "en_core_web_lg"}
            ],
        }
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        self.anonymizer = AnonymizerEngine()
        
        # Idioma base para el análisis
        self.lang = "es" if self.country_code in ["ES", "MX", "AR", "CL", "CO", "PE", "VE", "UY", "EC"] else "en"
        
        # 2. Inyectar el Reconocedor Universal (Cobertura 195 Países)
        self._add_universal_identity_recognizer()

    def _add_universal_identity_recognizer(self):
        """
        Crea un reconocedor que detecta documentos de identidad de cualquier país
        basándose en palabras clave internacionales y patrones alfanuméricos.
        """
        # Palabras clave en múltiples idiomas (Español, Inglés, Francés, Alemán, Portugués, etc.)
        id_keywords = [
            "DNI", "NIE", "RUT", "RUN", "CURP", "RFC", "CPF", "CNPJ", "CUIL", "CUIT", 
            "Cédula", "Cedula", "Identificación", "Identificacion", "Pasaporte", "Passport", 
            "ID Card", "Identity Card", "National ID", "Social Security", "SSN", "NIF", "CIF",
            "Documento", "Nº Documento", "ID Number", "Matrícula", "Registro", "Tax ID"
        ]
        
        # Patrón alfanumérico genérico que suele seguir cualquier documento (letras y números de 6 a 20 caracteres)
        # Se apoya en las palabras clave para evitar falsos positivos.
        id_pattern = Pattern(
            name="universal_id_pattern",
            regex=r"\b[A-Z0-9]{6,20}\b",
            score=0.4 # Puntuación base baja
        )
        
        universal_recognizer = PatternRecognizer(
            supported_entity="GLOBAL_ID",
            patterns=[id_pattern],
            context=id_keywords # Si estas palabras están cerca, la puntuación sube drásticamente
        )
        
        self.analyzer.registry.add_recognizer(universal_recognizer)

    def analyze(self, text):
        """Analiza el texto con la IA de Microsoft y el Reconocedor Universal."""
        return self.analyzer.analyze(text=text, language=self.lang)

    def anonymize(self, text):
        """Limpia el texto usando el estándar de Microsoft Presidio."""
        results = self.analyze(text)
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results
        )
        return anonymized_result.text

if __name__ == "__main__":
    # Prueba del Reconocedor Universal
    engine = PrivacyEngine(country_code="ES")
    # Ejemplo con un ID de un país no configurado previamente (ej: Portugal NIF)
    test_text = "El NIF de la persona es 123456789 y su Pasaporte es ABC123456."
    print("--- UNIVERSAL PRIVACY SHIELD TEST ---")
    print("Entrada:", test_text)
    print("Salida:", engine.anonymize(test_text))
