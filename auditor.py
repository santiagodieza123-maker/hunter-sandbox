from typing import Dict, Any, Optional
import os
import re
from groq import Groq, RateLimitError, APIStatusError, APIConnectionError

SYSTEM_PROMPT = """Eres el Auditor de Seguridad y Calidad de Código (Red Team) para el sistema Bounty Hunter 24/7.
Tu misión es auditar estrictamente la propuesta de parche de código.
Analiza con rigor:
1. Casos borde (edge cases) y condiciones de carrera (race conditions).
2. Fugas de memoria o manejo deficiente de recursos.
3. Problemas de tipado, contratos de datos y consistencia lógica.

Formato de respuesta obligatorio:
- Primero realiza tu análisis crítico detallado (Chain of Thought).
- Concluye tu respuesta estrictamente en la última línea con el veredicto en este formato exacto:
VERDICT: APPROVED
o
VERDICT: REJECTED | Motivo: <razón concisa del rechazo>"""

class CodeAuditor:
    def __init__(self, api_key: Optional[str] = None, model: str = "openai/gpt-oss-120b") -> None:
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY no encontrada en el entorno ni suministrada explícitamente.")
        self.client = Groq(api_key=self.api_key)
        self.model = model

    def audit(self, context: str, patch_code: str) -> Dict[str, Any]:
        prompt = f"### CONTEXTO DE LA INCIDENCIA:\n{context}\n\n### PROPUESTA DE PARCHE:\n{patch_code}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            raw_content = response.choices[0].message.content or ""
            return self._parse_verdict(raw_content)
        except RateLimitError as e:
            return {
                "verdict": "ERROR",
                "reason": f"Rate limit excedido (429): {str(e)}",
                "raw_response": ""
            }
        except APIStatusError as e:
            return {
                "verdict": "ERROR",
                "reason": f"Fallo en API Groq (Status {e.status_code}): {str(e)}",
                "raw_response": ""
            }
        except APIConnectionError as e:
            return {
                "verdict": "ERROR",
                "reason": f"Fallo de conexión con Groq: {str(e)}",
                "raw_response": ""
            }
        except Exception as e:
            return {
                "verdict": "ERROR",
                "reason": f"Error inesperado en nodo auditor: {str(e)}",
                "raw_response": ""
            }

    def _parse_verdict(self, raw_content: str) -> Dict[str, Any]:
        clean = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL).strip()
        pattern = r"\*{0,2}VERDICT:?\*{0,2}\s*:?\s*(APPROVED|REJECTED)(?:\s*\|\s*(?:Motivo:)?\s*(.*))?"
        matches = list(re.finditer(pattern, clean, re.IGNORECASE))
        if matches:
            last = matches[-1]
            return {
                "verdict": last.group(1).upper(),
                "reason": last.group(2).strip() if last.group(2) else "Aprobado sin observaciones.",
                "raw_response": raw_content
            }

        return {
            "verdict": "REJECTED",
            "reason": "El modelo no emitio un formato de veredicto determinista valido.",
            "raw_response": raw_content
        }
