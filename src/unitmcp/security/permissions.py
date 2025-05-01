"""
permissions.py
"""

"""Permission management for MCP hardware access."""

import re
from typing import Dict, Set
from dataclasses import dataclass, field


@dataclass
class PermissionRule:
    """Permission rule definition."""

    client_pattern: str
    resource: str
    allowed: bool = True

    def matches_client(self, client_id: str) -> bool:
        """Check if client ID matches pattern."""
        # Convert wildcard pattern to regex
        pattern = self.client_pattern.replace("*", ".*")
        return bool(re.match(f"^{pattern}$", client_id))


class PermissionManager:
    """Manages permissions for hardware access."""

    def __init__(self):
        self.rules: list[PermissionRule] = []
        self._cache: Dict[tuple[str, str], bool] = {}

    def grant_permission(self, client_pattern: str, resource: str):
        """Grant permission to client pattern for resource."""
        rule = PermissionRule(client_pattern, resource, True)
        self.rules.insert(0, rule)  # Newer rules take precedence
        self._cache.clear()

    def revoke_permission(self, client_pattern: str, resource: str):
        """Revoke permission from client pattern for resource."""
        rule = PermissionRule(client_pattern, resource, False)
        self.rules.insert(0, rule)  # Newer rules take precedence
        self._cache.clear()

    def check_permission(self, client_id: str, resource: str) -> bool:
        """Check if client has permission for resource."""
        # Check cache first
        cache_key = (client_id, resource)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Check rules in order (newer rules first)
        for rule in self.rules:
            if rule.resource == resource and rule.matches_client(client_id):
                self._cache[cache_key] = rule.allowed
                return rule.allowed

        # Default deny if no matching rule
        self._cache[cache_key] = False
        return False

    def get_client_permissions(self, client_id: str) -> Set[str]:
        """Get all permissions for a client."""
        permissions = set()

        for rule in self.rules:
            if rule.allowed and rule.matches_client(client_id):
                permissions.add(rule.resource)

        return permissions

    def clear_permissions(self):
        """Clear all permission rules."""
        self.rules.clear()
        self._cache.clear()

    def load_from_config(self, config: Dict):
        """Load permissions from configuration dictionary."""
        for rule_config in config.get("permission_rules", []):
            client_pattern = rule_config.get("client_pattern")
            resource = rule_config.get("resource")
            allowed = rule_config.get("allowed", True)

            if client_pattern and resource:
                if allowed:
                    self.grant_permission(client_pattern, resource)
                else:
                    self.revoke_permission(client_pattern, resource)

    def to_config(self) -> Dict:
        """Export permissions to configuration dictionary."""
        return {
            "permission_rules": [
                {
                    "client_pattern": rule.client_pattern,
                    "resource": rule.resource,
                    "allowed": rule.allowed,
                }
                for rule in self.rules
            ]
        }
