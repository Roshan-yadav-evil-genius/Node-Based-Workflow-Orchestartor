from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional
from enum import Enum


class FieldType(str, Enum):
    """
    Enumeration of valid field types.
    Inherits from str to allow direct string comparison and serialization.
    """
    TEXT = "text"
    EMAIL = "email"
    NUMBER = "number"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DATE = "date"
    FILE = "file"
    DERIVED = "derived"


@dataclass
class Field:
    """
    Pure data model for a form field.
    Its ONLY responsibility: hold data.
    """
    type: FieldType
    name: str
    label: str
    required: bool = False
    placeholder: str = ""
    dependsOn: Optional[List['Field']] = None
    options: Optional[List[Dict[str, str]]] = None
    defaultValue: Optional[Any] = None

    def depends_on(self, field: 'Field') -> None:
        """
        Add a field dependency.
        Prevents circular dependencies (direct and transitive) and duplicates.
        
        Args:
            field: The Field object this field depends on
            
        Raises:
            ValueError: If circular dependency detected, self-dependency, or field already in dependsOn
        """
        # Validate input
        if field is None:
            raise ValueError("Cannot add None as a dependency")
        
        # Prevent self-dependency
        if field is self:
            raise ValueError(f"Field '{self.name}' cannot depend on itself")
        
        # Initialize dependsOn if None
        if self.dependsOn is None:
            self.dependsOn = []

        # Check if field already in dependsOn list
        if field in self.dependsOn:
            raise ValueError(f"Field '{field.name}' already in dependsOn list for '{self.name}'")

        # Check for direct circular dependency: if field depends on self, it's circular
        if field.dependsOn and self in field.dependsOn:
            raise ValueError(
                f"Circular dependency detected: '{self.name}' depends on '{field.name}', "
                f"but '{field.name}' already depends on '{self.name}'"
            )
        
        # Check for transitive circular dependency: if adding this dependency would create a cycle
        # (e.g., A->B->C->A where we're trying to add A->B)
        if self._would_create_cycle(field):
            raise ValueError(
                f"Circular dependency detected: Adding '{field.name}' to '{self.name}' would create a cycle"
            )

        # Add field to dependencies
        self.dependsOn.append(field)
    
    def _would_create_cycle(self, target_field: 'Field', visited: Optional[set] = None) -> bool:
        """
        Check if adding target_field as a dependency would create a circular dependency.
        Uses DFS to detect cycles by checking if any path from target_field leads back to self.
        
        Args:
            target_field: The field we want to add as a dependency
            visited: Set of visited Field objects (for cycle detection)
            
        Returns:
            True if adding this dependency would create a cycle
        """
        if visited is None:
            visited = set()
        
        # If target_field is self, it's a cycle (shouldn't happen due to self-dependency check, but safe)
        if target_field is self:
            return True
        
        # If we've already visited this field object in this path, we found a cycle
        if target_field in visited:
            return True
        
        # Mark current field as visited (using object identity)
        visited.add(target_field)
        
        # Recursively check all dependencies of target_field
        # If any dependency chain leads back to self, it's a cycle
        if target_field.dependsOn:
            for dep in target_field.dependsOn:
                if self._would_create_cycle(dep, visited):
                    return True
        
        return False