import json
import os
from typing import Dict, Any, List
from backend.core.logging import get_logger

logger = get_logger("PolicyRetriever")


class PolicyRetriever:
    """
    Retrieves and indexes configured corporate compliance policies.
    Strictly avoids hardcoded or hallucinated regulatory claims.
    """

    DEFAULT_POLICY_PATH = os.path.join(os.path.dirname(__file__), "../../../policies/corporate_compliance_policy.json")

    @classmethod
    def load_policy(cls, policy_path: str = None) -> Dict[str, Any]:
        path = policy_path or cls.DEFAULT_POLICY_PATH
        path = os.path.abspath(path)
        if not os.path.exists(path):
            logger.warning(f"Policy file not found at {path}. Returning default baseline policy.")
            return {
                "policy_id": "DEFAULT-FALLBACK",
                "policy_name": "Standard Enterprise Policy",
                "rules": []
            }

        with open(path, "r", encoding="utf-8") as f:
            policy_data = json.load(f)

        logger.info(f"Loaded policy '{policy_data.get('policy_name')}' with {len(policy_data.get('rules', []))} rules.")
        return policy_data
