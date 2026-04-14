"""AI Advisor — Requirements 3.6, 3.7, 4.6, 5.6, 7.5, 9.3, 9.4."""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_OPENAI_AVAILABLE = False
try:
    import openai
    _OPENAI_AVAILABLE = True
except ImportError:
    pass


class AIAdvisor:
    """OpenAI-powered advisor with graceful degradation when API is unavailable."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.model = model
        self._client = None
        key = api_key or os.getenv("OPENAI_API_KEY", "")
        if _OPENAI_AVAILABLE and key and not key.startswith("sk-your"):
            try:
                self._client = openai.OpenAI(api_key=key)
            except Exception as exc:
                logger.warning("OpenAI client init failed: %s", exc)

    # ── Public methods ────────────────────────────────────────────────────────

    def infer_column_semantics(self, profile: dict) -> dict[str, dict]:
        """Return semantic type + confidence per column. Requirement 3.6, 3.7."""
        columns = profile.get("columns", [])
        result: dict[str, dict] = {}

        if self._client:
            try:
                col_summary = "\n".join(
                    f"- {c['name']}: dtype={c['dtype']}, sample_values={[v['value'] for v in c.get('top_values', [])[:3]]}"
                    for c in columns
                )
                prompt = (
                    "You are a data analyst. For each column below, infer the semantic type "
                    "(e.g. email, phone, age, price, date, country, id, name, etc.) and a confidence 0-1.\n"
                    f"Columns:\n{col_summary}\n\n"
                    "Respond as JSON: {\"column_name\": {\"semantic_type\": \"...\", \"confidence\": 0.9}, ...}"
                )
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    max_tokens=500,
                )
                import json
                result = json.loads(response.choices[0].message.content)
                return result
            except Exception as exc:
                logger.warning("OpenAI infer_column_semantics failed: %s", exc)

        # Fallback: rule-based inference
        for col in columns:
            name = col["name"].lower()
            dtype = col.get("dtype", "string")
            if any(k in name for k in ("email", "mail")):
                result[col["name"]] = {"semantic_type": "email", "confidence": 0.9}
            elif any(k in name for k in ("phone", "mobile", "tel")):
                result[col["name"]] = {"semantic_type": "phone", "confidence": 0.85}
            elif any(k in name for k in ("age",)):
                result[col["name"]] = {"semantic_type": "age", "confidence": 0.8}
            elif any(k in name for k in ("price", "cost", "amount", "revenue")):
                result[col["name"]] = {"semantic_type": "price", "confidence": 0.8}
            elif any(k in name for k in ("date", "time", "created", "updated")):
                result[col["name"]] = {"semantic_type": "datetime", "confidence": 0.85}
            elif any(k in name for k in ("country", "nation")):
                result[col["name"]] = {"semantic_type": "country", "confidence": 0.8}
            elif any(k in name for k in ("id", "_id", "uuid")):
                result[col["name"]] = {"semantic_type": "identifier", "confidence": 0.75}
            elif dtype in ("integer", "float"):
                result[col["name"]] = {"semantic_type": "numeric", "confidence": 0.7}
            else:
                result[col["name"]] = {"semantic_type": "text", "confidence": 0.5}
        return result

    def generate_narrative(self, issues: list[str], fixes: list[str]) -> str:
        """Generate plain-English report narrative. Requirement 9.3, 9.4."""
        if self._client and (issues or fixes):
            try:
                prompt = (
                    "You are a data quality analyst. Write a concise 2-3 paragraph narrative "
                    "summarizing the following data quality issues and fixes applied.\n\n"
                    f"Issues found:\n" + "\n".join(f"- {i}" for i in issues) + "\n\n"
                    f"Fixes applied:\n" + "\n".join(f"- {f}" for f in fixes)
                )
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                )
                return response.choices[0].message.content.strip()
            except Exception as exc:
                logger.warning("OpenAI generate_narrative failed: %s", exc)

        # Fallback narrative
        n_issues = len(issues)
        n_fixes = len(fixes)
        return (
            f"Data quality analysis identified {n_issues} issue(s) in the dataset. "
            f"{n_fixes} automated fix(es) were applied to improve data quality. "
            "Please review the detailed findings below for column-level statistics and recommendations."
        )

    def suggest_transformations(self, profile: dict) -> list[dict]:
        """Suggest transformations based on profile. Requirement 7.5."""
        suggestions: list[dict] = []
        for col in profile.get("columns", []):
            dtype = col.get("dtype", "string")
            missing_pct = col.get("missing_pct", 0)
            name = col["name"]

            if missing_pct > 5:
                suggestions.append({"column": name, "action": "impute", "reason": f"{missing_pct:.1f}% missing values"})
            if dtype in ("integer", "float") and col.get("std") and col.get("mean"):
                if col["std"] > col["mean"] * 2:
                    suggestions.append({"column": name, "action": "scale_robust", "reason": "High variance detected"})
            if dtype == "string" and col.get("cardinality", 0) < 20:
                suggestions.append({"column": name, "action": "encode_onehot", "reason": "Low-cardinality categorical"})
        return suggestions

    def explain_anomalies(self, anomaly_report: dict) -> str:
        """Plain-English anomaly explanation. Requirement 5.6."""
        count = anomaly_report.get("anomaly_count", 0)
        pct = anomaly_report.get("anomaly_pct", 0)
        threshold = anomaly_report.get("threshold", 0)

        if self._client and count > 0:
            try:
                prompt = (
                    f"A dataset had {count} anomalous records ({pct:.1f}% of total) detected by an autoencoder "
                    f"with reconstruction error threshold {threshold:.4f}. "
                    "In 2-3 sentences, explain what this means and what action to take."
                )
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                )
                return response.choices[0].message.content.strip()
            except Exception as exc:
                logger.warning("OpenAI explain_anomalies failed: %s", exc)

        if count == 0:
            return "No anomalies were detected. The dataset appears consistent with the expected distribution."
        return (
            f"{count} anomalous records ({pct:.1f}%) were detected with reconstruction errors "
            f"above the {threshold:.4f} threshold. These records deviate significantly from the "
            "learned data distribution and should be reviewed manually."
        )
